import os, json, sqlite3, hashlib, secrets, csv, io
from datetime import datetime
from flask import Flask, request, jsonify, g, send_from_directory

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, 'data', 'water.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH, timeout=10)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA journal_mode=WAL')
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop('db', None)
    if db: db.close()

def hash_pw(pwd):
    salt = secrets.token_hex(16)
    return salt + ':' + hashlib.sha256((salt + pwd).encode()).hexdigest()

def check_pw(pwd, stored):
    if ':' not in stored:
        return hashlib.sha256(pwd.encode()).hexdigest() == stored
    salt, h = stored.split(':', 1)
    return h == hashlib.sha256((salt + pwd).encode()).hexdigest()

def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute('PRAGMA journal_mode=WAL')
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL, real_name TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS products(id TEXT PRIMARY KEY, name TEXT, spec TEXT, price REAL, type TEXT DEFAULT 'bucket');
        CREATE TABLE IF NOT EXISTS customers(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, phone TEXT DEFAULT '', address TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY, date TEXT, customer_name TEXT, phone TEXT, address TEXT, items TEXT, total REAL, status TEXT DEFAULT 'pending', remark TEXT, delivery_person TEXT, delivery_time TEXT, done_time TEXT, cancel_time TEXT, create_time TEXT, create_by TEXT);
    ''')
    
    if db.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 0:
        now = datetime.now().isoformat()
        db.executemany('INSERT INTO users VALUES(?,?,?,?,?,?)', [
            ('admin', 'admin', hash_pw('admin123'), 'sales', '管理员', now),
            ('cangguan', 'cangguan', hash_pw('warehouse123'), 'warehouse', '仓管员', now),
            ('songshui', 'songshui', hash_pw('delivery123'), 'delivery', '送水工', now),
        ])
    if db.execute('SELECT COUNT(*) FROM products').fetchone()[0] == 0:
        db.executemany('INSERT INTO products VALUES(?,?,?,?,?)', [
            ('p1', '15L桶装水', '15L', 18, 'bucket'),
            ('p2', '18.9L桶装水', '18.9L', 20, 'bucket'),
            ('p3', '330ml瓶装水', '330ml', 2, 'bottle'),
            ('p4', '500ml瓶装水', '500ml', 3, 'bottle'),
        ])
    db.commit()
    db.close()

init_db()

# ---- Auth ----
@app.route('/api/login', methods=['POST'])
def login():
    d = request.json or {}
    u = d.get('username','').strip()
    p = d.get('password','')
    row = get_db().execute('SELECT * FROM users WHERE username=?',(u,)).fetchone()
    if not row or not check_pw(p, row['password_hash']):
        return jsonify({'error':'用户名或密码错误'}), 401
    return jsonify({'ok':True,'user':{'id':row['id'],'username':row['username'],'role':row['role'],'real_name':row['real_name']}})

# ---- Products ----
@app.route('/api/products')
def products():
    rows = get_db().execute('SELECT * FROM products ORDER BY type,name').fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/products', methods=['POST'])
def products_post():
    d = request.json or {}
    get_db().execute('INSERT OR REPLACE INTO products VALUES(?,?,?,?,?)',
        (d.get('id'),d.get('name'),d.get('spec'),float(d.get('price',0)),d.get('type','bucket')))
    get_db().commit()
    return jsonify({'ok':True})

@app.route('/api/products/<pid>', methods=['DELETE'])
def products_delete(pid):
    get_db().execute('DELETE FROM products WHERE id=?',(pid,))
    get_db().commit()
    return jsonify({'ok':True})

# ---- Customers ----
@app.route('/api/customers')
def customers():
    kw = request.args.get('q','')
    if kw:
        rows = get_db().execute('SELECT * FROM customers WHERE name LIKE ? OR phone LIKE ? ORDER BY name',(f'%{kw}%',f'%{kw}%')).fetchall()
    else:
        rows = get_db().execute('SELECT * FROM customers ORDER BY name').fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/api/customers', methods=['POST'])
def customers_post():
    d = request.json or {}
    db = get_db()
    if d.get('id'):
        db.execute('UPDATE customers SET name=?,phone=?,address=? WHERE id=?',(d['name'],d.get('phone',''),d.get('address',''),d['id']))
    else:
        db.execute('INSERT INTO customers(name,phone,address) VALUES(?,?,?)',(d['name'],d.get('phone',''),d.get('address','')))
    db.commit()
    return jsonify({'ok':True})

@app.route('/api/customers/<int:cid>', methods=['DELETE'])
def customers_delete(cid):
    get_db().execute('DELETE FROM customers WHERE id=?',(cid,))
    get_db().commit()
    return jsonify({'ok':True})

# ---- Orders ----
@app.route('/api/orders')
def orders():
    status = request.args.get('status','')
    kw = request.args.get('q','').lower()
    sql = 'SELECT * FROM orders WHERE 1=1'
    params = []
    if status:
        sql += ' AND status=?'; params.append(status)
    if kw:
        sql += ' AND (customer_name LIKE ? OR phone LIKE ? OR address LIKE ?)'
        params.extend([f'%{kw}%']*3)
    sql += ' ORDER BY date DESC, create_time DESC'
    rows = get_db().execute(sql, params).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        if isinstance(d.get('items'), str):
            try: d['items'] = json.loads(d['items'])
            except: pass
        result.append(d)
    return jsonify(result)

@app.route('/api/orders', methods=['POST'])
def orders_post():
    data = request.json
    items_list = data if isinstance(data, list) else [data] if data else []
    db = get_db()
    for o in items_list:
        items_json = json.dumps(o.get('items',[]), ensure_ascii=False)
        db.execute('''INSERT OR REPLACE INTO orders(id,date,customer_name,phone,address,items,total,status,remark,delivery_person,delivery_time,done_time,cancel_time,create_time,create_by)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (o.get('id') or f'DD-{datetime.now():%y%m%d%H%M%S}', 
             o.get('date',datetime.now().strftime('%Y-%m-%d')),
             o.get('customerName') or o.get('customer_name',''), o.get('phone',''), o.get('address',''),
             items_json, float(o.get('total',0)), o.get('status','pending'),
             o.get('remark',''), o.get('deliveryPerson',''), o.get('deliveryTime'), o.get('doneTime'), o.get('cancelTime'),
             o.get('create_time',datetime.now().isoformat()), o.get('createBy','')))
    db.commit()
    return jsonify({'ok':True})

@app.route('/api/orders/<oid>/status', methods=['PATCH'])
def order_status(oid):
    new_status = (request.json or {}).get('status','')
    db = get_db()
    now = datetime.now().isoformat()
    if new_status == 'delivering':
        db.execute('UPDATE orders SET status=?,delivery_time=? WHERE id=?',(new_status,now,oid))
    elif new_status == 'done':
        db.execute('UPDATE orders SET status=?,done_time=? WHERE id=?',(new_status,now,oid))
    elif new_status == 'cancelled':
        db.execute('UPDATE orders SET status=?,cancel_time=? WHERE id=?',(new_status,now,oid))
    else:
        db.execute('UPDATE orders SET status=? WHERE id=?',(new_status,oid))
    db.commit()
    return jsonify({'ok':True})

# ---- Stats ----
@app.route('/api/stats')
def stats():
    db = get_db()
    today = datetime.now().strftime('%Y-%m-%d')
    total = db.execute("SELECT COUNT(*) FROM orders WHERE status NOT IN ('cancelled','deleted')").fetchone()[0]
    today_orders = db.execute("SELECT COUNT(*), COALESCE(SUM(total),0) FROM orders WHERE date=? AND status!='cancelled'",(today,)).fetchone()
    pending = db.execute("SELECT COUNT(*) FROM orders WHERE status='pending'").fetchone()[0]
    ready = db.execute("SELECT COUNT(*) FROM orders WHERE status='ready'").fetchone()[0]
    delivering = db.execute("SELECT COUNT(*) FROM orders WHERE status='delivering'").fetchone()[0]
    done = db.execute("SELECT COUNT(*), COALESCE(SUM(total),0) FROM orders WHERE status='done'").fetchone()
    return jsonify({
        'totalOrders': total, 'todayOrders': today_orders[0], 'todayRevenue': today_orders[1],
        'pending': pending, 'ready': ready, 'delivering': delivering,
        'doneCount': done[0], 'totalRevenue': done[1]
    })

@app.route('/api/settings/password', methods=['POST'])
def change_password():
    d = request.json or {}
    username = d.get('username')
    old = d.get('old_password','')
    new = d.get('new_password','')
    if len(new) < 6: return jsonify({'error':'密码至少6位'}), 400
    row = get_db().execute('SELECT * FROM users WHERE username=?',(username,)).fetchone()
    if not row or not check_pw(old, row['password_hash']):
        return jsonify({'error':'旧密码错误'}), 403
    get_db().execute('UPDATE users SET password_hash=? WHERE username=?',(hash_pw(new),username))
    get_db().commit()
    return jsonify({'ok':True})

@app.route('/')
def index():
    return send_from_directory(BASE, 'index.html')

if __name__ == '__main__':
    print('\n  ====== 水站管理系统 ======')
    print('  http://localhost:5000')
    import socket
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM);s.connect(('10.254.254.254',1))
        ip=s.getsockname()[0];s.close()
        print(f'  http://{ip}:5000')
    except: pass
    print('  admin/admin123 | cangguan/warehouse123 | songshui/delivery123\n')
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
