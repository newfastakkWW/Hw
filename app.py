from flask import Flask, request, jsonify, render_template_string
import os, random, string, datetime

app = Flask(__name__)

# XOR декодинг для ADMIN_TOKEN: 0x34.. ^ "newlik4" = "adm_key"
def get_admin_token():
    cipher = [0x34, 0x3f, 0x2d, 0x36, 0x33, 0x31, 0x6e]
    key = "newlik4"
    return "".join(chr(c ^ ord(key[i % len(key)])) for i, c in enumerate(cipher))

ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', get_admin_token())

# Храним ключи как объекты: {"key": str, "used": bool, "days": int, "created_at": date}
keys_db = []

def gen_key():
    parts = [''.join(random.choices(string.ascii_uppercase + string.digits, k=4)) for _ in range(3)]
    return f"KEY-{'-'.join(parts)}"

ADMIN_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Equigen Admin</title>
    <link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --md-sys-color-primary: #6750A4;
            --md-sys-color-on-primary: #FFFFFF;
            --md-sys-color-surface: #FEF7FF;
            --md-sys-color-surface-container: #F3EDF7;
            --md-sys-color-outline: #79747E;
        }
        body { 
            font-family: 'Google Sans', sans-serif; 
            background: var(--md-sys-color-surface); 
            margin: 0; padding: 20px; color: #1C1B1F;
        }
        .card {
            background: var(--md-sys-color-surface-container);
            border-radius: 28px; padding: 24px; margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        input {
            width: 100%; border: 1px solid var(--md-sys-color-outline);
            border-radius: 12px; padding: 12px; margin: 8px 0;
            background: transparent; box-sizing: border-box;
        }
        button {
            background: var(--md-sys-color-primary); color: var(--md-sys-color-on-primary);
            border: none; border-radius: 100px; padding: 10px 24px;
            cursor: pointer; font-weight: 500; transition: opacity 0.2s;
        }
        button:hover { opacity: 0.8; }
        .key-item {
            display: flex; justify-content: space-between; align-items: center;
            padding: 12px; border-bottom: 1px solid rgba(0,0,0,0.05);
        }
        .status-used { color: #B3261E; font-weight: bold; }
        .status-valid { color: #21005D; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🔑 Key Manager</h2>
        <input type="password" id="token" placeholder="Admin Token">
        <div style="display: flex; gap: 8px; margin-top: 8px;">
            <button onclick="apiCall('/adm/gen')">Создать 1 день</button>
            <button onclick="apiCall('/adm/listall')">Обновить список</button>
        </div>
    </div>

    <div class="card">
        <h3>Активные ключи</h3>
        <div id="keyList"></div>
    </div>

    <script>
        async function apiCall(path) {
            const token = document.getElementById('token').value;
            const r = await fetch(path, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({token})
            });
            const d = await r.json();
            if (d.error) alert(d.error);
            if (d.keys) renderKeys(d.keys);
            if (d.key) apiCall('/adm/listall');
        }

        function renderKeys(keys) {
            const list = document.getElementById('keyList');
            list.innerHTML = keys.map(k => `
                <div class="key-item">
                    <div>
                        <div style="font-weight:500">${k.key}</div>
                        <div style="font-size:0.8em; color:gray">${k.days} day(s)</div>
                    </div>
                    <div class="${k.used ? 'status-used' : 'status-valid'}">
                        ${k.used ? 'Использован' : 'Активен'}
                    </div>
                </div>
            `).join('');
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
    new_key = {
        "key": gen_key(),
        "used": False,
        "days": 1,
        "created_at": datetime.datetime.now().isoformat()
    }
    keys_db.append(new_key)
    return jsonify({"key": new_key["key"]})

@app.route('/adm/listall', methods=['POST'])
def list_all():
    if request.json.get('token') != ADMIN_TOKEN:
        return jsonify({"error": "Forbidden"}), 403
    return jsonify({"keys": keys_db})

@app.route('/check', methods=['POST'])
def check_key():
    user_key = request.json.get('key', '').strip().upper()
    for k in keys_db:
        if k["key"] == user_key and not k["used"]:
            k["used"] = True
            return jsonify({"valid": True, "days": k["days"]})
    return jsonify({"valid": False})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
