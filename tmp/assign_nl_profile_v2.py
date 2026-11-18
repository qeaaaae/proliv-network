import json, subprocess, tempfile

jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1dWlkIjoiZmQwMzVjYzMtNzE1ZC00M2ZlLWI5N2MtOTBlN2JkMjIzMTY0IiwidXNlcm5hbWUiOm51bGwsInJvbGUiOiJBUEkiLCJpYXQiOjE3OTMwNzczMDgsImV4cCI6MjEwODQzNzMwOH0.VnEHdnUjXranuPmYP7BpVuuo998ABfa1aMgddObt5Vo"
headers = ["-H", f"Authorization: Bearer {jwt}", "-H", "Content-Type: application/json"]
base_url = "http://127.0.0.1:3443"

node_uuid = "3efb985b-a7a5-4775-9d96-0f652fbd5287"
profile_uuid = "4a270698-eed5-492e-a6a4-11ed84bbc6a7"

# Try PATCH to /api/nodes/{uuid}
patch_data = {
    "uuid": node_uuid,
    "activeConfigProfileUuid": profile_uuid,
    "activeInbounds": [
        "VLESS-TCP-Reality-NL",
        "VLESS-WS-CDN-NL",
        "VLESS-XHTTP-CDN-NL"
    ]
}

with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
    json.dump(patch_data, f)
    patch_file = f.name

result = subprocess.run([
    "curl", "-s", "-X", "PATCH"] + headers + [
    "-d", f"@{patch_file}",
    f"{base_url}/api/nodes/{node_uuid}"
], capture_output=True, text=True)

print(f"Node assign result: {result.stdout[:2000]}")
if result.stderr:
    print(f"Stderr: {result.stderr}")

# Verify
import time
time.sleep(2)
verify = subprocess.run(["curl", "-s"] + headers + [f"{base_url}/api/nodes/{node_uuid}"], capture_output=True, text=True)
vdata = json.loads(verify.stdout)
print(f"Verify activeConfigProfileUuid: {vdata.get('response', {}).get('configProfile', {}).get('activeConfigProfileUuid')}")