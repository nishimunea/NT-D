resource "google_container_cluster" "ntd_cluster" {
  name                     = "ntd-cluster"
  network                  = google_compute_network.private_network.name
  subnetwork               = google_compute_subnetwork.private_subnet.self_link
  initial_node_count       = 1
  remove_default_node_pool = true

  addons_config {
    http_load_balancing {
      disabled = false
    }
    network_policy_config {
      disabled = true
    }

    horizontal_pod_autoscaling {
      disabled = true
    }
  }

  ip_allocation_policy {}

  master_auth {
    username = "admin"
  }

  logging_service    = "none"
  monitoring_service = "none"

  private_cluster_config {
    enable_private_endpoint = false
    enable_private_nodes    = true
    master_ipv4_cidr_block  = "10.2.0.0/28"
  }
}


resource "google_container_node_pool" "ntd_node_pool" {
  name       = "ntd-node-pool"
  cluster    = google_container_cluster.ntd_cluster.name
  node_count = 1

  management {
    auto_repair  = true
    auto_upgrade = false
  }

  autoscaling {
    min_node_count = 1
    max_node_count = 5
  }

  node_config {
    metadata = {
      disable-legacy-endpoints = "true"
    }

    machine_type = "n1-standard-1"
    oauth_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
  }
}
