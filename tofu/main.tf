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
