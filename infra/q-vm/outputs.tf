output "q_vm_public_ip" {
  description = "Static public IP of the Q VM (for ~/.ssh/config and the Portainer endpoint)"
  value       = aws_lightsail_static_ip.q_vm.ip_address
}

output "q_vm_username" {
  description = "Default SSH user on the ubuntu blueprint"
  value       = aws_lightsail_instance.q_vm.username
}
