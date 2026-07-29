provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "Lira"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}