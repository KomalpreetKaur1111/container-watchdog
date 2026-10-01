import subprocess
import time
import json
from datetime import datetime

CHECK_INTERVAL = 5
STATUS_FILE = "status.json"

container_state = {}

def get_watched_containers():
    result = subprocess.run(
        ["docker", "ps", "-a", "--filter", "label=watch=true", "--format", "{{.Names}}"],
        capture_output=True,
        text=True
    )
    names = [name.strip() for name in result.stdout.strip().split("\n") if name.strip()]
    return names

def is_container_running(name):
    result = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", name],
        capture_output=True,
        text=True
    )
    return result.stdout.strip() == "true"

def restart_container(name):
    subprocess.run(["docker", "start", name])
    container_state[name]["restart_count"] += 1

def get_container_stats(name):
    result = subprocess.run(
        ["docker", "stats", "--no-stream", "--format", "{{.CPUPerc}}|{{.MemUsage}}", name],
        capture_output=True,
        text=True
    )
    output = result.stdout.strip()
    if "|" in output:
        cpu, mem = output.split("|")
        return cpu.strip(), mem.strip()
    return "N/A", "N/A"

def log(name, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{name}] {message}")

def check_container(name):
    if name not in container_state:
        container_state[name] = {"log_history": [], "restart_count": 0}

    if is_container_running(name):
        cpu, mem = get_container_stats(name)
        msg = "Container is healthy."
        log(name, f"{msg} CPU: {cpu}, Mem: {mem}")
        container_state[name]["healthy"] = True
        container_state[name]["cpu"] = cpu
        container_state[name]["mem"] = mem
    else:
        msg = "Container is DOWN! Restarting..."
        log(name, msg)
        restart_container(name)
        container_state[name]["healthy"] = False
        container_state[name]["cpu"] = "N/A"
        container_state[name]["mem"] = "N/A"

    container_state[name]["log_history"].append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "message": msg
    })
    if len(container_state[name]["log_history"]) > 10:
        container_state[name]["log_history"].pop(0)

def write_status(active_names):
    data = {}
    for name in active_names:
        c = container_state[name]
        data[name] = {
            "healthy": c.get("healthy", False),
            "logs": c["log_history"],
            "restart_count": c["restart_count"],
            "cpu": c.get("cpu", "N/A"),
            "mem": c.get("mem", "N/A"),
        }
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f)

def main():
    log("SYSTEM", "Watchdog started. Auto-discovering containers labeled watch=true...")
    while True:
        active_names = get_watched_containers()
        if not active_names:
            log("SYSTEM", "No labeled containers found. Waiting...")
        for name in active_names:
            check_container(name)
        write_status(active_names)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()