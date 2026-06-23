
import websocket
import requests
import re
import time
import json

USERNAME = "liudapao"
PASSWORD = "asdke0735"
BASE_URL = "https://www.pythonanywhere.com"

# Login
session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})
r = session.get(BASE_URL + "/login/?next=/")
csrf = re.search(r'Anywhere\.csrfToken\s*=\s*"([^"]+)"', r.text).group(1)
session.post(BASE_URL + "/login/", data={
    "csrfmiddlewaretoken": csrf, "auth-username": USERNAME,
    "auth-password": PASSWORD, "login_view-current_step": "auth"
}, headers={"Referer": BASE_URL + "/login/?next=/"})
session.headers["X-CSRFToken"] = session.cookies.get("csrftoken", "")
session.headers["Referer"] = BASE_URL + "/"

# List existing consoles
console_api = BASE_URL + "/api/v0/user/" + USERNAME + "/consoles/"
resp = session.get(console_api)
consoles = resp.json()
print("Consoles found: " + str(len(consoles)))

# Pick the first one or create new
if len(consoles) > 0:
    console_id = consoles[0]["id"]
else:
    resp = session.post(console_api, json={"executable": "bash", "arguments": ""},
                       headers={"Content-Type": "application/json"})
    console_id = resp.json()["id"]

print("Using console: " + str(console_id))

# Get WebSocket key from console page
r = session.get(BASE_URL + "/user/" + USERNAME + "/consoles/" + str(console_id) + "/")
m = re.search(r'LoadConsole\("([^"]+)",\s*"([^"]+)",\s*"([^"]+)"', r.text)
ws_host = m.group(1)
ws_key = m.group(2)
print("WS host: " + ws_host)

# Connect WebSocket
ws_url = "wss://" + ws_host + "/?key=" + ws_key
print("Connecting to: " + ws_url)

ws = websocket.create_connection(
    ws_url,
    cookie="; ".join([f"{k}={v}" for k, v in session.cookies.get_dict().items()]),
    sslopt={"cert_reqs": ssl.CERT_NONE},
    timeout=30
)
print("WebSocket connected!")

# Send commands to set up
commands = [
    "cd /home/liudapao/liudaopao\n",
    "source venv/bin/activate\n",
    "pip install flask gunicorn 2>&1\n",
    "echo FLASK_INSTALL_DONE\n",
]

for cmd in commands:
    print("\nSending: " + cmd.strip()[:50])
    ws.send(cmd)
    time.sleep(8)  # Wait for pip to install
    
    # Try to read all available output
    ws.settimeout(5)
    all_output = ""
    try:
        while True:
            msg = ws.recv()
            if msg:
                all_output += msg
    except:
        pass
    
    if all_output:
        print("Output: " + all_output[-500:])
    else:
        print("(no output received)")

ws.close()
print("\nWebSocket closed")
print("\nNow trying to access the site...")

# Try to access the site
resp = requests.get("https://liudapao.pythonanywhere.com/", timeout=10)
print("Site status: " + str(resp.status_code))
if resp.status_code == 200:
    print("Site is UP!")
    print(resp.text[:300])
