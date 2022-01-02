import requests
import json

def load_seed():
    with open("./seed/api_tables.seed.json") as f:
        data = json.loads(f.read())

    return data

seed_data = load_seed()

for endpoint, data_list in seed_data:
    for payload in data_list:
        r = requests.post(f"http://localhost:8000/{endpoint}", json=payload)
        print(r)
        print(r.content)
