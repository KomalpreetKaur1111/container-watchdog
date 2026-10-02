# Container Watchdog

A self-healing container monitoring system that detects when a Docker container goes down and automatically restarts it — with a live web dashboard showing real-time health, resource usage, and recovery history.

## Problem it solves

In real infrastructure, a crashed service usually stays down until someone notices and manually restarts it. This project demonstrates the same self-healing principle used by production tools like AWS ECS health checks and Kubernetes restart policies, built manually to understand the underlying mechanism.

## Architecture

Flask App (in Docker) is checked by the Watchdog Script every 5 seconds.
The Watchdog Script writes status to a file, which the Live Dashboard (Flask) reads and displays.

- app.py — the monitored application, running inside a Docker container
- watchdog.py — auto-discovers containers labeled watch=true, checks their status every 5 seconds via the Docker CLI, auto-restarts them if down, and logs CPU/memory usage
- dashboard.py — a separate Flask app that reads the watchdog's status file and displays it as a live, auto-refreshing dashboard with one card per container, including a Simulate Crash button for live demos

## Tech Stack

- Python, Flask
- Docker
- HTML/CSS with Jinja templating

## Features

- Automatic health checking every 5 seconds
- Automatic container restart on failure
- Multi-container support via Docker label-based auto-discovery (no hardcoded container names)
- Live CPU and memory usage per container
- Restart counter per container
- Auto-refreshing dashboard (updates every 3 seconds)
- One-click crash simulation button per container, for live demos

## How to Run

1. Build and run the monitored app, labeled for discovery:

docker build -t watchdog-app .
docker run -d -p 5000:5000 --name watchdog-container --label watch=true watchdog-app

2. Start the watchdog:

python watchdog.py

3. Start the dashboard (in a separate terminal):

python dashboard.py

4. Open http://localhost:6060 in your browser.

## Demo

Click "Simulate Crash" on any container's card and watch its status flip from healthy to down, then automatically recover within seconds — with the event logged in that card's activity log.

## Limitations / Future Work

- Health checks are restart-based, not threshold/predictive; a natural extension would be flagging sustained high CPU/memory as unhealthy before an actual crash
- Runs the watchdog and dashboard locally rather than containerized themselves; this could be extended using Docker-in-Docker (mounting the Docker socket) so the entire system ships as a single portable image
- A production version would deploy behind a reverse proxy (Nginx) and run on an actual cloud VM