output "lambda_security_group_id" {
  description = "ID of the Lambda Security Group"
  value       = aws_security_group.lambda.id
}

output "postgres_security_group_id" {
  description = "ID of the PostgreSQL Security Group"
  value       = aws_security_group.postgres.id
}