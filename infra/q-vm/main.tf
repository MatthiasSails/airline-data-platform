# Q (stage) VM — sibling of the manually-created prod VM (aws-airline-1).
# Three resources: the instance, a static IP, and the firewall rules.

resource "aws_lightsail_instance" "q_vm" {
  name              = var.instance_name
  availability_zone = var.availability_zone
  blueprint_id      = var.blueprint_id
  bundle_id         = var.bundle_id
  key_pair_name     = var.key_pair_name
  user_data         = file("${path.module}/user_data.sh")

  tags = {
    project     = "airline-data-platform"
    environment = "q"
    managed_by  = "terraform"
  }
}

# Without a static IP, Lightsail assigns a new public IP on every stop/start —
# the Portainer endpoint config and ~/.ssh/config would break each time.
# Free of charge while attached to a running instance.
resource "aws_lightsail_static_ip" "q_vm" {
  name = "${var.instance_name}-ip"
}

resource "aws_lightsail_static_ip_attachment" "q_vm" {
  static_ip_name = aws_lightsail_static_ip.q_vm.name
  instance_name  = aws_lightsail_instance.q_vm.name
}

# Firewall (Lightsail's simplified security group). This resource REPLACES the
# default open ports (22, 80) with exactly this list:
#   - 22:  SSH, open (key-auth only, same posture as prod)
#   - 9001: Portainer agent, reachable ONLY from the prod VM (least privilege)
# No 80/443 on purpose — cloudflared connects outbound, no inbound web ports needed.
resource "aws_lightsail_instance_public_ports" "q_vm" {
  instance_name = aws_lightsail_instance.q_vm.name

  port_info {
    protocol  = "tcp"
    from_port = 22
    to_port   = 22
  }

  port_info {
    protocol  = "tcp"
    from_port = 9001
    to_port   = 9001
    cidrs     = ["${var.prod_vm_ip}/32"]
  }
}
