from flask import Flask, request, jsonify, render_template_string
import os, json, random, string
# пмдорч срс опен срс для ключей, мне похуй
app = Flask(__name__)
KEYS_FILE = "keys.json"
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', 'secret123')

def load_keys():
    if os.path.exists(KEYS_FILE):
        with open(KEYS_FILE) as f:
            return json.load(f)
    return {"valid": [], "used": []}

def save_keys(data):
    with open(KEYS_FILE, "w") as f:
        json.dump(data, f)

def gen_key():
    parts = [''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) for _ in range(3)]
    return "KEY-" + "-".join(parts)
# паста 
ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Key Admin</title>
    <style>
        body { font-family: monospace; background: #111; color: #0f0; padding: 30px; }
        input, button { background: #222; color: #0f0; border: 1px solid #0f0; padding: 8px 14px; margin: 5px; }
        button { cursor: pointer; }
        button:hover { background: #0f0; color: #000; }
        .key { background: #1a1a1a; padding: 8px; margin: 4px 0; border-left: 3px solid #0f0; }
        .used { border-left-color: #f00; color: #888; }
        h2 { color: #0f0; border-bottom: 1px solid #0f0; padding-bottom: 8px; }
        #msg { color: #ff0; margin: 10px 0; }
    </style>
</head>
<body>
    <h2>🔑 Key Manager</h2>
    <div id="msg"></div>

    <div>
        <input type="password" id="token" placeholder="Admin token" />
        <button onclick="genKey()">Генерировать ключ</button>
        <button onclick="loadKeys()">Обновить список</button>
    </div>
    <br>
    <div>
        <input type="text" id="customKey" placeholder="Свой ключ (необязательно)" />
        <button onclick="addKey()">Добавить ключ</button>
    </div>

    <h2>Ключи:</h2>
    <div id="keyList"></div>

    <script>
        function getToken() { return document.getElementById('token').value; }
        function msg(t, err) { document.getElementById('msg').style.color = err ? '#f00' : '#ff0'; document.getElementById('msg').innerText = t; }

        async function genKey() {
            const r = await fetch('/adm/gen', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({token: getToken()})});
            const d = await r.json();
            if (d.key) { msg('Создан: ' + d.key); loadKeys(); }
            else msg(d.error || 'Ошибка', true);
        }

        async function addKey() {
            const key = document.getElementById('customKey').value;
            const r = await fetch('/adm/add', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({token: getToken(), key: key})});
            const d = await r.json();
            if (d.ok) { msg('Добавлен!'); loadKeys(); }
            else msg(d.error || 'Ошибка', true);
        }

        async function loadKeys() {
            const r = await fetch('/adm/list', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({token: getToken()})});
            const d = await r.json();
            if (d.error) { msg(d.error, true); return; }
            const el = document.getElementById('keyList');
            el.innerHTML = '';
            d.valid.forEach(k => {
                const used = d.used.includes(k);
                el.innerHTML += '<div class="key' + (used ? ' used' : '') + '">' + k + (used ? ' — ИСПОЛЬЗОВАН' : '') + '</div>';
            });
        }
    </script>
</body>
</html>
"""

@app.route('/adm')
def admin():
    return render_template_string(ADMIN_HTML)

@app.route('/adm/gen', methods=['POST'])
def gen():
    if request.json.get('token') != ADMIN_TOKEN:
        return jsonify({"error": "Forbidden"}), 403
    key = gen_key()
    data = load_keys()
    data["valid"].append(key)
    save_keys(data)
    return jsonify({"key": key})

@app.route('/adm/add', methods=['POST'])
def add():
    if request.json.get('token') != ADMIN_TOKEN:
        return jsonify({"error": "Forbidden"}), 403
    key = request.json.get('key', '').upper().strip()
    if not key:
        return jsonify({"error": "Пустой ключ"}), 400
    data = load_keys()
    data["valid"].append(key)
    save_keys(data)
    return jsonify({"ok": True})

@app.route('/adm/list', methods=['POST'])
def list_keys():
    if request.json.get('token') != ADMIN_TOKEN:
        return jsonify({"error": "Forbidden"}), 403
    return jsonify(load_keys())

@app.route('/check', methods=['POST'])
def check_key():
    key = request.json.get('key', '').strip().upper()
    data = load_keys()
    if key in data["valid"] and key not in data["used"]:
        data["used"].append(key)
        save_keys(data)
        return jsonify({"valid": True})
    return jsonify({"valid": False})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
