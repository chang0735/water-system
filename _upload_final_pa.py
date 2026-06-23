import requests, re, os

USERNAME = "liudapao"
PASSWORD = "asdke0735"
BASE_URL = "https://www.pythonanywhere.com"
FILES_DIR = r"C:\Users\Administrator\Desktop\刘大泡送水管理系统"
FILES = ["app.py", "index.html", "sw.js", "manifest.json", "icon-192.png", "icon-512.png", "requirements.txt"]

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

# Upload updated wsgi.py with correct path
wsgi_content = b"""import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "liudaopao"))
from app import app as application
"""
resp = session.post(
    files_api + "/home/liudapao/liudaopao/wsgi.py",
    files={"content": wsgi_content}
)
print(f"WSGI upload: {resp.status_code} - {resp.text[:50]}")

# Upload all files
print("\nUploading all project files...")
for filename in FILES:
    filepath = os.path.join(FILES_DIR, filename)
    if not os.path.exists(filepath):
        print(f"  {filename}: SKIP")
        continue
    
    with open(filepath, "rb") as f:
        raw = f.read()
    
    resp = session.post(
        files_api + f"/home/liudapao/liudaopao/{filename}",
        files={"content": raw}
    )
    status = "OK" if resp.status_code in (200, 201) else f"FAIL ({resp.status_code})"
    print(f"  {filename}: {status}")

# Verify
print("\nVerification:")
resp = session.get(files_api + "/home/liudapao/liudaopao/")
if resp.status_code == 200:
    files = sorted(resp.json().keys())
    print(f"Files: {files}")
    print(f"Total: {len(files)}")

# Create root-level wsgi.py that points to the project directory
wsgi_root = b"""import sys
import os
sys.path.insert(0, "/home/liudapao/liudaopao")
from app import app as application
"""
resp = session.post(
    files_api + "/home/liudapao/wsgi_symlink.py",
    files={"content": wsgi_root}
)
print(f"\nRoot WSGI link: {resp.status_code}")

print("\n=== Files upload complete! ===")
print(f"\nNext steps needed:")
print(f"1. Set up virtual environment at /home/liudapao/liudaopao/venv")
print(f"2. Install flask+gunicorn in the venv")
print(f"3. Configure web app to use:")
print(f"   - Source code: /home/liudapao/liudaopao")
print(f"   - WSGI: /home/liudapao/liudaopao/wsgi.py")
print(f"   - Virtualenv: /home/liudapao/liudaopao/venv")
print(f"4. Reload web app at https://{USERNAME}.pythonanywhere.com")
