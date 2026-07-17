variable "instance_name" {
  description = "Lightsail instance name for the Q (stage) VM"
  type        = string
  default     = "aws-airline-q-1"
}

variable "availability_zone" {
  description = "AZ, same as the prod VM (aws-airline-1)"
  type        = string
  default     = "eu-central-1a"
}

variable "blueprint_id" {
  description = "OS image, same as the prod VM"
  type        = string
  default     = "ubuntu_24_04"
}

variable "bundle_id" {
  description = "Instance size. micro_3_0 = 1 GB RAM / USD 7 per month — Q only runs the gold-dash stack + Portainer agent + cloudflared. Prod uses small_3_0 (2 GB)."
  type        = string
  default     = "micro_3_0"
}

variable "key_pair_name" {
  description = "Existing Lightsail SSH key pair (shared with the prod VM)"
  type        = string
  default     = "airline_vm"
}

# No default on purpose: real IPs never go into tracked files (see CLAUDE.md,
# ADR 007/014 leak history). Supplied via the gitignored terraform.tfvars.
variable "prod_vm_ip" {
  description = "Public IPv4 of the prod VM — the only host allowed to reach the Portainer agent port"
  type        = string
}
