resource "random_id" "suffix" {
  byte_length = 4
}

resource "random_password" "password" {
  length  = 24
  special = false
}

resource "google_sql_user" "user" {
  name     = var.db_user
  instance = google_sql_database_instance.instance.name
  password = random_password.password.result
}

resource "google_sql_database" "db" {
  name     = var.db_name
  instance = google_sql_database_instance.instance.name
  charset  = "utf8mb4"
}

resource "google_sql_database_instance" "instance" {
  database_version = "MYSQL_5_7"
  name             = "${var.db_name}-${random_id.suffix.hex}"

  settings {
    tier            = var.db_tier
    disk_size       = "10"
    disk_autoresize = "true"

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
