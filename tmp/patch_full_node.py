import json, subprocess, tempfile

jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1dWlkIjoiZmQwMzVjYzMtNzE1ZC00M2ZlLWI5N2MtOTBlN2JkMjIzMTY0IiwidXNlcm5hbWUiOm51bGwsInJvbGUiOiJBUEkiLCJpYXQiOjE3OTMwNzczMDgsImV4cCI6MjEwODQzNzMwOH0.VnEHdnUjXranuPmYP7BpVuuo998ABfa1aMgddObt5Vo"
headers = ["-H", f"Authorization: Bearer {jwt}", "-H", "Content-Type: application/json"]
base_url = "http://127.0.0.1:3443"

# Get full node object
result = subprocess.run(["curl", "-s"] + headers + [f"{base_url}/api/nodes/3efb985b-a7a5-4775-9d96-0f652fbd5287"], capture_output=True, text=True)
node_data = json.loads(result.stdout)
node = node_data["response"]

# Update the profile assignment
node["configProfileUuid"] = "4a270698-eed5-492e-a6a4-11ed84bbc6a7"
# Also try activeConfigProfileUuid at top level
node["activeConfigProfileUuid"] = "4a270698-eed5-492e-a6a4-11ed84bbc6a7"

# Remove read-only fields
readonly_fields = ["createdAt", "updatedAt", "configProfile", "id", "ips", "integrationUuids", "lastStatusChange", "lastStatusMessage", "trafficUsedBytes", "xrayUptime", "usersOnline", "system", "versions", "provider", "providerUuid", "activePluginUuid"]
for field in readonly_fields:
    node.pop(field, None)

with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
    json.dump(node, f)
    patch_file = f.name

result = subprocess.run([
    "curl", "-s", "-X", "PATCH"] + headers + [
    "-d", f"@{patch_file}",
    f"{base_url}/api/nodes"
], capture_output=True, text=True)

print(f"PATCH result: {result.stdout[:2000]}")
if result.stderr:
    print(f"Stderr: {result.stderr}")

# Verify
import time
time.sleep(2)
verify = subprocess.run(["curl", "-s"] + headers + [f"{base_url}/api/nodes/3efb985b-a7a5-4775-9d96-0f652fbd5287"], capture_output=True, text=True)
vdata = json.loads(verify.stdout)
profile_info = vdata["response"].get("configProfile", {})
print(f"activeConfigProfileUuid: {profile_info.get('activeConfigProfileUuid')}")
for inbound in profile_info.get("activeInbounds", []):
    print(f"  inbound: uuid={inbound.get('uuid')} tag={inbound.get('tag')}")