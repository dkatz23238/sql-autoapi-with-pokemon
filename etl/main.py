import requests
import pandas as pd

ENDPOINT = "http://webapp:8000"

r = requests.get("https://bulbapedia.bulbagarden.net/wiki/List_of_moves")
dfs = pd.read_html(r.content)

moves = dfs[1]
columns = moves.iloc[1,:]
moves = moves.iloc[2:,:]
moves.columns=list(columns)
moves.set_index("#", drop=True)

for name in moves.Name:
    try:
        payload = {"name":name, "type_id":2, "damage":100}
        r = requests.post(ENDPOINT + "/move", json=payload)
        print(r.status_code)
        print(r.content)
    except Exception as e:
        print(e)