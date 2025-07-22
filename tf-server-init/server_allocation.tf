terraform {
    required_providers {
      hcloud = {
        source = "opentofu/hcloud"
        version = "1.32.0"
      } 
    }
}

variable "hcloud_token" {
    sensitive = true
}

provider "hcloud" {
    token = var.hcloud_token
}

resource "hcloud_server" "mc_server" {
    name = "mc-server"
    server_type = "ccx33"
    image = "ubuntu-24.04"
    location = "fsn1"
    ssh_keys = ["100417185"]
    user_data = file("cloud-init.sh")
}

output "instance_ips" {
    value = hcloud_server.mc_server.ipv4_address
}