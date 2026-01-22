import json, time, uuid


def write_audit_log(data: dict):
    entry = {"id": str(uuid.uuid4()), "timestamp": time.time(), **data}
    with open("audit.log", "a") as f:
        f.write(json.dumps(entry) + "\n")
