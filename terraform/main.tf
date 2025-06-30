provider "aws" {
  region = var.region
}

resource "aws_security_group" "web_sg" {
  name        = "web-sg"
  description = "Allow HTTP and SSH access"

  ingress {
    from_port   = 80
    to_port     = 80
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


resource "aws_instance" "resiliency_app" {
  ami                    = "ami-0c2b8ca1dad447f8a" # Amazon Linux 2
  instance_type          = var.instance_type
  security_groups        = [aws_security_group.web_sg.name]

  user_data = <<-EOF
              #!/bin/bash
              yum update -y
              yum install -y python3 git

              cd /home/ec2-user
              git clone https://github.com/vinay682000/Vinay_SRO_Lab6.git 
              cd Vinay_SRO_Lab6

              pip3 install -r requirements.txt
              pip3 install uvicorn fastapi

              # Start FastAPI from api.main:app on port 80
              nohup uvicorn api.main:app --host 0.0.0.0 --port 80 &
              EOF

  tags = {
    Name = "ResiliencyApp"
  }
}