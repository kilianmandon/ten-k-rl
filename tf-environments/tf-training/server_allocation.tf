terraform {
  required_providers {
    digitalocean = {
      source = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

variable "do_token" {
    sensitive = true
}

provider "digitalocean" {
    token = var.do_token
}

data "digitalocean_ssh_key" "terraform" {
  name = "digital-ocean"
}

resource "digitalocean_droplet" "ten-k-training" {
  image = "gpu-h100x1-base"
  name = "ten-k-training"
  region = "tor1"
  size = "gpu-4000adax1-20gb"
  ssh_keys = [
    data.digitalocean_ssh_key.terraform.id
  ]
  user_data = file("cloud-init.sh")

}

output "instance_ips" {
    value = digitalocean_droplet.ten-k-training.ipv4_address
}