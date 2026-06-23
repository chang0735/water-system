import requests, re, os, time, json

USERNAME = "liudapao"
PASSWORD = "asdke0735"
BASE_URL = "https://www.pythonanywhere.com"

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

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

# Try different upload methods
tests = [
    ("form-data files", lambda url, content: session.post(url, files={"content": ("test.txt", content.encode())})),
    ("form-data data", lambda url, content: session.post(url, data={"content": content})),
    ("multipart alternate", lambda url, content: session.post(url, files={"content": content.encode()})),
]

test_content = "upload test"
for name, upload_fn in tests:
    try:
        resp = upload_fn(files_api + "/home/liudapao/liudaopao/_test_api.txt", test_content)
        print(f"  {name}: {resp.status_code} - {resp.text[:100]}")
        if resp.status_code == 200:
            print(f"  *** {name} WORKS! ***")
    except Exception as e:
        print(f"  {name}: ERROR - {e}")

# Check if the test file was created
resp = session.get(files_api + "/home/liudapao/liudaopao/_test_api.txt")
print(f"\nCheck test file: {resp.status_code}")
if resp.status_code == 200:
    print(f"  Content: {resp.text[:200]}")

# Delete test file
resp = session.delete(files_api + "/home/liudapao/liudaopao/_test_api.txt")
print(f"Delete test file: {resp.status_code}")
