resource "random_id" "db_name_suffix" {
  byte_length = 4
}

resource "google_sql_user" "user" {
  name     = "${var.db_user}"
  instance = "${google_sql_database_instance.instance.name}"
  password = "${var.db_password}"
}

resource "google_sql_database" "db" {
  name     = "${var.db_name}"
  instance = "${google_sql_database_instance.instance.name}"
  charset  = "utf8mb4"
}

resource "google_sql_database_instance" "instance" {
  provider         = "google-beta"
  database_version = "MYSQL_5_7"
  name             = "${var.db_name}-${random_id.db_name_suffix.hex}"

  depends_on = ["google_service_networking_connection.private_conn"]

  settings {
    tier            = "${var.db_tier}"
    disk_size       = "10"
    disk_autoresize = "true"

    ip_configuration {
      ipv4_enabled    = "false"
      private_network = "${google_compute_network.private_network.self_link}"
      require_ssl     = "false"
    }

    database_flags {
      name  = "character_set_server"
      value = "utf8mb4"
    }

    database_flags {
      name  = "default_time_zone"
      value = "+00:00"
    }

    database_flags {
      name  = "slow_query_log"
      value = "on"
    }

    backup_configuration {
      enabled = true
    }
  }
}
