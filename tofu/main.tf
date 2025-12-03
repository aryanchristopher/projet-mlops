terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# On configure la région Paris (eu-west-3) comme demandé dans le sujet
provider "aws" {
  region = "eu-west-3"
}

# 1. On génère une nouvelle clé SSH sécurisée automatiquement
resource "tls_private_key" "ssh_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# 2. On envoie la partie "publique" de la clé à AWS
resource "aws_key_pair" "deployer" {
  key_name   = "mlops-key"
  public_key = tls_private_key.ssh_key.public_key_openssh
}

# 3. On sauvegarde la partie "privée" sur ton PC pour qu'Ansible l'utilise
resource "local_file" "private_key" {
  content         = tls_private_key.ssh_key.private_key_pem
  filename        = "${path.module}/../ansible/id_rsa.pem"
  file_permission = "0600" # Très important : lecture seule pour toi (sécurité Linux)
}

# Sécurité pour l'API (SSH + HTTP + Exporter metrics)
resource "aws_security_group" "api_sg" {
  name        = "mlops-api-sg"
  description = "Security group for API server"

  # SSH (Port 22)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # API (Port 5000 - Flask/FastAPI)
  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Node Exporter pour Prometheus (Port 9100)
  ingress {
    from_port   = 9100
    to_port     = 9100
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Sortie illimitée (pour télécharger des paquets, docker, etc)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Sécurité pour le Monitoring (SSH + Prometheus + Grafana)
resource "aws_security_group" "monitoring_sg" {
  name        = "mlops-monitoring-sg"
  description = "Security group for Monitoring server"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Prometheus UI (Port 9090)
  ingress {
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Grafana UI (Port 3000)
  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# --- 1. Trouver automatiquement la dernière version d'Ubuntu ---
# (C'est une bonne pratique du cours : ne pas mettre l'ID en dur)
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # ID officiel de Canonical (Ubuntu)

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

# --- 2. Créer l'Instance API ---
resource "aws_instance" "api_server" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro" # Instance gratuite (Free Tier)
  key_name      = aws_key_pair.deployer.key_name
  
  # On attache le Security Group API créé juste avant
  vpc_security_group_ids = [aws_security_group.api_sg.id]

  tags = {
    Name = "mlops-api-server"
  }
}

# --- 3. Créer l'Instance Monitoring ---
resource "aws_instance" "monitoring_server" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"
  key_name      = aws_key_pair.deployer.key_name

  # On attache le Security Group Monitoring
  vpc_security_group_ids = [aws_security_group.monitoring_sg.id]

  tags = {
    Name = "mlops-monitoring-server"
  }
}

# --- 4. Générer l'inventaire Ansible automatiquement ---
# (Ceci remplit l'exigence "Génération automatique de l'inventaire")
resource "local_file" "ansible_inventory" {
  content = <<EOT
api:
  hosts:
    ${aws_instance.api_server.public_ip}:
      ansible_user: ubuntu
      ansible_ssh_private_key_file: ./id_rsa.pem

monitoring:
  hosts:
    ${aws_instance.monitoring_server.public_ip}:
      ansible_user: ubuntu
      ansible_ssh_private_key_file: ./id_rsa.pem
EOT
  filename = "${path.module}/../ansible/inventory.yml"
}
