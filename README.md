# OpenEPM Agent

The agent component of the OpenEPM lightweight endpoint management system for SMEs.

## Features
- Registers itself with the server
- Sends periodic heartbeats
- Polls for commands
- Executes commands locally
- Submits command results back to the server

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Running

```bash
export OPENEPM_SERVER_URL=http://localhost:5000
openepm-agent start
```

## Service installation

Edit `openepm-agent.service` with your actual paths, then:

```bash
sudo cp openepm-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable openepm-agent
sudo systemctl start openepm-agent
sudo systemctl status openepm-agent
```
