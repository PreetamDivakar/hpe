#!/bin/bash
echo "Starting services..."

sudo systemctl start mosquitto kafka logstash opensearch.service grafana-server

echo "Setup complete!"
