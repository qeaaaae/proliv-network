import json, subprocess, tempfile

jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1dWlkIjoiZmQwMzVjYzMtNzE1ZC00M2ZlLWI5N2MtOTBlN2JkMjIzMTY0IiwidXNlcm5hbWUiOm51bGwsInJvbGUiOiJBUEkiLCJpYXQiOjE3OTMwNzczMDgsImV4cCI6MjEwODQzNzMwOH0.VnEHdnUjXranuPmYP7BpVuuo998ABfa1aMgddObt5Vo"
headers = ["-H", f"Authorization: Bearer {jwt}", "-H", "Content-Type: application/json"]
base_url = "http://127.0.0.1:3443"

# Get Default-Profile
result = subprocess.run(["curl", "-s"] + headers + [f"{base_url}/api/config-profiles/00000000-0000-0000-0000-000000000000"], capture_output=True, text=True)
data = json.loads(result.stdout)
default_profile = data["response"]

# Create new profile with minimal changes - let API generate inbound UUIDs
new_profile = {
    "name": "NL-Profile-v2",
    "description": "NL with WARP for AI",
    "config": default_profile["config"]
}

# Modify inbound tags to be unique
for inbound in new_profile["config"]["inbounds"]:
    inbound["tag"] = inbound["tag"] + "-NL-v2"

# Add ai-via-warp outbound
ai_outbound = {
    "tag": "ai-via-warp",
    "protocol": "socks",
    "settings": {
        "servers": [{
            "address": "127.0.0.1",
            "port": 40001
        }]
    }
}
new_profile["config"].setdefault("outbounds", []).append(ai_outbound)

# Add routing rule for Gemini
routing = new_profile["config"].setdefault("routing", {})
rules = routing.setdefault("rules", [])

gemini_rule = {
    "type": "field",
    "domain": ["geosite:category-ai-chat", "generativelanguage.googleapis.com", "gemini.google.com"],
    "outboundTag": "ai-via-warp"
}

new_rules = []
inserted = False
for rule in rules:
    if not inserted and rule.get("type") == "field":
        domains = rule.get("domain", [])
        if any("google" in str(d).lower() for d in domains) and "youtube" not in str(domains).lower():
            new_rules.append(gemini_rule)
            inserted = True
    new_rules.append(rule)

if not inserted:
    new_rules.append(gemini_rule)

routing["rules"] = new_rules

with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
    json.dump(new_profile, f)
    profile_file = f.name

result = subprocess.run([
    "curl", "-s", "-X", "POST"] + headers + [
    "-d", f"@{profile_file}",
    f"{base_url}/api/config-profiles"
], capture_output=True, text=True)

print(f"Create result: {result.stdout[:3000]}")
if result.stderr:
    print(f"Stderr: {result.stderr}")