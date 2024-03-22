import time
import requests
from pprint import pprint

def watch_task_status(endpoint, interval=10):
    while True:
        resp = requests.get(endpoint)
        resp = resp.json()
        train_task_id, status = resp['train_task_id'], resp['status']

        if status == "completed":
            print(f"task id: {train_task_id} | status: {status}")
            # Do something with the result 
            print("Training task completed!")
            break

        else:
            print(f"task id: {train_task_id} | status: {status}")
            time.sleep(interval)  # Check status periodically

body = [
    {
        "store_id": "4",
        "product_name": "product_A",
        "begin_date": "2023-03-01T00:00:00Z",
        "end_date": "2023-03-07T00:00:00Z",
    },
    {
        "store_id": "3",
        "product_name": "product_A",
        "begin_date": "2023-03-01T00:00:00Z",
        "end_date": "2023-03-07T00:00:00Z",
    },
    {
        "store_id": "10",
        "product_name": "product_A",
        "begin_date": "2023-03-01T00:00:00Z",
        "end_date": "2023-03-07T00:00:00Z",
    },
]
# direct test
# resp = requests.post("http://localhost:4242/forecast", json=body)
# resp = requests.post("http://localhost:4243/train", json=body)

# reverse proxy test (nginx)
resp = requests.post("http://localhost/api/trainers/train", json=body)
# resp = requests.post("http://localhost/api/trainers/1000/product_A/train", json=body)
# resp = requests.post("http://localhost/api/forecasters/forecast", json=body)
print(resp.raw)
resp_json = resp.json()
pprint(resp_json, indent=4)
time.sleep(5) # delay a bit

print('Watching training task status...')
watch_task_status(f"http://localhost/api/trainers/training_task_status/{resp_json['train_task_id']}")

# watch_task_status(f"http://localhost/api/trainers/training_task_status/train_1711118459.4240654")
