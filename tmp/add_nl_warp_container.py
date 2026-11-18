import json, subprocess, uuid, tempfile

jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1dWlkIjoiZmQwMzVjYzMtNzE1ZC00M2ZlLWI5N2MtOTBlN2JkMjIzMTY0IiwidXNlcm5hbWUiOm51bGwsInJvbGUiOiJBUEkiLCJpYXQiOjE3OTMwNzczMDgsImV4cCI6MjEwODQzNzMwOH0.VnEHdnUjXranuPmYP7BpVuuo998ABfa1aMgddObt5Vo"

result = subprocess.run([
    "curl", "-s",
    "-H", "X-Forwarded-Proto: https",
    "-H", "X-Forwarded-For: 127.0.0.1",
    "-H", f"Authorization: Bearer {jwt}",
    "http://localhost:3000/api/config-profiles"
], capture_output=True, text=True)

data = json.loads(result.stdout)

default_profile = None
for p in data.get("response", {}).get("configProfiles", []):
    if p.get("uuid") == "00000000-0000-0000-0000-000000000000":
        default_profile = p
        break

if not default_profile:
    print("Default-Profile not found")
    exit(1)

print(f"Found Default-Profile: {default_profile.get('name')}")

nl_profile = default_profile.copy()
nl_profile["uuid"] = str(uuid.uuid4())
nl_profile["name"] = "NL-Profile"
nl_profile["description"] = "NL with WARP for AI"

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

existing_tags = [o.get("tag") for o in nl_profile.get("config", {}).get("outbounds", [])]
if "ai-via-warp" not in existing_tags:
    nl_profile.setdefault("config", {}).setdefault("outbounds", []).append(ai_outbound)
    print("Added ai-via-warp outbound")

routing = nl_profile.setdefault("config", {}).setdefault("routing", {})
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
print("Added routing rule for Gemini API -> ai-via-warp")

with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
    json.dump(nl_profile, f)
    profile_file = f.name

create_result = subprocess.run([
    "curl", "-s", "-X", "POST",
    "-H", "X-Forwarded-Proto: https",
    "-H", "X-Forwarded-For: 127.0.0.1",
    "-H", f"Authorization: Bearer {jwt}",
    "-H", "Content-Type: application/json",
    "-d", f"@{profile_file}",
    "http://localhost:3000/api/config-profiles"
], capture_output=True, text=True)

print(f"Create result: {create_result.stdout[:1000]}")
if create_result.stderr:
    print(f"Stderr: {create_result.stderr}")