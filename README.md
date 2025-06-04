# nba-pub-sub

Demonstrates Google Cloud Pub/Sub patterns using NBA game events.

## Setup

### Prerequisites
- GCP account with billing enabled
- gcloud CLI installed and authenticated
- UV package manager
- Terraform

### Install Dependencies
```bash
uv sync
```

### Deploy Infrastructure
```bash
export PROJECT_ID="your-gcp-project-id"
cd terraform
terraform init
terraform plan -var="project_id=$PROJECT_ID"
terraform apply -var="project_id=$PROJECT_ID"
```

### Build and Deploy Fantasy Calculator
```bash
# Build container
gcloud builds submit src/fantasy_calculator --tag gcr.io/$PROJECT_ID/fantasy-calculator

# Update Cloud Run service
gcloud run deploy fantasy-calculator \
  --image gcr.io/$PROJECT_ID/fantasy-calculator \
  --region us-central1 \
  --allow-unauthenticated
```

## Usage

### Run Complete Demo
```bash
export PROJECT_ID="your-gcp-project-id"
uv run scripts/run_demo.py
```

### Manual Testing
```bash
# Publish test events
uv run scripts/test_manual.py --publish

# Show gcloud commands
uv run scripts/test_manual.py --commands
```

### Individual Components
```bash
# Run producer only
export PROJECT_ID="your-gcp-project-id"
uv run src/producer/game_simulator.py

# Run stats consumer only
uv run src/consumers/stats_service.py

# Run notification consumer only
uv run src/consumers/notification_service.py
```

## Key Files

| File | Purpose |
|------|---------|
| `terraform/main.tf` | GCP infrastructure (topics, subscriptions, Cloud Run) |
| `src/producer/game_simulator.py` | Publishes NBA game events to Pub/Sub |
| `src/consumers/stats_service.py` | Pull-based consumer for player statistics |
| `src/consumers/notification_service.py` | Flaky consumer demonstrating dead letters |
| `src/fantasy_calculator/main.py` | FastAPI app receiving push notifications |
| `scripts/run_demo.py` | Runs complete end-to-end demonstration |
| `scripts/test_manual.py` | Manual testing and gcloud commands |

## Pub/Sub Features Demonstrated

- **Message Filtering**: Different subscriptions receive different events
- **Pull vs Push**: Stats service polls, fantasy calculator receives pushes
- **Dead Letter Queues**: Failed notifications land in dead letter topic
- **Message Replay**: Retained messages can be reprocessed
- **Error Handling**: Retry policies and acknowledgment patterns

## Testing Commands

```bash
# Pull from subscriptions
gcloud pubsub subscriptions pull stats-service-pull --auto-ack --limit=5
gcloud pubsub subscriptions pull notification-service-flaky --auto-ack --limit=5

# Check dead letters
gcloud pubsub subscriptions pull dead-letter-inspection --auto-ack --limit=5

# View fantasy calculator logs
gcloud run services logs read fantasy-calculator --region=us-central1

# Message replay
gcloud pubsub subscriptions seek stats-service-pull --time=$(date -d '1 hour ago' --iso-8601)
```

## Cleanup
```bash
cd terraform
terraform destroy -var="project_id=$PROJECT_ID"
```
# nba-pub-sub
