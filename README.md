# nba-pub-sub

```
nba-pubsub-demo/
├── pyproject.toml              # UV package configuration (already exists)
├── README.md                   # Setup instructions
├── terraform/
│   └── main.tf                 # Infrastructure configuration (already exists)
├── src/
│   ├── __init__.py
│   ├── producer/
│   │   ├── __init__.py
│   │   └── game_simulator.py   # NBA event producer
│   ├── consumers/
│   │   ├── __init__.py
│   │   ├── stats_service.py    # Pull-based stats consumer
│   │   └── notification_service.py  # Flaky consumer for dead letter demo
│   └── fantasy_calculator/
│       ├── __init__.py
│       ├── main.py             # FastAPI app for push endpoint
│       └── Dockerfile          # Container configuration
├── scripts/
│   ├── run_demo.py             # Orchestrates the complete demo
│   └── test_manual.py          # Manual testing commands
└── requirements.txt            # Python dependencies
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