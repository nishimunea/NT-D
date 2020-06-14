provider "google" {
  region = var.region
}

data "google_project" "project" {}
