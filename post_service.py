import requests
from pprint import pprint

body = [
    {
        "store_id": "4",
        "begin_date": "2023-03-01T00:00:00Z",
        "end_date": "2023-03-07T00:00:00Z",
    },
    {
        "store_id": "3",
        "begin_date": "2023-03-01T00:00:00Z",
        "end_date": "2023-03-07T00:00:00Z",
    },
    {
        "store_id": "10",
        "begin_date": "2023-03-01T00:00:00Z",
        "end_date": "2023-03-07T00:00:00Z",
    },
]
# direct test
# resp = requests.post("http://localhost:4242/forecast", json=body)
# resp = requests.post("http://localhost:4243/train", json=body)

# reverse proxy test (nginx)
# resp = requests.post("http://localhost/api/trainers/train", json=body)
resp = requests.post("http://localhost/api/forecasters/forecast", json=body)
print(resp.raw)
pprint(resp.json(), indent=4)
