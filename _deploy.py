import requests, re, time

s = requests.Session()
s.headers.update({"User-Agent": "Mozilla/5.0"})
r = s.get("https://www.pythonanywhere.com/login/?next=/")
csrf = re.search(r'Anywhere\.csrfToken\s*=\s*"([^"]+)"', r.text).group(1)
s.post("https://www.pythonanywhere.com/login/", data={
    "csrfmiddlewaretoken": csrf,
    "auth-username": "liudapao",
    "auth-password": "asdke0735",
    "login_view-current_step": "auth"
}, headers={"Referer": "https://www.pythonanywhere.com/login/?next=/"})

s.headers["X-CSRFToken"] = s.cookies.get("csrftoken", "")
s.headers["Referer"] = "https://www.pythonanywhere.com/"

fapi = "https://www.pythonanywhere.com/api/v0/user/liudapao/files/path"
wsgi_path = "/var/www/liudapao_pythonanywhere_com_wsgi.py"

# Read error log for latest errors
r = s.get(fapi + "/var/log/liudapao.pythonanywhere.com.error.log")
if r.status_code == 200:
    print("=== ERROR LOG (last 15 lines) ===")
    lines = r.text.strip().split("\n")
    for line in lines[-15:]:
        print("  " + line)

# Write new WSGI that uses --target for pip install
new_wsgi = """import subprocess, sys, os

target_dir = "/home/liudapao/liudaopao/packages"
if os.path.isdir(target_dir):
    sys.path.insert(0, target_dir)

try:
    import flask
except ImportError:
    os.makedirs(target_dir, exist_ok=True)
    subprocess.run([
        sys.executable, "-m", "pip", "install",
        "--target", target_dir,
        "flask", "gunicorn"
    ], capture_output=True, timeout=120)
    sys.path.insert(0, target_dir)

sys.path.insert(0, "/home/liudapao/liudaopao")
from app import app as application
"""

r = s.post(fapi + wsgi_path, files={"content": new_wsgi.encode("utf-8")})
print("\nWSGI update:", r.status_code)

# Reload
reload_url = "https://www.pythonanywhere.com/user/liudapao/webapps/liudapao.pythonanywhere.com/reload"
r = s.post(reload_url, data={"csrfmiddlewaretoken": s.cookies.get("csrftoken", "")})
print("Reload:", r.status_code)

# Wait for pip install to complete (30 seconds)
print("\nWaiting 35s for pip install...")
time.sleep(35)

# Check site
r = requests.get("https://liudapao.pythonanywhere.com/health", timeout=10)
print("\nHealth after install:", r.status_code)
if r.status_code == 200:
    print("\n=== SUCCESS! ===")
    print(r.text[:200])
elif r.status_code == 500:
    r2 = s.get(fapi + "/var/log/liudapao.pythonanywhere.com.error.log")
    if r2.status_code == 200:
        print("\nNew errors:")
        lines = r2.text.strip().split("\n")
        for line in lines[-8:]:
            print("  " + line)

# Also try main page
r = requests.get("https://liudapao.pythonanywhere.com/", timeout=10)
print("\nMain page:", r.status_code)
if r.status_code == 200:
    import re as re2
    m = re2.search(r'<title>(.*?)</title>', r.text)
    print("Title:", m.group(1) if m else "N/A")

print("\nDone")