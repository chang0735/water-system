import requests, re, os, time, json

USERNAME = "liudapao"
PASSWORD = "asdke0735"
BASE_URL = "https://www.pythonanywhere.com"
FILES_DIR = r"C:\Users\Administrator\Desktop\刘大泡送水管理系统"

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

# Use session CSRF token
session.headers["X-CSRFToken"] = session.cookies.get("csrftoken", "")
session.headers["Referer"] = BASE_URL + "/"

files_api = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path"

# First, upload wsgi.py with proper content targeting liudaopao subdirectory
print("=== Uploading updated wsgi.py ===")
wsgi_content = r'''import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "liudaopao"))
from app import app as application
'''
resp = session.put(files_api + "/home/liudapao/liudaopao/wsgi.py", data=wsgi_content.encode("utf-8"))
print(f"  WSGI upload: {resp.status_code} - {resp.text[:100]}")

# Also upload wsgi.py at root level pointing to subdirectory
wsgi_root = r'''import sys
import os
sys.path.insert(0, "/home/liudapao/liudaopao")
from app import app as application
'''
resp = session.put(files_api + "/home/liudapao/wsgi.py", data=wsgi_root.encode("utf-8"))
print(f"  Root WSGI upload: {resp.status_code} - {resp.text[:100]}")

# Now check current web app setup
print("\n=== Checking web app setup ===")
# Check the web page for existing apps
resp = session.get(f"{BASE_URL}/user/{USERNAME}/webapps/")
print(f"  Web apps page: {resp.status_code}")

# Look for existing webapp details
# Try to find webapp config
existing_app = re.search(rf"{USERNAME}\.pythonanywhere\.com", resp.text)
if existing_app:
    print(f"  Existing web app found: {existing_app.group(0)}")
    
    # Try to get webapp config
    config_match = re.search(rf'action="(/user/{USERNAME}/webapps/{USERNAME}\.pythonanywhere\.com/update/)"', resp.text)
    if config_match:
        # Get the csrf token from the page
        page_csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', resp.text)
        if page_csrf:
            # It exists, just reload it
            pass
    
    # Try the reload button
    reload_match = re.search(rf'(/user/{USERNAME}/webapps/{USERNAME}\.pythonanywhere\.com/reload/)', resp.text)
    if reload_match:
        # There's a reload URL
        pass
    
    print("  Web app exists - will reload after setup")
else:
    print("  No existing web app found, need to create one")

# Set up venv via Files API - just touch the venv path
print("\n=== Setting up virtual environment ===")

# First check if venv exists
resp = session.get(files_api + "/home/liudapao/liudaopao/venv/")
if resp.status_code == 200:
    print("  venv directory exists")
else:
    print("  Need to create venv")

# Try to create a bash console via the web API
print("\n=== Creating bash console ===")
console_api = f"{BASE_URL}/api/v0/user/{USERNAME}/consoles/"
resp = session.post(console_api, json={"executable": "bash", "arguments": ""}, 
                   headers={"Content-Type": "application/json"})
print(f"  Console create: {resp.status_code} - {resp.text[:200]}")

# Update session csrf token
session.headers["X-CSRFToken"] = session.cookies.get("csrftoken", "")

# Send commands to set up venv
if resp.status_code == 201:
    console_id = resp.json().get("id")
    send_url = console_api + str(console_id) + "/send/"
    print(f"  Console ID: {console_id}")
    
    cmds = [
        "cd /home/liudapao/liudaopao",
        "python3 -m venv venv",
        "source venv/bin/activate",
        "pip install flask gunicorn",
        "echo VENV_SETUP_DONE"
    ]
    
    for cmd in cmds:
        time.sleep(2)
        sresp = session.post(send_url, json={"input": cmd + "\n"},
                            headers={"Content-Type": "application/json"})
        print(f"  Cmd '{cmd[:30]}...': {sresp.status_code}")
        if sresp.status_code == 200:
            result = sresp.json()
            print(f"    Output preview: {json.dumps(result).get('output','')[:200]}")

print("\n=== Trying web app setup via web UI ===")
# Go to web app or create page
resp = session.get(f"{BASE_URL}/user/{USERNAME}/webapps/")
# Check if there's a "Create" button
if "Add a new web app" in resp.text or "Create" in resp.text:
    print("  Need to create web app from scratch")
    # Save the page for analysis
    with open(os.path.join(FILES_DIR, "_webapps_page.html"), "w", encoding="utf-8") as f:
        f.write(resp.text)
else:
    # Check existing web app configuration
    # Look for the current wsgi file path
    wsgi_path_match = re.search(r"WSGI config file[^<]*<[^>]*>([^<]+)", resp.text)
    if wsgi_path_match:
        print(f"  WSGI path: {wsgi_path_match.group(1)}")
    
    # Try to update virtualenv path
    venv_path = "/home/liudapao/liudaopao/venv"
    # Look for the venv input
    venv_match = re.search(r'name="virtualenv" value="([^"]*)"', resp.text)
    if venv_match:
        print(f"  Current venv: {venv_match.group(1)}")
        if venv_match.group(1) != venv_path:
            # Update it
            page_csrf = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', resp.text).group(1)
            update_resp = session.post(
                f"{BASE_URL}/user/{USERNAME}/webapps/{USERNAME}.pythonanywhere.com/update/",
                data={
                    "csrfmiddlewaretoken": page_csrf,
                    "virtualenv": venv_path
                },
                headers={"Referer": resp.url}
            )
            print(f"  Venv update: {update_resp.status_code}")

print("\n=== Done! ===")
