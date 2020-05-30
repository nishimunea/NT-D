resource "google_compute_network" "private_network" {
  name                    = "ntd-private-vpc"
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
}

resource "google_compute_subnetwork" "private_subnet" {
  name                     = "ntd-private-subnet"
  network                  = google_compute_network.private_network.self_link
  ip_cidr_range            = "10.0.0.0/16"
  private_ip_google_access = true
}

resource "google_compute_firewall" "egress" {
  name      = "ntd-egress-firewall"
  direction = "EGRESS"
  network   = google_compute_network.private_network.name

  allow {
    protocol = "all"
  }
}
