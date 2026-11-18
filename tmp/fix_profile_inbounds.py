import json, subprocess, tempfile, uuid

jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1dWlkIjoiZmQwMzVjYzMtNzE1ZC00M2ZlLWI5N2MtOTBlN2JkMjIzMTY0IiwidXNlcm5hbWUiOm51bGwsInJvbGUiOiJBUEkiLCJpYXQiOjE3OTMwNzczMDgsImV4cCI6MjEwODQzNzMwOH0.VnEHdnUjXranuPmYP7BpVuuo998ABfa1aMgddObt5Vo"
headers = ["-H", f"Authorization: Bearer {jwt}", "-H", "Content-Type: application/json"]
base_url = "http://127.0.0.1:3443"

# Get NL-Profile-v2
result = subprocess.run(["curl", "-s"] + headers + [f"{base_url}/api/config-profiles/58c03fa0-3724-47ea-a045-47cf139b7f80"], capture_output=True, text=True)
data = json.loads(result.stdout)
profile = data["response"]

# Add UUIDs to inbounds
for inbound in profile["config"]["inbounds"]:
    inbound["uuid"] = str(uuid.uuid4())
    print(f'Added UUID {inbound["uuid"]} to {inbound["tag"]}')

with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
    json.dump(profile, f)
    profile_file = f.name

result = subprocess.run([
    "curl", "-s", "-X", "PATCH"] + headers + [
    "-d", f"@{profile_file}",
    f"{base_url}/api/config-profiles/58c03fa0-3724-47ea-a045-47cf139b7f80"
], capture_output=True, text=True)

print(f"Update result: {result.stdout[:2000]}")
if result.stderr:
    print(f"Stderr: {result.stderr}")

# Verify
import time
time.sleep(1)
verify = subprocess.run(["curl", "-s"] + headers + [f"{base_url}/api/config-profiles/58c03fa0-3724-47ea-a045-47cf139b7f80"], capture_output=True, text=True)
vdata = json.loads(verify.stdout)
for ib in vdata["response"]["config"]["inbounds"]:
    print(f'{ib.get("uuid", "NO UUID")} {ib["tag"]}')