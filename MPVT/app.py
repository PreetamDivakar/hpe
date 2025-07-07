from coolingComponents import kafkaComp, mosquittoComp, logstashComp, opensearchComp
from flask import Flask, jsonify, request, render_template
from data import Logger, dataflow
import yaml
import subprocess
import os
from datetime import datetime
import pytz
from markupsafe import Markup
import re
import glob

app = Flask(__name__)
log = Logger()

ADMIN_PASSWORD = "admin"

opensearch_status = "Inactive"
kafka_status = "Inactive"
mosquitto_status = "Inactive"
logstash_status = "Inactive"

opensearch_uptime = "0 days, 0 hours, 0 minutes, 0 seconds"
kafka_uptime = "0 days, 0 hours, 0 minutes, 0 seconds"
mosquitto_uptime = "0 days, 0 hours, 0 minutes, 0 seconds"
logstash_uptime = "0 days, 0 hours, 0 minutes, 0 seconds"

opensearch_node_color = "red"
kafka_node_color = "red"
mosquitto_node_color = "red"
logstash_node_color = "red"

mqtt_to_kafka_edge = "red"
kafka_to_logstash_edge = "red"
logstash_to_opensearch_edge = "red"

mqtt_to_kafka_mainStat = 0.0
kafka_to_log_mainStat = 0.0
log_to_open_mainStat = 0.0


@app.route('/api/graph/fields')
def fetch_graph_fields():
    nodes_fields = [
        {"field_name": "id", "type": "string",
         "links": [
             {
                 "title": "Actions/Start",
                 "url": "http://localhost:5000/api/action?service=${__data.fields.title}&action=start"
             },
             {
                 "title": "Actions/Restart",
                 "url": "http://localhost:5000/api/action?service=${__data.fields.title}&action=restart"
             } ,
             {
                 "title": "Actions/Stop",
                 "url": "http://localhost:5000/api/action?service=${__data.fields.title}&action=stop"
             },
             {
                 "title": "Show Logs",
                 "url": "http://127.0.0.1:5000/api/logs?service=${__data.fields.title}"
             }
          ]
        },
        {"field_name": "title", "type": "string"},
        {"field_name": "mainStat", "type": "string"},
        {"field_name": "detail__role", "type": "string", "displayName": "Role"},
        {"field_name": "detail__uptime", "type": "string", "displayName": "Uptime"},
        {"field_name": "arc__failed", "type": "number", "color": "red", "displayName": "Inactive"},
        {"field_name": "arc__passed", "type": "number", "color": "green", "displayName": "Active"},
        {"field_name": "arc__neither", "type": "number", "color": "yellow", "displayName": "Active (No Dataflow)"},
    ]
    edges_fields = [
        {"field_name": "id", "type": "string"},
        {"field_name": "source", "type": "string"},
        {"field_name": "target", "type": "string"},
        {"field_name": "mainStat", "type": "number"},
        {"field_name": "color", "type": "string"}
    ]
    result = {"nodes_fields": nodes_fields, "edges_fields": edges_fields}
    return jsonify(result)


@app.route('/api/graph/data')
def fetch_graph_data():
    topics_dict = dict()
    with open('/home/preetam/phase1T1/MPVT/topic.yml', 'r') as file:
        topics_dict = yaml.safe_load(file)
    topics_list = topics_dict["kafka"]
    result = {"nodes": list(
        [
            {
                "id": "pcim",
                "title": "PCIM",
                "arc__passed": 1.0,
                "arc__failed": 0.0,
                "arc__neither": 0.0
            },
            {
                "id": "grafana",
                "title": "grafana",
                "arc__passed": 1.0,
                "arc__failed": 0.0,
                "arc__neither": 0.0,
                "links": [
                    {
                        "title": "Actions/Start",
                        "url": "http://localhost:5000/api/action?service=${__data.fields.title}&action=start"
                    },
                    {
                        "title": "Actions/Restart",
                        "url": "http://localhost:5000/api/action?service=${__data.fields.title}&action=restart"
                    },
                    {
                        "title": "Actions/Stop",
                        "url": "http://localhost:5000/api/action?service=${__data.fields.title}&action=stop"
                    },
                    {
                        "title": "Show Logs",
                        "url": "http://127.0.0.1:5000/api/logs?service=${__data.fields.title}"
                    }
                ]
            }
        ]), "edges": list()}
    for topic in topics_list:
        update_statuses(topic)
        mqtt_col = [0.0, 0.0, 0.0]
        kafka_col = [0.0, 0.0, 0.0]
        log_col = [0.0, 0.0, 0.0]
        open_col = [0.0, 0.0, 0.0]

        if kafka_node_color == "green":
            kafka_col[0] = 1.0
        elif kafka_node_color == "red":
            kafka_col[1] = 1.0
        else:
            kafka_col[2] = 1.0

        if mosquitto_node_color == "green":
            mqtt_col[0] = 1.0
        elif mosquitto_node_color == "red":
            mqtt_col[1] = 1.0
        else:
            mqtt_col[2] = 1.0

        if logstash_node_color == "green":
            log_col[0] = 1.0
        elif logstash_node_color == "red":
            log_col[1] = 1.0
        else:
            log_col[2] = 1.0

        if opensearch_node_color == "green":
            open_col[0] = 1.0
        elif opensearch_node_color == "red":
            open_col[1] = 1.0
        else:
            open_col[2] = 1.0

        result["nodes"] += [
            {
                "id": "mqtt",
                "title": "mosquitto",
                "detail__role": "extrct(IOT)",
                "mainStat": mosquitto_status,
                "detail__uptime": mosquitto_uptime,
                "arc__passed": mqtt_col[0],
                "arc__failed": mqtt_col[1],
                "arc__neither": mqtt_col[2],
                "links": [
                    {
                        "title": "Actions/Start",
                        "url": "http://localhost:5000/api/action?service=${__data.fields.title}&action=start"
                    },
                    {
                        "title": "Actions/Restart",
                        "url": "http://localhost:5000/api/action?service=${__data.fields.title}&action=restart"
                    },
                    {
                        "title": "Actions/Stop",
                        "url": "http://localhost:5000/api/action?service=${__data.fields.title}&action=stop"
                    },
                   {
                        "title": "Show Logs",
                        "url": "http://127.0.0.1:5000/api/logs?service=${__data.fields.title}"
                    }
                ]
            },
            {
                "id": "kafka",
                "title": "kafka",
                "detail__role": "Stream",
                "mainStat": kafka_status,
                "detail__uptime": kafka_uptime,
                "arc__passed": kafka_col[0],
                "arc__failed": kafka_col[1],
                "arc__neither": kafka_col[2],
                "links": [
                    {
                        "title": "Actions/Start",
                        "url": "http://localhost:5000/api/action?service=${__data.fields.title}&action=start"
                    },
                    {
                        "title": "Actions/Restart",
                        "url": "http://localhost:5000/api/action?service=${__data.fields.title}&action=restart"
                    },
                    {
                        "title": "Actions/Stop",
                        "url": "http://localhost:5000/api/action?service=${__data.fields.title}&action=stop"
                    },
                   {
                        "title": "Show Logs",
                        "url": "http://127.0.0.1:5000/api/logs?service=${__data.fields.title}"
                    }
                ]
            },
            {
                "id": "logstash",
                "title": "logstash",
                "detail__role": "Data Processing",
                "mainStat": logstash_status,
                "detail__uptime": logstash_uptime,
                "arc__passed": log_col[0],
                "arc__failed": log_col[1],
                "arc__neither": log_col[2],
                "links": [
                    {
                        "title": "Actions/Start",
                        "url": "http://localhost:5000/api/action?service=${__data.fields.title}&action=start"
                    },
                    {
                        "title": "Actions/Restart",
                        "url": "http://localhost:5000/api/action?service=${__data.fields.title}&action=restart"
                    },
                    {
                        "title": "Actions/Stop",
                        "url": "http://localhost:5000/api/action?service=${__data.fields.title}&action=stop"
                    },
                   {
                        "title": "Show Logs",
                        "url": "http://127.0.0.1:5000/api/logs?service=${__data.fields.title}"
                    }
                ]
            },
            {
                "id": "opensearch",
                "title": "opensearch",
                "detail__role": "Database",
                "mainStat": opensearch_status,
                "detail__uptime": opensearch_uptime,
                "arc__passed": open_col[0],
                "arc__failed": open_col[1],
                "arc__neither": open_col[2],
                "links": [
                    {
                        "title": "Actions/Start",
                        "url": "http://localhost:5000/api/action?service=${__data.fields.title}&action=start"
                    },
                    {
                        "title": "Actions/Restart",
                        "url": "http://localhost:5000/api/action?service=${__data.fields.title}&action=restart"
                    },
                    {
                        "title": "Actions/Stop",
                        "url": "http://localhost:5000/api/action?service=${__data.fields.title}&action=stop"
                    },
                    {
                        "title": "Show Logs",
                        "url": "http://127.0.0.1:5000/api/logs?service=${__data.fields.title}"
                    }
                ]
            }
        ]

        result["edges"] += [
            {
                "id": "pcim_to_mqtt",
                "source": "pcim",
                "target": "mqtt",
                "mainStat": 1.0,
                "color": "green"
            },
            {
                "id": "mqtt_to_kafka_",
                "source": "mqtt",
                "target": "kafka",
                "mainStat": mqtt_to_kafka_mainStat,
                "color": mqtt_to_kafka_edge
            },
            {
                "id": "kafka_to_log",
                "source": "kafka",
                "target": "logstash",
                "mainStat": kafka_to_log_mainStat,
                "color": kafka_to_logstash_edge
            },
            {
                "id": "log_to_open_",
                "source": "logstash",
                "target": "opensearch",
                "mainStat": log_to_open_mainStat,
                "color": logstash_to_opensearch_edge
            },
            {
                "id": "open_to_grafana_",
                "source": "opensearch",
                "target": "grafana",
                "mainStat": 1.0,
                "color": "green"
            }
        ]
    return jsonify(result)

COLOR_MAP = {
    "ERROR": "#fc0008",  # Red
    "EXCEPTION": "#fcf000",  # Yellow
    "WARNING": "#fa712d",  # Orange
    "INFO": "#35fc03",  # Green
    "DEBUG": "#03b1fc",  # Blue
    "OTHER": "#aab0b3"  # Gray
}

def is_service_active(service_name):
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.stdout.strip() == "active"
    except Exception as e:
        print(f"Error checking service status for {service_name}: {e}")
        return False

def extract_timestamp(line):
    match = re.search(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}", line)
    return match.group(0) if match else ""

@app.template_filter('datetimeformat')
def datetimeformat(value, format='%d-%m-%y | %I:%M:%S %p'):
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    return value.strftime(format)

def format_log_entry(line):
    lower_line = line.lower()
    if "error" in lower_line:
        log_type = "ERROR"
    elif "exception" in lower_line:
        log_type = "EXCEPTION"
    elif "warn" in lower_line:
        log_type = "WARNING"
    elif "info" in lower_line:
        log_type = "INFO"
    elif "debug" in lower_line:
        log_type = "DEBUG"
    else:
        log_type = "OTHER"

    timestamp = extract_timestamp(line)
    color = COLOR_MAP[log_type]

    html = f"""
    <div class='log-entry' data-type='{log_type}' data-timestamp='{timestamp}'>
        <span style='color:{color}; font-weight:bold;'>[{log_type}]</span>
        <span style='color:{color}; font-family:monospace;'>{Markup.escape(line)}</span>
    </div>
    """
    return {"html": html, "timestamp": timestamp}


def get_recent_logs(component, num_lines=100):
    try:
        result = subprocess.run(
            ["journalctl", "-u", component, "--no-pager", "-n", str(num_lines)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        lines = result.stdout.splitlines()
    except subprocess.CalledProcessError as e:
        return [{
            "html": f"<div class='log-entry' style='color:red;'>Failed to fetch logs: {e.stderr}</div>",
            "timestamp": ""
        }]

    entries = [format_log_entry(line) for line in lines]
    sorted_entries = sorted(entries, key=lambda e: e["timestamp"], reverse=True)
    return sorted_entries



@app.route('/api/action', methods=['GET', 'POST'])
def get_status():
    # Extract action and service from URL parameters
    action = request.args.get("action")
    component = request.args.get("service")

    # Define valid services and actions for security validation
    valid_services = {"kafka", "mosquitto", "logstash", "opensearch", "grafana"}
    valid_actions = {"start", "stop", "restart"}

    # Validate input parameters
    if component not in valid_services or action not in valid_actions:
        response = {
            "status": "error",
            "component": "nil",
            "action": "nil",
            "message": "Invalid action or component",
            "output": "Please choose a valid action and component.",
            "logs": [],
            "color_map": COLOR_MAP,
            "timestamp": datetime.now(pytz.timezone("Asia/Kolkata")).isoformat(),
            "is_running": False
        }
        return render_template("status_result.html", response=response), 400

    # Handle POST request (action execution)
    if request.method == 'POST':
        # Verify admin password
        entered_password = request.form.get("password")
        if entered_password != ADMIN_PASSWORD:
            return render_template(
                "error_generic.html",
                message="Incorrect password.",
                back_url=f"/api/action?service={component}&action={action}"
            )

        # Construct systemctl command for service control
        command = ["sudo", "-n", "systemctl", action, component]

        try:
            # Execute the systemctl command
            result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Get recent logs and current service status
            logs = get_recent_logs(component)
            is_running = is_service_active(component)

            # Prepare success response
            response = {
                "status": "success",
                "component": component,
                "action": action,
                "message": f"{action.capitalize()} command sent to {component}",
                "output": result.stdout,
                "logs": [entry["html"] for entry in logs],
                "color_map": COLOR_MAP,
                "timestamp": datetime.now(pytz.timezone("Asia/Kolkata")).isoformat(),
                "is_running": is_running
            }
            return render_template("status_result.html", response=response)

        except subprocess.CalledProcessError as e:
            # Handle command execution failure
            logs = get_recent_logs(component)
            is_running = is_service_active(component)
            response = {
                "status": "error",
                "component": component,
                "action": action,
                "message": f"Failed to {action} {component}",
                "output": e.stderr,
                "logs": [entry["html"] for entry in logs],
                "color_map": COLOR_MAP,
                "timestamp": datetime.now(pytz.timezone("Asia/Kolkata")).isoformat(),
                "is_running": is_running
            }
            return render_template("status_result.html", response=response), 500

    return render_template("password_prompt.html", action=action, service=component)



@app.route('/api/logs', methods=['GET'])
def show_logs():
    # Extract service name from URL parameter
    service = request.args.get("service")

    # Validate that service parameter is provided
    if not service:
        return render_template("error_generic.html", message="No service specified in query string.", back_url="/")

    # Define log file paths for each supported service
    LOG_PATHS = {
        "kafka": "/home/preetam/kafka/kafka_2.13-3.9.0/logs/server.log",
        "opensearch": "/var/log/opensearch/opensearch.log",
        "grafana": "/var/log/grafana/grafana.log",
        "logstash": "/var/log/logstash/logstash-plain.log", 
        "mosquitto": "/var/log/mosquitto/mosquitto.log"
    }

    # Normalize service name to lowercase for consistent lookup
    service_key = service.lower()

    # Validate service first
    if service_key not in LOG_PATHS:
        return render_template("error_generic.html", message=f"Unknown service: {service}", back_url="/")

    # Get log path based on service type
    if service_key == "kafka":
        # Kafka has multiple log files - find the most recent one
        kafka_logs = glob.glob("/home/preetam/kafka/kafka_2.13-3.9.0/logs/server.log*")
        log_path = max(kafka_logs, key=os.path.getmtime) if kafka_logs else None
    else:
        # Other services have single log files
        log_path = LOG_PATHS.get(service_key)

    # Verify log file exists
    if not log_path or not os.path.exists(log_path):
        return render_template("error_generic.html", message=f"Log file not found for service: {service}", back_url="/")

    # Check if service is currently running
    is_running = is_service_active(service_key)

    try:
        # Read the last 200 lines from the log file
        with open(log_path, 'r') as f:
            lines = f.readlines()[-200:]
    except Exception as e:
        return render_template("error_generic.html", message=f"Error reading log file: {str(e)}", back_url="/")

    # Format log entries with syntax highlighting and reverse order (newest first)
    log_entries = [format_log_entry(line)["html"] for line in reversed(lines)]

    # Render the log viewer template
    return render_template(
        "log_viewer.html",
        service_key=service_key,
        is_running=is_running,
        log_entries=log_entries,
        color_map=COLOR_MAP
    )

@app.route('/api/health')
def check_health():
    return "API is working well!", 200

def update_statuses(topic):
    kafka_metric = kafkaComp()
    mosquitto_metric = mosquittoComp()
    logstash_metric = logstashComp()
    opensearch_metric = opensearchComp()
    data_pipeline = dataflow(topic)
    global kafka_status, mosquitto_status, logstash_status, opensearch_status
    global kafka_uptime, mosquitto_uptime, logstash_uptime, opensearch_uptime
    global kafka_node_color, mosquitto_node_color, logstash_node_color, opensearch_node_color
    global mqtt_to_kafka_edge, kafka_to_logstash_edge, logstash_to_opensearch_edge
    global mqtt_to_kafka_mainStat, kafka_to_log_mainStat, log_to_open_mainStat

    kafka_status = kafka_metric.get_comp_status()
    mosquitto_status = mosquitto_metric.get_comp_status()
    logstash_status = logstash_metric.get_comp_status()
    opensearch_status = opensearch_metric.get_comp_status()

    kafka_uptime = kafka_metric.get_service_uptime()
    mosquitto_uptime = mosquitto_metric.get_service_uptime()
    logstash_uptime = logstash_metric.get_service_uptime()
    opensearch_uptime = opensearch_metric.get_service_uptime()

    kafka_node_color = kafka_metric.node_color
    mosquitto_node_color = mosquitto_metric.node_color
    logstash_node_color = logstash_metric.node_color
    opensearch_node_color = opensearch_metric.node_color

    mqtt_to_kafka_edge = data_pipeline.check_kafka_data()
    kafka_to_logstash_edge = data_pipeline.kafka_logstash_dataflow()
    logstash_to_opensearch_edge = data_pipeline.monitor_index_growth()

    if mqtt_to_kafka_edge == "red" and kafka_node_color == "green":
        kafka_node_color = "yellow"

    if kafka_to_logstash_edge == "red" and logstash_node_color == "green":
        logstash_node_color = "yellow"

    if logstash_to_opensearch_edge == "red" and opensearch_node_color == "green":
        opensearch_node_color = "yellow"

    mqtt_to_kafka_mainStat = 1.0 if mqtt_to_kafka_edge == "green" else 0.0
    kafka_to_log_mainStat = 1.0 if kafka_to_logstash_edge == "green" else 0.0
    log_to_open_mainStat = 1.0 if logstash_to_opensearch_edge == "green" else 0.0


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
