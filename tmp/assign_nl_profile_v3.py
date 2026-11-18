import json, subprocess, tempfile, time

jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1dWlkIjoiZmQwMzVjYzMtNzE1ZC00M2ZlLWI5N2MtOTBlN2JkMjIzMTY0IiwidXNlcm5hbWUiOm51bGwsInJvbGUiOiJBUEkiLCJpYXQiOjE3OTMwNzczMDgsImV4cCI6MjEwODQzNzMwOH0.VnEHdnUjXranuPmYP7BpVuuo998ABfa1aMgddObt5Vo"
headers = ["-H", f"Authorization: Bearer {jwt}", "-H", "Content-Type: application/json"]
base_url = "http://127.0.0.1:3443"

node_uuid = "3efb985b-a7a5-4775-9d96-0f652fbd5287"
profile_uuid = "4a270698-eed5-492e-a6a4-11ed84bbc6a7"

# Get current node config to preserve other fields
result = subprocess.run(["curl", "-s"] + headers + [f"{base_url}/api/nodes/{node_uuid}"], capture_output=True, text=True)
node_data = json.loads(result.stdout)
node = node_data["response"]

# Update only the profile assignment
node["activeConfigProfileUuid"] = profile_uuid
# Don't specify activeInbounds - let the system generate them

with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
    json.dump(node, f)
    patch_file = f.name

result = subprocess.run([
    "curl", "-s", "-X", "PATCH"] + headers + [
    "-d", f"@{patch_file}",
    f"{base_url}/api/nodes"
], capture_output=True, text=True)

print(f"Node assign result: {result.stdout[:2000]}")
if result.stderr:
    print(f"Stderr: {result.stderr}")

time.sleep(3)

# Verify
verify = subprocess.run(["curl", "-s"] + headers + [f"{base_url}/api/nodes/{node_uuid}"], capture_output=True, text=True)
vdata = json.loads(verify.stdout)
profile_info = vdata["response"].get("configProfile", {})
print(f"activeConfigProfileUuid: {profile_info.get('activeConfigProfileUuid')}")
for inbound in profile_info.get("activeInbounds", []):
    print(f"  inbound: uuid={inbound.get('uuid')} tag={inbound.get('tag')}")