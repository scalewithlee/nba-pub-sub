#!/bin/bash
PROJECT_ID="your-project-id"

echo "Starting complete cleanup..."

# 1. Destroy Terraform resources
echo "1. Destroying Terraform resources..."
cd terraform
terraform destroy -var="project_id=$PROJECT_ID" -auto-approve

# 2. Clean up container images
echo "2. Cleaning up container images..."
gcloud container images list --repository=gcr.io/$PROJECT_ID --format="value(name)" | \
while read image; do
  echo "Deleting image: $image"
  gcloud container images delete $image --force-delete-tags --quiet
done

# 3. Check for any remaining Pub/Sub resources
echo "3. Checking for remaining Pub/Sub resources..."
gcloud pubsub topics list --format="value(name)" | grep nba || echo "No NBA topics found"
gcloud pubsub subscriptions list --format="value(name)" | grep -E "(stats|fantasy|notification)" || echo "No demo subscriptions found"

# 4. Check for Cloud Run services
echo "4. Checking for Cloud Run services..."
gcloud run services list --format="value(metadata.name)" | grep fantasy || echo "No fantasy calculator service found"

echo "Cleanup complete!"
