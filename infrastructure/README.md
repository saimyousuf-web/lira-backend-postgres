sam deploy --parameter-overrides liraEnv=dev LambdaSecurityGroupId=<terraform-output> PrivateSubnetA=<terraform-output> PrivateSubnetB=<terraform-output> DbSecretArn=<terraform-output>


# Lira Infrastructure

Terraform Infrastructure for the **Lira Backend** platform.

This repository provisions the AWS infrastructure required by the Lira Backend application. The application itself is deployed separately using **AWS SAM**.

---

# Architecture

```
                   Internet
                       │
               Internet Gateway
                       │
        ┌──────────────┴──────────────┐
        │                             │
 Public Subnet A                Public Subnet B
        │
    NAT Gateway
        │
  Private Route Table
      ├───────────────┐
      │               │
      ▼               ▼
Private Subnet A  Private Subnet B
      │               │
      └──────┬────────┘
             ▼
        AWS Lambda
     (Inside VPC)
             │
             ▼
      Amazon RDS PostgreSQL
             │
             ▼
     AWS Secrets Manager
```

---

# Infrastructure Components

Terraform provisions:

- VPC Networking
- Public & Private Subnets
- NAT Gateway
- Route Tables
- Security Groups
- Amazon RDS PostgreSQL
- Secrets Manager
- Supporting Infrastructure

AWS SAM provisions:

- Lambda Function
- API Gateway
- Lambda Execution Role
- Container Image Deployment

---

# Repository Structure

```
lira-infra/

├── modules/
│   ├── networking/
│   ├── security/
│   ├── rds/
│   └── secrets/
│
├── environments/
│   ├── dev/
│   ├── qa/
│   └── prod/
│
└── README.md
```

---

# Module Overview

## Networking

Creates:

- Public Subnet B
- Private Subnet A
- Private Subnet B
- Elastic IP
- NAT Gateway
- Private Route Table
- Route Table Associations

Imports existing:

- VPC
- Internet Gateway
- Public Route Table
- Public Subnet A
- Public Route Table Association

---

## Security

Creates:

- Lambda Security Group
- PostgreSQL Security Group

Rules

Lambda SG

- Outbound → Allow All

PostgreSQL SG

- Inbound
    - TCP 5432
    - Source → Lambda Security Group

---

## RDS

Creates

- DB Subnet Group
- Parameter Group
- PostgreSQL Instance

Database is deployed inside private subnets.

---

## Secrets

Creates

- Random Password
- Secrets Manager Secret
- Secret Version

Stores

```json
{
  "username": "...",
  "password": "..."
}
```

---

# Deployment Flow

Infrastructure

```
terraform init

terraform plan

terraform apply
```

Application

```
sam build

sam deploy
```

Terraform and SAM are intentionally separated.

Terraform never deploys Lambda.

SAM never provisions infrastructure.

---

# Design Decisions

## Infrastructure Ownership

Terraform owns

- Networking
- Security Groups
- Amazon RDS
- Secrets Manager

AWS SAM owns

- Lambda
- API Gateway
- Lambda Execution Role

---

## Networking

Development

- Single NAT Gateway
- Two Private Subnets
- Two Public Subnets

Production

- One NAT Gateway per Availability Zone (planned)

---

## Database

- Amazon RDS PostgreSQL
- Private Deployment
- Not Publicly Accessible
- Security Group restricted to Lambda only

---

## Secrets

Database credentials are stored in AWS Secrets Manager.

The Lambda retrieves the credentials during runtime.

Passwords are never hardcoded inside the application.

---

# Environment Structure

Each environment has its own Terraform configuration.

```
environments/

dev/

qa/

prod/
```

Each environment may have different

- Instance Sizes
- CIDRs
- Scaling
- Resource Counts

while reusing the same modules.

---

# Outputs

Networking

- VPC ID
- Public Subnet IDs
- Private Subnet IDs

Security

- Lambda Security Group ID
- PostgreSQL Security Group ID

Secrets

- Secret ARN

RDS

- Endpoint
- Port
- Database Name

These outputs are consumed by AWS SAM during deployment.

---

# Integration with AWS SAM

The application repository receives infrastructure values as parameters.

Example

- Lambda Security Group ID
- Private Subnet IDs
- Secret ARN

These are passed during

```
sam deploy
```

using parameter overrides or CI/CD variables.

---

# Development Workflow

```
Write Terraform

↓

terraform fmt

↓

terraform validate

↓

terraform plan

↓

Code Review

↓

terraform apply

↓

sam build

↓

sam deploy
```

---

# Best Practices

- No hardcoded AWS resource IDs
- Reusable Terraform modules
- Least Privilege Security Groups
- Private RDS Deployment
- Secrets stored in AWS Secrets Manager
- Infrastructure and Application managed independently
- Multi-environment support

---

# Future Improvements

- Remote Terraform Backend (S3 + DynamoDB)
- CI/CD Pipeline
- Multi-AZ NAT Gateway (Production)
- Monitoring & Alarms
- Automated Database Migration
- Infrastructure Testing

---

# AWS Services Used

- Amazon VPC
- Internet Gateway
- NAT Gateway
- Route Tables
- Security Groups
- Amazon RDS PostgreSQL
- AWS Secrets Manager
- AWS Lambda
- Amazon API Gateway
- AWS SAM
- Terraform
