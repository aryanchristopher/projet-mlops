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
