from flask import Flask, request, jsonify, render_template_string
import os, random, string

app = Flask(__name__)
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', 'secret123')

# Перешли на словарь для O(1) скорости поиска
# Формат: {"KEY-123": {"used": False, "days": 30}}
keys_db = {}

def gen_key():
    parts = [''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) for _ in range(3)]
    return "KEY-" + "-".join(parts)

ADMIN_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Key Admin MD3</title>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --md-sys-color-background: #1c1b1f;
            --md-sys-color-surface: #2b2930;
            --md-sys-color-primary: #d0bcff;
            --md-sys-color-on-primary: #381e72;
            --md-sys-color-error: #f2b8b5;
            --md-sys-color-outline: #938f99;
            --md-sys-color-on-surface: #e6e1e5;
            --md-sys-color-on-surface-variant: #cac4d0;
        }
        body { 
            font-family: 'Roboto', sans-serif; 
            background: var(--md-sys-color-background); 
            color: var(--md-sys-color-on-surface); 
            padding: 20px; 
            margin: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .container {
            max-width: 600px;
            width: 100%;
        }
        h2 { 
            font-weight: 500; 
            color: var(--md-sys-color-primary); 
            margin-bottom: 20px;
        }
        .card {
            background: var(--md-sys-color-surface);
            border-radius: 24px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        input { 
            background: var(--md-sys-color-background); 
            color: var(--md-sys-color-on-surface); 
            border: 1px solid var(--md-sys-color-outline); 
            border-radius: 16px;
            padding: 14px 16px; 
            margin: 8px 0;
            width: calc(100% - 34px);
            font-size: 16px;
            outline: none;
            transition: border-color 0.2s;
        }
        input:focus {
            border-color: var(--md-sys-color-primary);
        }
        .row {
            display: flex;
            gap: 12px;
            margin-bottom: 16px;
        }
        .row input {
            margin: 0;
            flex: 1;
        }
        button { 
            background: var(--md-sys-color-primary); 
            color: var(--md-sys-color-on-primary); 
            border: none; 
            border-radius: 100px;
            padding: 10px 24px; 
            font-size: 14px;
            font-weight: 500;
            cursor: pointer; 
            transition: background 0.2s, transform 0.1s;
            height: 48px;
            white-space: nowrap;
        }
        button:hover { 
            opacity: 0.9; 
        }
        button:active {
            transform: scale(0.98);
        }
        .key-item { 
            background: var(--md-sys-color-background); 
            padding: 16px; 
            margin: 8px 0; 
            border-radius: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .used { 
            border: 1px solid var(--md-sys-color-error);
            color: var(--md-sys-color-on-surface-variant);
        }
        .badge {
            background: var(--md-sys-color-surface);
            padding: 6px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
            color: var(--md-sys-color-primary);
            margin-left: 8px;
        }
        .badge.error {
            color: var(--md-sys-color-error);
        }
        .badges-container {
            display: flex;
            align-items: center;
        }
        #msg { margin-bottom: 16px; font-weight: 500; min-height: 20px;}
    </style>
</head>
<body>
    <div class="container">
        <h2>🔑 Key Admin</h2>
        <div class="card">
            <input type="password" id="token" placeholder="Admin token" />
            <div id="msg"></div>
        </div>

        <div class="card">
            <h3 style="margin-top: 0;">Генерация</h3>
            <div class="row">
                <input type="number" id="genDays" placeholder="Дней (стандартно 30)" />
                <button onclick="genKey()">Создать</button>
            </div>
            
            <h3>Свой ключ</h3>
            <div class="row">
                <input type="text" id="customKey" placeholder="Формат: KEY-..." />
                <input type="number" id="customDays" placeholder="Дней" style="max-width: 100px;" />
                <button onclick="addKey()">Добавить</button>
            </div>
        </div>

        <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <h3 style="margin: 0;">Список ключей</h3>
                <button onclick="loadKeys()">Обновить</button>
            </div>
            <div id="keyList"></div>
        </div>
    </div>

    <script>
        function getToken() { return document.getElementById('token').value; }
        function msg(t, err) { 
            const el = document.getElementById('msg');
            el.style.color = err ? 'var(--md-sys-color-error)' : 'var(--md-sys-color-primary)'; 
            el.innerText = t; 
            setTimeout(() => el.innerText = '', 3000);
        }

        async function genKey() {
            const days = document.getElementById('genDays').value || 30;
            const r = await fetch('/adm/gen', {
                method:'POST', 
                headers:{'Content-Type':'application/json'}, 
                body: JSON.stringify({token: getToken(), days: parseInt(days)})
            });
            const d = await r.json();
            if (d.key) { msg('Создан: ' + d.key); loadKeys(); }
            else msg(d.error || 'Ошибка', true);
        }

        async function addKey() {
            const key = document.getElementById('customKey').value;
            const days = document.getElementById('customDays').value || 30;
            const r = await fetch('/adm/add', {
                method:'POST', 
                headers:{'Content-Type':'application/json'}, 
                body: JSON.stringify({token: getToken(), key: key, days: parseInt(days)})
            });
            const d = await r.json();
            if (d.ok) { msg('Добавлен!'); loadKeys(); }
            else msg(d.error || 'Ошибка', true);
        }

        async function loadKeys() {
            const r = await fetch('/adm/listall', {
                method:'POST', 
                headers:{'Content-Type':'application/json'}, 
                body: JSON.stringify({token: getToken()})
            });
            const d = await r.json();
            if (d.error) { msg(d.error, true); return; }
            
            const el = document.getElementById('keyList');
            el.innerHTML = '';
            
            for (const [key, data] of Object.entries(d.keys)) {
                const isUsed = data.used;
                el.innerHTML += `
                    <div class="key-item ${isUsed ? 'used' : ''}">
                        <span style="font-family: monospace; font-size: 16px;">${key}</span>
                        <div class="badges-container">
                            <span class="badge ${isUsed ? 'error' : ''}">${data.days} дней</span>
                            <span class="badge ${isUsed ? 'error' : ''}">${isUsed ? 'ЮЗНУТ' : 'АКТИВЕН'}</span>
                        </div>
                    </div>
                `;
            }
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
    
    days = request.json.get('days', 30)
    key = gen_key()
    keys_db[key] = {"used": False, "days": days}
    
    return jsonify({"key": key, "days": days})

@app.route('/adm/add', methods=['POST'])
def add():
    if request.json.get('token') != ADMIN_TOKEN:
        return jsonify({"error": "Forbidden"}), 403
    
    key = request.json.get('key', '').upper().strip()
    days = request.json.get('days', 30)
    
    if not key:
        return jsonify({"error": "Пустой ключ"}), 400
        
    keys_db[key] = {"used": False, "days": days}
    return jsonify({"ok": True})

@app.route('/adm/listall', methods=['POST'])
def list_all():
    if request.json.get('token') != ADMIN_TOKEN:
        return jsonify({"error": "Forbidden"}), 403
    return jsonify({"keys": keys_db})

@app.route('/check', methods=['POST'])
def check_key():
    key = request.json.get('key', '').strip().upper()
    
    if key in keys_db and not keys_db[key]['used']:
        keys_db[key]['used'] = True
        return jsonify({"valid": True, "days": keys_db[key]['days']})
        
    return jsonify({"valid": False})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
