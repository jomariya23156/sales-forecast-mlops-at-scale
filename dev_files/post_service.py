import time
import requests
from pprint import pprint


def wait_until_status(
    endpoint, status_to_wait_for, poll_interval=5, timeout_seconds=30
):
    start = time.time()
    while time.time() - start <= timeout_seconds:
        resp = requests.get(endpoint)
        resp = resp.json()
        train_job_id, status = resp["train_job_id"], resp["status"]
        print(f"status: {status}")
        if str(status) in status_to_wait_for:
            break
        time.sleep(poll_interval)


body = [
    {
        "store_id": "1000",
        "product_name": "product_A",
        "begin_date": "2023-03-01T00:00:00Z",
        "end_date": "2023-03-07T00:00:00Z",
    },
]
# direct test
# resp = requests.post("http://localhost:4242/forecast", json=body)
# resp = requests.post("http://localhost:4243/train", json=body)

# reverse proxy test (nginx)
# resp = requests.post("http://localhost/api/trainers/train")
resp = requests.post("http://localhost/api/trainers/1000/product_A/train")
# resp = requests.post("http://localhost/api/forecasters/forecast", json=body)
# resp = requests.get("http://localhost/")
print("status_code:", resp.status_code)
print(resp.raw)
resp_json = resp.json()
pprint(resp_json, indent=4)

# print("Watching training task status...")
# status_to_wait_for = {"SUCCEEDED", "STOPPED", "FAILED"}
# wait_until_status(
#     endpoint=f"http://localhost/api/trainers/training_job_status/{resp_json['train_job_id']}",
#     status_to_wait_for=status_to_wait_for,
#     poll_interval=5,
#     timeout_seconds=60 * 30,  # 30 mins
# )
