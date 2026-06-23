import requests, re

USERNAME = "liudapao"
PASSWORD = "asdke0735"
BASE_URL = "https://www.pythonanywhere.com"

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})
resp = session.get(BASE_URL + "/login/?next=/")
csrf = re.search(r"Anywhere\.csrfToken\s*=\s*\"([^\"]+)\"", resp.text).group(1)
session.post(BASE_URL + "/login/", data={
    "csrfmiddlewaretoken": csrf, "auth-username": USERNAME,
    "auth-password": PASSWORD, "login_view-current_step": "auth"
}, headers={"Referer": BASE_URL + "/login/?next=/"})

session.headers["X-CSRFToken"] = session.cookies.get("csrftoken", "")
session.headers["Referer"] = BASE_URL + "/"

files_api = f"https://www.pythonanywhere.com/api/v0/user/{USERNAME}/files/path"

# Read the current WSGI file
wsgi_path = "/var/www/liudapao_pythonanywhere_com_wsgi.py"
resp = session.get(files_api + wsgi_path)
print(f"Current WSGI ({resp.status_code}):")
if resp.status_code == 200:
    print(resp.text[:1000])
else:
    print(f"Cannot read WSGI file: {resp.text[:200]}")
    # Try to find the actual WSGI file
    dir_path = "/var/www/"
    resp = session.get(files_api + dir_path)
    if resp.status_code == 200:
        files = resp.json()
        print(f"Files in /var/www/: {list(files.keys())[:10]}")
