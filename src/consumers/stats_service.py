"""Stats Service - Pull-based Consumer

Demonstrates pull-based message consumption with message filtering.
Only processes scoring events due to subscription filter.
"""

import json
import os
from google.cloud import pubsub_v1
from typing import Dict, Any


class StatsService:
    def __init__(self, project_id: str, subscription_name: str):
        self.subscriber = pubsub_v1.SubscriberClient()
        self.subscription_path = self.subscriber.subscription_path(
            project_id, subscription_name
        )
        self.player_stats: Dict[str, Dict[str, int]] = {}

    def process_message(self, message: pubsub_v1.subscriber.message.Message):
        """Process a single stats message"""
        try:
            # Parse message data
            data = json.loads(message.data.decode("utf-8"))
            player = data["player"]
            points = data["points"]
            event = data["event"]

            # Update stats
            if player not in self.player_stats:
                self.player_stats[player] = {"total_points": 0, "events": 0}

            self.player_stats[player]["total_points"] += points
            self.player_stats[player]["events"] += 1

            print(f"Stats Updated: {player} - {event} (+{points} pts)")
            print(
                f"  Total: {self.player_stats[player]['total_points']} points in {self.player_stats[player]['events']} events"
            )

            # Acknowledge message
            message.ack()

        except Exception as e:
            print(f"Error processing stats message: {e}")
            message.nack()

    def start_listening(self, timeout: int = 30):
        """Start pulling messages"""
        print(f"Stats Service listening for {timeout} seconds...")

        flow_control = pubsub_v1.types.FlowControl(max_messages=10)

        with self.subscriber:
            try:
                streaming_pull_future = self.subscriber.subscribe(
                    self.subscription_path,
                    callback=self.process_message,
                    flow_control=flow_control,
                )

                streaming_pull_future.result(timeout=timeout)

            except Exception as e:
                print(f"Stats service stopped: {e}")
            finally:
                streaming_pull_future.cancel()
                self.print_final_stats()

    def print_final_stats(self):
        """Print final statistics"""
        print("\nFINAL PLAYER STATS:")
        for player, stats in self.player_stats.items():
            print(
                f"  {player}: {stats['total_points']} points, {stats['events']} events"
            )


if __name__ == "__main__":
    project_id = os.getenv("PROJECT_ID")
    if not project_id:
        raise ValueError("PROJECT_ID environment variable must be set")

    service = StatsService(project_id, "stats-service-pull")
    service.start_listening(60)
