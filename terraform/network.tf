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

resource "google_compute_router" "ntd_egress_router" {
  name    = "ntd-egress-router"
  network = google_compute_network.private_network.self_link
}

resource "google_compute_address" "ntd_egress_ip" {
  name = "ntd-egress-ip"
}

resource "google_compute_router_nat" "ntd_egress_nat" {
  name                               = "ntd-egress-nat"
  router                             = google_compute_router.ntd_egress_router.name
  nat_ip_allocate_option             = "MANUAL_ONLY"
  nat_ips                            = [google_compute_address.ntd_egress_ip.self_link]
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}