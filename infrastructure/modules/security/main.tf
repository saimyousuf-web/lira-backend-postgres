resource "aws_security_group" "lambda" {
  name        = "${var.environment}-lambda-sg"
  description = "Security group for Lambda functions"
  vpc_id      = var.vpc_id

  tags = {
    Name        = "${var.environment}-lambda-sg"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_vpc_security_group_egress_rule" "lambda_all_outbound" {
  security_group_id = aws_security_group.lambda.id

  ip_protocol = "-1"
  cidr_ipv4   = "0.0.0.0/0"

  description = "Allow Lambda outbound traffic"
}

resource "aws_security_group" "postgres" {
  name        = "${var.environment}-postgres-sg"
  description = "Security group for PostgreSQL database"
  vpc_id      = var.vpc_id

  tags = {
    Name        = "${var.environment}-postgres-sg"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_vpc_security_group_ingress_rule" "postgres_from_lambda" {
 
  security_group_id = aws_security_group.postgres.id

  referenced_security_group_id = aws_security_group.lambda.id

  ip_protocol = "tcp"
  from_port   = var.postgres_port
  to_port     = var.postgres_port

  description = "Allow PostgreSQL access from Lambda"
}