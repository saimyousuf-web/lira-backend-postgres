resource "aws_vpc" "this" {

  cidr_block = var.vpc_cidr

  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "lira-vpc"
  }
}


resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = "lira-igw"
  }
}


resource "aws_subnet" "public_a" {

  vpc_id = aws_vpc.this.id

  cidr_block = var.public_subnet_a_cidr

  availability_zone = var.public_subnet_a_az

  map_public_ip_on_launch = true

  tags = {
    Name = "lira-public-subnet"
  }
}

resource "aws_route_table" "public" {

  vpc_id = aws_vpc.this.id

  route {

    cidr_block = "0.0.0.0/0"

    gateway_id = aws_internet_gateway.this.id
  }

  tags = {
    Name = "lira-public-rt"
  }
}

resource "aws_route_table_association" "public_a" {

  subnet_id = aws_subnet.public_a.id

  route_table_id = aws_route_table.public.id
}


resource "aws_subnet" "public_b" {

  vpc_id = aws_vpc.this.id

  cidr_block = var.public_subnet_b_cidr

  availability_zone = var.public_subnet_b_az

  map_public_ip_on_launch = true

  tags = {

    Name = "${var.environment}-lira-public-subnet-b"

  }

}

resource "aws_route_table_association" "public_b" {

  subnet_id = aws_subnet.public_b.id

  route_table_id = aws_route_table.public.id

}

resource "aws_subnet" "private_a" {

  vpc_id = aws_vpc.this.id

  cidr_block = var.private_subnet_a_cidr

  availability_zone = var.private_subnet_a_az

  map_public_ip_on_launch = false

  tags = {

    Name = "${var.environment}-lira-private-subnet-a"

  }
}

resource "aws_subnet" "private_b" {

  vpc_id = aws_vpc.this.id

  cidr_block = var.private_subnet_b_cidr

  availability_zone = var.private_subnet_b_az

  map_public_ip_on_launch = false

  tags = {

    Name = "${var.environment}-lira-private-subnet-b"

  }

}


resource "aws_eip" "nat" {

  domain = "vpc"

  tags = {

    Name = "${var.environment}-lira-nat-eip"

  }

}


resource "aws_nat_gateway" "this" {

  allocation_id = aws_eip.nat.id

  subnet_id = aws_subnet.public_a.id

  tags = {

    Name = "lira-nat"

  }

  depends_on = [

    aws_internet_gateway.this

  ]

}


resource "aws_route_table" "private" {

  vpc_id = aws_vpc.this.id

  route {

    cidr_block = "0.0.0.0/0"

    nat_gateway_id = aws_nat_gateway.this.id

  }

  tags = {

    Name = "lira-private-rt"

  }

}


resource "aws_route_table_association" "private_a" {

  subnet_id = aws_subnet.private_a.id

  route_table_id = aws_route_table.private.id

}

resource "aws_route_table_association" "private_b" {

  subnet_id = aws_subnet.private_b.id

  route_table_id = aws_route_table.private.id

}

