resource "aws_db_subnet_group" "this" {
  name = "${var.environment}-lira-db-subnet-group"

  subnet_ids = var.private_subnet_ids

  tags = {
    Name        = "${var.environment}-lira-db-subnet-group"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_db_parameter_group" "postgres" {
  name   = "${var.environment}-lira-postgres-params"
  family = "postgres18"

  description = "PostgreSQL parameter group"

  tags = {
    Name        = "${var.environment}-lira-postgres-params"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_db_instance" "postgres" {

  identifier = "${var.environment}-lira-postgres"

  engine         = "postgres"
  engine_version = "18.5"

  instance_class = "db.t4g.micro"

  allocated_storage = 20
  storage_type       = "gp3"

  db_name  = "lira"
  username = var.db_username
  password = var.db_password

  db_subnet_group_name = aws_db_subnet_group.this.name

  vpc_security_group_ids = [
    var.postgres_security_group_id
  ]

  parameter_group_name = aws_db_parameter_group.postgres.name

  publicly_accessible = false

  multi_az = false

  skip_final_snapshot = true

  deletion_protection = false

  storage_encrypted = true

  backup_retention_period = 7

  tags = {
    Name        = "${var.environment}-lira-postgres"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}