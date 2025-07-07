from prometheus_client import start_http_server, Gauge
import time
import requests

# Existing metric for links
link_status = Gauge('link_status', 'Status of data link between nodes', ['source', 'target'])

# New metric for nodes
node_status = Gauge('node_status', 'Status of individual nodes', ['node'])

def fetch_and_update_metrics():
    try:
        resp = requests.get("http://localhost:5000/api/graph/data")
        data = resp.json()

        # Link metrics
        for edge in data.get('edges', []):
            source = edge.get('source')
            target = edge.get('target')
            status = edge.get('mainStat', 0)
            link_status.labels(source=source, target=target).set(status)

        # Node metrics
        for node in data.get('nodes', []):
            node_id = node.get('id')
            main_stat = node.get('mainStat', 'Inactive')  # Default to Inactive if missing
            numeric_status = 1 if main_stat.lower() == 'active' else 0
            node_status.labels(node=node_id).set(numeric_status)

    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    start_http_server(9101)
    print("Daemon running on port 9101...")

    while True:
        fetch_and_update_metrics()
        time.sleep(30)



