provider "aws" {
  region = "us-east-1" # Adjust if your Learner Lab uses a different region
}

# Use the default VPC
data "aws_vpc" "default" {
  default = true
}

# Use a default subnet in the default VPC
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Data source to get the latest Amazon Linux 2 AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

# Security group to allow HTTP traffic on port 5000
resource "aws_security_group" "ec2_sg" {
  name        = "ec2-flask-sg"
  description = "Allow HTTP traffic for Flask API"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# EC2 instance to host the Flask API
resource "aws_instance" "flask_api" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t2.micro"
  vpc_security_group_ids = [aws_security_group.ec2_sg.id]
  subnet_id     = data.aws_subnets.default.ids[0]

  user_data = <<EOF
#!/bin/bash
sudo yum update -y
sudo yum install python3 -y
sudo pip3 install flask
cat << 'EOT' > /home/ec2-user/app.py
from flask import Flask, jsonify
import random
import time

app = Flask(__name__)

@app.route('/healthy')
def healthy():
    return jsonify({"status": "success", "message": "Healthy endpoint"})

@app.route('/unreliable')
def unreliable():
    if random.random() > 0.5:
        return jsonify({"status": "success", "message": "Unreliable endpoint succeeded"}), 200
    else:
        return jsonify({"status": "error", "message": "Unreliable endpoint failed"}), 500

@app.route('/slow')
def slow():
    delay = random.uniform(1, 10)
    time.sleep(delay)
    return jsonify({"status": "success", "message": f"Slow endpoint with {delay:.2f}s delay"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
EOT

sudo python3 /home/ec2-user/app.py &
EOF

  tags = {
    Name = "Flask-API-Instance"
  }
}