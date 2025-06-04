"""Notification Service - Flaky Consumer

Demonstrates error handling and dead letter queues.
Intentionally fails some messages to show retry behavior.
"""

import json
import random
import os
from google.cloud import pubsub_v1


class NotificationService:
    def __init__(
        self, project_id: str, subscription_name: str, failure_rate: float = 0.4
    ):
        self.subscriber = pubsub_v1.SubscriberClient()
        self.subscription_path = self.subscriber.subscription_path(
            project_id, subscription_name
        )
        self.failure_rate = failure_rate
        self.processed_count = 0
        self.failed_count = 0

    def process_message(self, message: pubsub_v1.subscriber.message.Message):
        """Process notification with intentional failures"""
        try:
            data = json.loads(message.data.decode("utf-8"))
            player = data["player"]
            event = data["event"]

            # Simulate random failures
            if random.random() < self.failure_rate:
                self.failed_count += 1
                print(
                    f"Notification FAILED for: {player} {event} (failure #{self.failed_count})"
                )
                # Don't acknowledge - this will cause retry and eventually dead letter
                message.nack()
                return

            # Simulate successful notification
            self.processed_count += 1
            print(
                f"Notification sent: {player} {event} (success #{self.processed_count})"
            )
            message.ack()

        except Exception as e:
            print(f"Error in notification service: {e}")
            message.nack()

    def start_listening(self, timeout: int = 30):
        """Start listening with failures"""
        print(
            f"Notification Service listening (with {self.failure_rate * 100}% failure rate)..."
        )

        flow_control = pubsub_v1.types.FlowControl(max_messages=5)

        with self.subscriber:
            try:
                streaming_pull_future = self.subscriber.subscribe(
                    self.subscription_path,
                    callback=self.process_message,
                    flow_control=flow_control,
                )

                streaming_pull_future.result(timeout=timeout)

            except Exception as e:
                print(f"Notification service stopped: {e}")
            finally:
                streaming_pull_future.cancel()
                self.print_summary()

    def print_summary(self):
        """Print processing summary"""
        total = self.processed_count + self.failed_count
        print(f"\nNotification Service Summary:")
        print(f"  Processed: {self.processed_count}")
        print(f"  Failed: {self.failed_count}")
        print(f"  Total: {total}")
        if total > 0:
            print(f"  Success Rate: {(self.processed_count / total) * 100:.1f}%")


if __name__ == "__main__":
    project_id = os.getenv("PROJECT_ID")
    if not project_id:
        raise ValueError("PROJECT_ID environment variable must be set")

    service = NotificationService(project_id, "notification-service-flaky")
    service.start_listening(60)
