"""Manual Testing Scripts

Provides functions for manual testing and gcloud command examples.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from producer.game_simulator import NBAEventProducer


def publish_test_events():
    """Publish a few test events manually"""
    project_id = os.getenv("PROJECT_ID")
    if not project_id:
        raise ValueError("PROJECT_ID environment variable must be set")

    producer = NBAEventProducer(project_id, "nba-game-events")

    print("Publishing test events...")

    # Publish a star player scoring event (will trigger both stats and fantasy)
    producer.publish_single_event("LeBron James", "score")

    # Publish a regular player rebound (will only trigger stats)
    producer.publish_single_event("Austin Reaves", "rebound")

    # Publish a random event
    producer.publish_single_event()

    print("Test events published!")


def print_gcloud_commands():
    """Print useful gcloud commands for manual testing"""
    print("Manual Testing Commands:")
    print("=" * 40)

    print("\n1. Publish messages manually:")
    print("gcloud pubsub topics publish nba-game-events \\")
    print(
        '  --message=\'{"player":"LeBron James","event":"scored 3 points","points":3}\' \\'
    )
    print("  --attribute=event_type=score,player_rating=star,team=LAL")

    print("\n2. Pull from subscriptions:")
    print("gcloud pubsub subscriptions pull stats-service-pull --auto-ack --limit=5")
    print(
        "gcloud pubsub subscriptions pull notification-service-flaky --auto-ack --limit=5"
    )

    print("\n3. Check dead letter queue:")
    print(
        "gcloud pubsub subscriptions pull dead-letter-inspection --auto-ack --limit=5"
    )

    print("\n4. View Cloud Run logs:")
    print("gcloud run services logs read fantasy-calculator --region=us-central1")

    print("\n5. Message replay (seek to 1 hour ago):")
    print(
        "gcloud pubsub subscriptions seek stats-service-pull --time=$(date -d '1 hour ago' --iso-8601)"
    )

    print("\n6. Monitor subscription metrics:")
    print("gcloud pubsub subscriptions describe stats-service-pull")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manual testing utilities")
    parser.add_argument("--publish", action="store_true", help="Publish test events")
    parser.add_argument("--commands", action="store_true", help="Show gcloud commands")

    args = parser.parse_args()

    if args.publish:
        publish_test_events()
    elif args.commands:
        print_gcloud_commands()
    else:
        print("Use --publish to send test events or --commands to see manual commands")
        print_gcloud_commands()
