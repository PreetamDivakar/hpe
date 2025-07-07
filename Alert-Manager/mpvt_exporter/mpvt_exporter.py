import time
import requests
from prometheus_client import start_http_server, Gauge

# Metrics for link and node status
link_status = Gauge('link_status', 'Status of data link between nodes', ['source', 'target'])
node_status = Gauge('node_status', 'Status of each node', ['node'])

def fetch_and_update_metrics():
    try:
        resp = requests.get("http://localhost:5000/api/graph/data")
        data = resp.json()

        # Update edge/link status
        for edge in data.get('edges', []):
            source = edge.get('source')
            target = edge.get('target')
            status = edge.get('mainStat', 0)
            link_status.labels(source=source, target=target).set(status)

        # Update node status
        for node in data.get('nodes', []):
            name = node.get('name')
            status = node.get('mainStat', 0)
            node_status.labels(node=name).set(status)

    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    # Prometheus will scrape from http://localhost:9101/metrics
    start_http_server(9101)
    print("Daemon running on port 9101...")

    while True:
        fetch_and_update_metrics()
        time.sleep(30)  # Match with Prometheus scrape interval

