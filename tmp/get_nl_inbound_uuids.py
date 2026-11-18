import json, subprocess

jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1dWlkIjoiZmQwMzVjYzMtNzE1ZC00M2ZlLWI5N2MtOTBlN2JkMjIzMTY0IiwidXNlcm5hbWUiOm51bGwsInJvbGUiOiJBUEkiLCJpYXQiOjE3OTMwNzczMDgsImV4cCI6MjEwODQzNzMwOH0.VnEHdnUjXranuPmYP7BpVuuo998ABfa1aMgddObt5Vo"
headers = ["-H", f"Authorization: Bearer {jwt}", "-H", "Content-Type: application/json"]
base_url = "http://127.0.0.1:3443"

result = subprocess.run(["curl", "-s"] + headers + [f"{base_url}/api/config-profiles/4a270698-eed5-492e-a6a4-11ed84bbc6a7"], capture_output=True, text=True)
data = json.loads(result.stdout)
for ib in data["response"]["config"]["inbounds"]:
    print(json.dumps(ib, indent=2, ensure_ascii=False))