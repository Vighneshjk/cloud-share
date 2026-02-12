import requests

try:
    r = requests.get('http://127.0.0.1:8000/files/', timeout=5)
    print(f"Status: {r.status_code}")
    print(f"URL: {r.url}")
except Exception as e:
    print(f"Error: {e}")
