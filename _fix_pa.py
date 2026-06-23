import requests, re, os, time, json

USERNAME = "liudapao"
PASSWORD = "asdke0735"
BASE_URL = "https://www.pythonanywhere.com"

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

# Login
resp = session.get(BASE_URL + "/login/?next=/")
csrf = re.search(r"Anywhere\.csrfToken\s*=\s*\"([^\"]+)\"", resp.text).group(1)
session.post(BASE_URL + "/login/", data={
    "csrfmiddlewaretoken": csrf,
    "auth-username": USERNAME,
    "auth-password": PASSWORD,
    "login_view-current_step": "auth"
}, headers={"Referer": BASE_URL + "/login/?next=/"})

session.headers["X-CSRFToken"] = session.cookies.get("csrftoken", "")
session.headers["Referer"] = BASE_URL + "/"

files_api = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path"

# Read existing console output
console_api = f"{BASE_URL}/api/v0/user/{USERNAME}/consoles/"
resp = session.get(console_api + "47240816/")
print(f"Console read: {resp.status_code}")
if resp.status_code == 200:
    console_data = resp.json()
    print(f"Console info: {json.dumps(console_data, indent=2)[:500]}")
else:
    print(f"Response: {resp.text[:200]}")
    
# Try sending command via the web URL instead
console_id = 47240816
send_url = f"{BASE_URL}/user/{USERNAME}/consoles/{console_id}/send/"
print(f"\nSend URL: {send_url}")

# Get CSRF from the console page
resp = session.get(f"{BASE_URL}/user/{USERNAME}/consoles/{console_id}/")
page_csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', resp.text)
if page_csrf:
    session.headers["X-CSRFToken"] = page_csrf.group(1)

# Try sending command
resp = session.post(send_url, data={"input": "echo HELLO\n"}, 
                   headers={"Referer": f"{BASE_URL}/user/{USERNAME}/consoles/{console_id}/"})
print(f"Send command: {resp.status_code} - {resp.text[:200]}")

# Try uploading file via POST
print("\n=== Upload wsgi.py via POST ===")
wsgi_content = b"""import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "liudaopao"))
from app import app as application
"""
resp = session.post(
    files_api + "/home/liudapao/liudaopao/wsgi.py",
    data=wsgi_content,
    headers={"Content-Type": "application/octet-stream", "Referer": BASE_URL + "/"}
)
print(f"POST file: {resp.status_code}")
if resp.status_code != 200:
    resp = session.post(
        files_api + "/home/liudapao/wsgi.py",
        data=wsgi_content,
        headers={"Content-Type": "application/octet-stream"}
    )
    print(f"POST root wsgi: {resp.status_code} - {resp.text[:200]}")
