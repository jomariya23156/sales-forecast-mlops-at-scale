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

resp = requests.post("http://localhost:4242/forecast", json=body)
# resp = requests.post("http://localhost:4243/train", json=body)
pprint(resp.json(), indent=4)
