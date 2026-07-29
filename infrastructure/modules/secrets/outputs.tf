output "secret_arn" {
  value = aws_secretsmanager_secret.postgres.arn
}

output "secret_name" {
  value = aws_secretsmanager_secret.postgres.name
}

output "db_username" {
  value = var.db_username
}

output "db_password" {
  value     = random_password.db_password.result
  sensitive = true
}