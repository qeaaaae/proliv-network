import json, subprocess, tempfile

jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1dWlkIjoiZmQwMzVjYzMtNzE1ZC00M2ZlLWI5N2MtOTBlN2JkMjIzMTY0IiwidXNlcm5hbWUiOm51bGwsInJvbGUiOiJBUEkiLCJpYXQiOjE3OTMwNzczMDgsImV4cCI6MjEwODQzNzMwOH0.VnEHdnUjXranuPmYP7BpVuuo998ABfa1aMgddObt5Vo"
headers = ["-H", f"Authorization: Bearer {jwt}", "-H", "Content-Type: application/json"]
base_url = "http://127.0.0.1:3443"

# Get full node object
result = subprocess.run(["curl", "-s"] + headers + [f"{base_url}/api/nodes/3efb985b-a7a5-4775-9d96-0f652fbd5287"], capture_output=True, text=True)
node = json.loads(result.stdout)["response"]

# Update profile
node["configProfileUuid"] = "58c03fa0-3724-47ea-a045-47cf139b7f80"

# Remove read-only
for f in ["createdAt","updatedAt","configProfile","id","ips","integrationUuids","lastStatusChange","lastStatusMessage","trafficUsedBytes","xrayUptime","usersOnline","system","versions","provider","providerUuid","activePluginUuid"]:
    node.pop(f, None)

with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
    json.dump(node, f)
    patch_file = f.name

result = subprocess.run(["curl", "-s", "-X", "PATCH"] + headers + ["-d", f"@{patch_file}", f"{base_url}/api/nodes"], capture_output=True, text=True)
print(f"Result: {result.stdout[:2000]}")
if result.stderr:
    print(f"Stderr: {result.stderr}")

import time
time.sleep(2)
verify = subprocess.run(["curl", "-s"] + headers + [f"{base_url}/api/nodes/3efb985b-a7a5-4775-9d96-0f652fbd5287"], capture_output=True, text=True)
vdata = json.loads(verify.stdout)
print(f"Profile: {vdata['response'].get('configProfile',{}).get('activeConfigProfileUuid')}")