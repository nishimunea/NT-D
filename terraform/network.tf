resource "google_compute_network" "private_network" {
  name                    = "ntd-private-network"
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
}

resource "google_compute_subnetwork" "private_subnet" {
  name                     = "ntd-private-subnet"
  network                  = "${google_compute_network.private_network.self_link}"
  ip_cidr_range            = "10.0.0.0/16"
  private_ip_google_access = true
}

resource "google_compute_firewall" "egress" {
  name      = "ntd-egress-firewall"
  direction = "EGRESS"
  network   = "${google_compute_network.private_network.name}"

  allow {
    protocol = "all"
  }
}

resource "google_compute_global_address" "private_ips" {
  name          = "ntd-private-ip-alloc"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = "${google_compute_network.private_network.self_link}"
}

resource "google_service_networking_connection" "private_conn" {
  provider                = "google-beta"
  network                 = "${google_compute_network.private_network.self_link}"
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = ["${google_compute_global_address.private_ips.name}"]
}

resource "google_vpc_access_connector" "ntd_serverless_vpc_conn" {
  provider      = "google-beta"
  name          = "ntd-serverless-vpc-conn"
  region        = "${var.region}"
  ip_cidr_range = "10.8.0.0/28"
  network       = "${google_compute_network.private_network.name}"
}
