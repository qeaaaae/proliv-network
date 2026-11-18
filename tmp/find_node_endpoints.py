import json, subprocess

jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1dWlkIjoiZmQwMzVjYzMtNzE1ZC00M2ZlLWI5N2MtOTBlN2JkMjIzMTY0IiwidXNlcm5hbWUiOm51bGwsInJvbGUiOiJBUEkiLCJpYXQiOjE3OTMwNzczMDgsImV4cCI6MjEwODQzNzMwOH0.VnEHdnUjXranuPmYP7BpVuuo998ABfa1aMgddObt5Vo"
headers = ["-H", f"Authorization: Bearer {jwt}", "-H", "Content-Type: application/json"]
base_url = "http://127.0.0.1:3443"

result = subprocess.run(["curl", "-s"] + headers + [f"{base_url}/api/openapi.json"], capture_output=True, text=True)
if result.stdout:
    try:
        data = json.loads(result.stdout)
        for path, methods in data.get("paths", {}).items():
            if "node" in path.lower():
                for method, details in methods.items():
                    print(f"{method.upper()} {path}")
    except:
        print("Failed to parse openapi.json")
else:
    print("No openapi.json endpoint")