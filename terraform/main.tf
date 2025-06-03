# This creates a complete Pub/Sub system with multiple consumers demonstrating different patterns
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Variables
variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

# Provider
provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "pubsub.googleapis.com",
    "cloudfunctions.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com"
  ])

  service            = each.value
  disable_on_destroy = false
}

# Main Pub/Sub Topic - where all NBA game events are published
resource "google_pubsub_topic" "nba_game_events" {
  name = "nba-game-events"

  depends_on = [google_project_service.required_apis]
}

# Dead Letter Topic - where failed messages go
resource "google_pubsub_topic" "dead_letter" {
  name = "nba-dead-letter"
}

# Dead Letter Subscription - so we can inspect failed messages
resource "google_pubsub_subscription" "dead_letter_sub" {
  name  = "dead-letter-inspection"
  topic = google_pubsub_topic.dead_letter.name

  message_retention_duration = "604800s" # 7 days
}

# Subscription 1: Stats Service (PULL-based)
# This simulates a service that polls for messages to update player stats
resource "google_pubsub_subscription" "stats_service" {
  name  = "stats-service-pull"
  topic = google_pubsub_topic.nba_game_events.name

  # Pull-based configuration
  ack_deadline_seconds = 60

  # Message retention and replay capabilities
  message_retention_duration = "604800s" # 7 days - allows message replay
  retain_acked_messages      = true      # Keep messages even after ack for replay

  # Dead letter policy - after 5 failed attempts, send to dead letter
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = 5
  }

  # Filter for only scoring events (demonstrates message filtering)
  filter = "attributes.event_type = \"score\""
}

# Subscription 2: Fantasy Points Calculator (PUSH-based)
# This will push messages to a Cloud Run service
resource "google_pubsub_subscription" "fantasy_calculator" {
  name  = "fantasy-calculator-push"
  topic = google_pubsub_topic.nba_game_events.name

  # Push configuration - will send HTTP POST to our Cloud Run service
  push_config {
    push_endpoint = google_cloud_run_v2_service.fantasy_calculator.uri

    # Authentication for the push endpoint
    oidc_token {
      service_account_email = google_service_account.pubsub_invoker.email
    }
  }

  ack_deadline_seconds = 30

  # Only process events for star players
  filter = "attributes.player_rating = \"star\""
}

# Subscription 3: Notification Service (PULL with failures)
# This simulates a flaky service that sometimes fails to process messages
resource "google_pubsub_subscription" "notification_service" {
  name  = "notification-service-flaky"
  topic = google_pubsub_topic.nba_game_events.name

  ack_deadline_seconds = 20

  # Aggressive dead letter policy to demonstrate failures
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = 3
  }

  # Retry policy - exponential backoff for failed messages
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "300s"
  }
}

# Service Account for Pub/Sub to invoke Cloud Run
resource "google_service_account" "pubsub_invoker" {
  account_id   = "pubsub-cloud-run-invoker"
  display_name = "Pub/Sub Cloud Run Invoker"
}

# Grant the service account permission to invoke Cloud Run
resource "google_cloud_run_service_iam_member" "invoker" {
  service  = google_cloud_run_v2_service.fantasy_calculator.name
  location = google_cloud_run_v2_service.fantasy_calculator.location
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.pubsub_invoker.email}"
}

# Cloud Run service for Fantasy Points Calculator (PUSH endpoint)
resource "google_cloud_run_v2_service" "fantasy_calculator" {
  name     = "fantasy-calculator"
  location = var.region

  depends_on = [google_project_service.required_apis]

  template {
    containers {
      # Simple Python container that processes pushed messages
      image = "gcr.io/cloudrun/hello" # We'll replace this with our custom image

      ports {
        container_port = 8080
      }

      env {
        name  = "PROJECT_ID"
        value = var.project_id
      }
    }

    # Allow unauthenticated requests from Pub/Sub
    service_account = google_service_account.pubsub_invoker.email
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_ALLOCATION_LATEST"
  }
}

# IAM permissions for our demo applications
resource "google_project_iam_member" "pubsub_subscriber" {
  project = var.project_id
  role    = "roles/pubsub.subscriber"
  member  = "serviceAccount:${google_service_account.demo_app.email}"
}

resource "google_project_iam_member" "pubsub_publisher" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.demo_app.email}"
}

# Service account for our demo applications
resource "google_service_account" "demo_app" {
  account_id   = "nba-demo-app"
  display_name = "NBA Demo Application"
}

# Output important information
output "topic_name" {
  description = "Name of the main Pub/Sub topic"
  value       = google_pubsub_topic.nba_game_events.name
}

output "subscriptions" {
  description = "Created subscriptions and their types"
  value = {
    stats_service        = "PULL (filters: score events only)"
    fantasy_calculator   = "PUSH (filters: star players only)"
    notification_service = "PULL (flaky, demonstrates dead letter)"
  }
}

output "dead_letter_topic" {
  description = "Dead letter topic for failed messages"
  value       = google_pubsub_topic.dead_letter.name
}

output "cloud_run_url" {
  description = "URL of the Fantasy Calculator Cloud Run service"
  value       = google_cloud_run_v2_service.fantasy_calculator.uri
}

output "demo_commands" {
  description = "Commands to test the system"
  value = {
    publish_message   = "gcloud pubsub topics publish ${google_pubsub_topic.nba_game_events.name} --message='LeBron James scored 2 points' --attribute=event_type=score,player_rating=star,team=LAL"
    pull_stats        = "gcloud pubsub subscriptions pull ${google_pubsub_subscription.stats_service.name} --auto-ack"
    view_dead_letters = "gcloud pubsub subscriptions pull ${google_pubsub_subscription.dead_letter_sub.name} --auto-ack"
  }
}
