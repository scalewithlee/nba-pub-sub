"""Demo Runner

Orchestrates the complete NBA Pub/Sub demonstration.
Runs producer and consumers to show end-to-end message flow.
"""

import os
import sys
import time
import threading
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from producer.game_simulator import NBAEventProducer
from consumers.stats_service import StatsService
from consumers.notification_service import NotificationService


def run_demo():
    """Run the complete NBA Pub/Sub demo"""
    project_id = os.getenv('PROJECT_ID')
    if not project_id:
        raise ValueError("PROJECT_ID environment variable must be set")

    print("NBA Pub/Sub Demo Starting!")
    print("=" * 50)

    # Create services
    producer = NBAEventProducer(project_id, 'nba-game-events')
    stats_service = StatsService(project_id, 'stats-service-pull')
    notification_service = NotificationService(project_id, 'notification-service-flaky')

    # Start consumers in separate threads
    print("Starting consumer services...")
    stats_thread = threading.Thread(
        target=stats_service.start_listening,
        args=(45,),
        name="StatsService"
    )
    notification_thread = threading.Thread(
        target=notification_service.start_listening,
        args=(45,),
        name="NotificationService"
    )

    stats_thread.start()
    notification_thread.start()

    # Give consumers time to start
    print("Waiting for consumers to initialize...")
    time.sleep(3)

    # Simulate game events
    print("\nStarting game event simulation...")
    producer.simulate_game_events(15)

    # Wait for processing to complete
    print("\nWaiting for message processing to complete...")
    stats_thread.join()
    notification_thread.join()

    print("\nDemo Complete!")
    print("\nNext steps to explore:")
    print("1. Check dead letter queue:")
    print("   gcloud pubsub subscriptions pull dead-letter-inspection --auto-ack")
    print("\n2. View fantasy calculator logs:")
    print("   gcloud run services logs read fantasy-calculator --region=us-central1")
    print("\n3. Try message replay:")
    print("   gcloud pubsub subscriptions seek stats-service-pull --time=$(date -d '1 hour ago' --iso-8601)")


if __name__ == "__main__":
    run_demo()
