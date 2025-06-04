"""Fantasy Calculator - FastAPI Push Endpoint

Receives push notifications from Pub/Sub and calculates fantasy points.
Demonstrates push-based message consumption.
"""

import json
import base64
import os
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI(title="NBA Fantasy Calculator", version="1.0.0")

# Fantasy point values
FANTASY_POINTS = {
    "score": {"2": 2, "3": 3},
    "rebound": 1.2,
    "assist": 1.5,
    "steal": 2.0,
    "block": 2.0,
}


class PubSubMessage(BaseModel):
    message: Dict[str, Any]


class FantasyCalculator:
    def __init__(self):
        self.total_events = 0
        self.total_fantasy_points = 0.0
        self.player_totals: Dict[str, float] = {}

    def calculate_fantasy_points(self, event_data: dict, attributes: dict) -> float:
        """Calculate fantasy points for an NBA event"""
        event_type = attributes.get("event_type")
        points_scored = int(attributes.get("points", 0))

        fantasy_points = 0.0
        if event_type == "score":
            fantasy_points = FANTASY_POINTS["score"].get(str(points_scored), 0)
        else:
            fantasy_points = FANTASY_POINTS.get(event_type, 0)

        return fantasy_points

    def process_event(self, event_data: dict, attributes: dict) -> dict:
        """Process a single NBA event and return fantasy points"""
        player = event_data["player"]
        fantasy_points = self.calculate_fantasy_points(event_data, attributes)

        # Update totals
        self.total_events += 1
        self.total_fantasy_points += fantasy_points

        if player not in self.player_totals:
            self.player_totals[player] = 0.0
        self.player_totals[player] += fantasy_points

        return {
            "player": player,
            "event": event_data["event"],
            "fantasy_points": fantasy_points,
            "player_total": self.player_totals[player],
        }


# Global calculator instance
calculator = FantasyCalculator()


@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "NBA Fantasy Calculator",
        "events_processed": calculator.total_events,
        "total_fantasy_points": calculator.total_fantasy_points,
    }


@app.get("/stats")
async def get_stats():
    """Get current fantasy point statistics"""
    return {
        "total_events": calculator.total_events,
        "total_fantasy_points": calculator.total_fantasy_points,
        "player_totals": calculator.player_totals,
    }


@app.post("/")
async def handle_pubsub_push(request: Request):
    """Handle Pub/Sub push notifications"""
    try:
        # Parse the Pub/Sub message
        body = await request.json()

        if "message" not in body:
            raise HTTPException(status_code=400, detail="No Pub/Sub message found")

        pubsub_message = body["message"]

        # Decode message data
        if "data" not in pubsub_message:
            raise HTTPException(status_code=400, detail="No message data found")

        message_data = base64.b64decode(pubsub_message["data"]).decode("utf-8")
        attributes = pubsub_message.get("attributes", {})

        # Parse the NBA event
        event_data = json.loads(message_data)

        # Process the event
        result = calculator.process_event(event_data, attributes)

        print(
            f"Fantasy Calculator: {result['player']} earned {result['fantasy_points']} fantasy points"
        )
        print(f"  Player total: {result['player_total']} points")

        return {"status": "success", "result": result}

    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    except Exception as e:
        print(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {e}")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
