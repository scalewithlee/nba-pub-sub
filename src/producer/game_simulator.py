"""NBA Game Event Producer

Simulates real NBA game events and publishes them to Pub/Sub.
Demonstrates message publishing with attributes for filtering.
"""

import json
import random
import time
from datetime import datetime
from google.cloud import pubsub_v1
import os

# NBA data for realistic events
NBA_PLAYERS = [
    {"name": "LeBron James", "team": "LAL", "rating": "star"},
    {"name": "Stephen Curry", "team": "GSW", "rating": "star"},
    {"name": "Giannis Antetokounmpo", "team": "MIL", "rating": "star"},
    {"name": "Jayson Tatum", "team": "BOS", "rating": "star"},
    {"name": "Austin Reaves", "team": "LAL", "rating": "regular"},
    {"name": "James Harden", "team": "LAC", "rating": "regular"},
]

EVENT_TYPES = [
    {"type": "score", "points": [2, 3], "description": "scored"},
    {"type": "rebound", "points": [0], "description": "grabbed a rebound"},
    {"type": "assist", "points": [0], "description": "made an assist"},
    {"type": "steal", "points": [0], "description": "made a steal"},
    {"type": "block", "points": [0], "description": "blocked a shot"},
]


class NBAEventProducer:
    def __init__(self, project_id: str, topic_name: str):
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(project_id, topic_name)

    def publish_single_event(self, player_name: str = "", event_type: str = "") -> dict:
        """Publish a single NBA event"""
        if player_name:
            player = next(
                (p for p in NBA_PLAYERS if p["name"] == player_name),
                random.choice(NBA_PLAYERS),
            )
        else:
            player = random.choice(NBA_PLAYERS)

        if event_type:
            event = next(
                (e for e in EVENT_TYPES if e["type"] == event_type),
                random.choice(EVENT_TYPES),
            )
        else:
            event = random.choice(EVENT_TYPES)

        points = random.choice(event["points"])

        # Create message
        message_data = {
            "player": player["name"],
            "team": player["team"],
            "event": event["description"],
            "points": points,
            "timestamp": datetime.now().isoformat(),
            "game_id": "LAL_vs_GSW_2024_01_15",
        }

        # Message attributes for filtering
        attributes = {
            "event_type": event["type"],
            "player_rating": player["rating"],
            "team": player["team"],
            "points": str(points),
        }

        # Publish message
        message_json = json.dumps(message_data)
        future = self.publisher.publish(
            self.topic_path, message_json.encode("utf-8"), **attributes
        )

        result = future.result()
        print(
            f"Published: {player['name']} {event['description']} ({points} pts) - Message ID: {result}"
        )

        return message_data

    def simulate_game_events(
        self, num_events: int = 10, delay_range: tuple = (0.5, 2.0)
    ):
        """Simulate random NBA game events"""
        print(f"Starting NBA game simulation - publishing {num_events} events")

        events = []
        for i in range(num_events):
            event_data = self.publish_single_event()
            events.append(event_data)

            # Add realistic timing between events
            time.sleep(random.uniform(*delay_range))

        print("Game simulation complete!")
        return events


if __name__ == "__main__":
    project_id = os.getenv("PROJECT_ID")
    if not project_id:
        raise ValueError("PROJECT_ID environment variable must be set")

    producer = NBAEventProducer(project_id, "nba-game-events")
    producer.simulate_game_events(15)
