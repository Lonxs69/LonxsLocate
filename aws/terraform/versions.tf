terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }

  # Estado remoto: terraform init -backend-config="bucket=<bucket-de-estado>"
  backend "s3" {
    key     = "lonxslocate/terraform.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Proyecto  = "LonxsLocate"
      Entorno   = var.entorno
      ManagedBy = "terraform"
    }
  }
}
