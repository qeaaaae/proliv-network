import json, subprocess

jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1dWlkIjoiZmQwMzVjYzMtNzE1ZC00M2ZlLWI5N2MtOTBlN2JkMjIzMTY0IiwidXNlcm5hbWUiOm51bGwsInJvbGUiOiJBUEkiLCJpYXQiOjE3OTMwNzczMDgsImV4cCI6MjEwODQzNzMwOH0.VnEHdnUjXranuPmYP7BpVuuo998ABfa1aMgddObt5Vo"
headers = ["-H", f"Authorization: Bearer {jwt}", "-H", "Content-Type: application/json"]
base_url = "http://127.0.0.1:3443"

result = subprocess.run(["curl", "-s"] + headers + [f"{base_url}/api/nodes/3efb985b-a7a5-4775-9d96-0f652fbd5287"], capture_output=True, text=True)
data = json.loads(result.stdout)
node = data["response"]
for k, v in node.items():
    if k not in ["system", "stats"]:
        print(f"{k}: {type(v).__name__} = {v if not isinstance(v, (dict, list)) else '...'}")