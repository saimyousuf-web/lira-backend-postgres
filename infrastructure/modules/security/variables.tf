variable "environment" {
  description = "Deployment environment (dev, qa, prod)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where security groups will be created"
  type        = string
}

variable "postgres_port" {
  description = "Port used by PostgreSQL"
  type        = number
  default     = 5432
}