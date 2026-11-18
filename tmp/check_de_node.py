import json, subprocess

jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1dWlkIjoiZmQwMzVjYzMtNzE1ZC00M2ZlLWI5N2MtOTBlN2JkMjIzMTY0IiwidXNlcm5hbWUiOm51bGwsInJvbGUiOiJBUEkiLCJpYXQiOjE3OTMwNzczMDgsImV4cCI6MjEwODQzNzMwOH0.VnEHdnUjXranuPmYP7BpVuuo998ABfa1aMgddObt5Vo"
headers = ["-H", f"Authorization: Bearer {jwt}", "-H", "Content-Type: application/json"]
base_url = "http://127.0.0.1:3443"

result = subprocess.run(["curl", "-s"] + headers + [f"{base_url}/api/nodes/b4393e6a-7369-4b93-8dd9-4c5381554544"], capture_output=True, text=True)
data = json.loads(result.stdout)
profile = data["response"].get("configProfile", {})
print(f"activeConfigProfileUuid: {profile.get('activeConfigProfileUuid')}")
for inbound in profile.get("activeInbounds", []):
    print(f"  inbound: uuid={inbound.get('uuid')} tag={inbound.get('tag')} profileUuid={inbound.get('profileUuid')}")