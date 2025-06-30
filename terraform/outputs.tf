output "public_dns" {
  value = aws_instance.resiliency_app.public_dns
}

output "public_ip" {
  value = aws_instance.resiliency_app.public_ip
}

output "api_url" {
  value = "http://${aws_instance.resiliency_app.public_dns}/product-info"
}