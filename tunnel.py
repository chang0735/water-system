import subprocess, re, time, sys

while True:
    print(f"[{time.strftime('%H:%M:%S')}] Starting tunnel...")
    p = subprocess.Popen(
        ['ssh','-o','StrictHostKeyChecking=no','-o','ConnectTimeout=15','-o','ServerAliveInterval=30',
         '-R','80:localhost:5000','nokey@localhost.run'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    url = None
    start = time.time()
    while time.time() - start < 30:
        line = p.stdout.readline()
        if not line: break
        m = re.search(r'https://[a-z0-9]+\.lhr\.life', line)
        if m:
            url = m.group()
            break
    
    if url:
        with open('tunnel_url.txt', 'w') as f:
            f.write(url)
        print(f'URL: {url}')
        # Keep alive
        p.wait()
    else:
        print('Failed to get URL, retrying...')
        p.terminate()
    
    print('Tunnel disconnected, reconnecting in 5s...')
    time.sleep(5)
