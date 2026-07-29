resource "random_password" "db_password" {
  length           = 20
  special          = true
  override_special = "_%@"
}


resource "aws_secretsmanager_secret" "postgres" {
  name = "${var.environment}-lira-postgres-secret"

  tags = {
    Name = "${var.environment}-lira-postgres-secret"
  }
}

resource "aws_secretsmanager_secret_version" "postgres" {

  secret_id = aws_secretsmanager_secret.postgres.id

  secret_string = jsonencode({
    username = var.db_username
    password = random_password.db_password.result
  })
}