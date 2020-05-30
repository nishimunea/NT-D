output "DB_NAME" {
  value = "${google_sql_database.db.name}"
}

output "DB_HOST" {
  value = "${google_sql_database_instance.instance.private_ip_address}"
}

output "DB_USER" {
  value = "${google_sql_user.user.name}"
}

output "DB_PASSWORD" {
  value = "${google_sql_user.user.password}"
}
