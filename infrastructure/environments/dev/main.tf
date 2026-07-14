module "networking" {
  source = "../../modules/networking"

  environment = var.environment
  aws_region  = var.aws_region
  vpc_cidr    = var.vpc_cidr

  public_subnet_a_cidr = var.public_subnet_a_cidr
  public_subnet_a_az   = var.public_subnet_a_az

  public_subnet_b_cidr = var.public_subnet_b_cidr
  public_subnet_b_az   = var.public_subnet_b_az

  private_subnet_a_cidr = var.private_subnet_a_cidr
  private_subnet_a_az   = var.private_subnet_a_az

  private_subnet_b_cidr = var.private_subnet_b_cidr
  private_subnet_b_az   = var.private_subnet_b_az
}


module "security" {
  source = "../../modules/security"
                                  
  environment = var.environment
  vpc_id      = module.networking.vpc_id
}    


module "secrets" {
  source = "../../modules/secrets"

  environment = var.environment
  db_username = "postgres"
}

module "rds" {
  source = "../../modules/rds"

  environment = var.environment

  private_subnet_ids = [
    module.networking.private_subnet_a_id,
    module.networking.private_subnet_b_id
  ]

  postgres_security_group_id = module.security.postgres_security_group_id

  db_username = module.secrets.db_username
  db_password = module.secrets.db_password
}