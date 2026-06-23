import requests, re
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

# Write WSGI with --target pip install
new_wsgi = """import subprocess, sys, os
target_dir = "/home/liudapao/liudaopao/packages"
if os.path.isdir(target_dir):
    sys.path.insert(0, target_dir)
try:
    import flask
except ImportError:
    os.makedirs(target_dir, exist_ok=True)
    subprocess.run([sys.executable, "-m", "pip", "install",
                   "--target", target_dir, "flask", "gunicorn", "werkzeug"],
                  capture_output=True, timeout=120)
    sys.path.insert(0, target_dir)
sys.path.insert(0, "/home/liudapao/liudaopao")
from app import app as application
"""
r = s.post(fapi + wsgi_path, files={"content": new_wsgi.encode("utf-8")})
print("WSGI updated:", r.status_code)

# Reload
reload_url = "https://www.pythonanywhere.com/user/liudapao/webapps/liudapao.pythonanywhere.com/reload"
r = s.post(reload_url, data={"csrfmiddlewaretoken": s.cookies.get("csrftoken", "")})
print("Reloaded:", r.status_code)
print("Now WAIT 40s before next step...")