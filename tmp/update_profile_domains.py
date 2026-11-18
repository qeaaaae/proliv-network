import json, subprocess, tempfile

jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1dWlkIjoiZmQwMzVjYzMtNzE1ZC00M2ZlLWI5N2MtOTBlN2JkMjIzMTY0IiwidXNlcm5hbWUiOm51bGwsInJvbGUiOiJBUEkiLCJpYXQiOjE3OTMwNzczMDgsImV4cCI6MjEwODQzNzMwOH0.VnEHdnUjXranuPmYP7BpVuuo998ABfa1aMgddObt5Vo"
headers = ["-H", f"Authorization: Bearer {jwt}", "-H", "Content-Type: application/json"]
base_url = "http://127.0.0.1:3443"

# Get current profile
result = subprocess.run(["curl", "-s"] + headers + [f"{base_url}/api/config-profiles/58c03fa0-3724-47ea-a045-47cf139b7f80"], capture_output=True, text=True)
data = json.loads(result.stdout)
profile = data["response"]

# Replace geosite:category-ai-chat with explicit domains
ai_domains = [
    "generativelanguage.googleapis.com",
    "gemini.google.com",
    "openrouter.ai",
    "api.individual.githubcopilot.com",
    "claude.ai",
    "x.ai",
    "perplexity.ai",
    "mistral.ai",
    "api.openai.com",
    "api.anthropic.com"
]

for rule in profile["config"]["routing"]["rules"]:
    if rule.get("type") == "field":
        domains = rule.get("domain", [])
        new_domains = []
        for d in domains:
            if d == "geosite:category-ai-chat":
                new_domains.extend(ai_domains)
            else:
                new_domains.append(d)
        rule["domain"] = new_domains

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