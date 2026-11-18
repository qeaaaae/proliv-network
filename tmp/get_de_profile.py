import json, subprocess

jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1dWlkIjoiZmQwMzVjYzMtNzE1ZC00M2ZlLWI5N2MtOTBlN2JkMjIzMTY0IiwidXNlcm5hbWUiOm51bGwsInJvbGUiOiJBUEkiLCJpYXQiOjE3OTMwNzczMDgsImV4cCI6MjEwODQzNzMwOH0.VnEHdnUjXranuPmYP7BpVuuo998ABfa1aMgddObt5Vo"
headers = ["-H", f"Authorization: Bearer {jwt}"]
base_url = "http://127.0.0.1:3443"

result = subprocess.run(["curl", "-s"] + headers + [f"{base_url}/api/config-profiles/451b8d6a-218c-4fc3-a1cf-04ca940e6548"], capture_output=True, text=True)
data = json.loads(result.stdout)
p = data["response"]
print(f'Profile: {p["name"]}')
for rule in p["config"]["routing"]["rules"]:
    if rule.get("type") == "field" and "domain" in rule:
        print(f'  {json.dumps(rule, ensure_ascii=False)}')