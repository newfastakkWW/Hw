from flask import Flask, request, jsonify, render_template_string
import os, random, string, datetime

app = Flask(__name__)

def get_admin_token():
    cipher = [0x34, 0x3f, 0x2d, 0x36, 0x33, 0x31, 0x6e]
    key = "newlik4"
    return "".join(chr(c ^ ord(key[i % len(key)])) for i, c in enumerate(cipher))

ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', get_admin_token())
keys_db = []

def gen_random_key():
    return f"KEY-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}-{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"

ADMIN_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Equigen Key System</title>
    <link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #6750A4;
            --surface: #FEF7FF;
            --container: #F3EDF7;
        }
        body { font-family: 'Google Sans', sans-serif; background: var(--surface); padding: 20px; color: #1C1B1F; }
        .card { background: var(--container); border-radius: 24px; padding: 24px; margin-bottom: 16px; border: 1px solid #E6E0E9; }
        input { 
            width: 100%; border: 1px solid #79747E; border-radius: 8px; padding: 12px; 
            margin: 8px 0; background: white; box-sizing: border-box; font-size: 16px;
        }
        .actions { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
        button { 
            background: var(--primary); color: white; border: none; border-radius: 20px; 
            padding: 10px 20px; cursor: pointer; font-weight: 500; flex-grow: 1;
        }
        .key-row { 
            display: flex; justify-content: space-between; align-items: center; 
            padding: 12px; border-bottom: 1px solid rgba(0,0,0,0.05); 
        }
        .status { font-size: 12px; padding: 4px 8px; border-radius: 12px; font-weight: bold; }
        .status.used { background: #F9DEDC; color: #410E0B; }
        .status.active { background: #E8DEF8; color: #1D192B; }
    </style>
</head>
<body>
    <div class="card">
        <h3>Управление ключами</h3>
        <input type="password" id="token" placeholder="Админ-токен (adm_key)">
        <input type="text" id="customKey" placeholder="Кастомный ключ (пусто для рандома)">
        <input type="number" id="days" placeholder="Срок действия в днях" value="1">
        <div class="actions">
            <button onclick="genAction()">Создать ключ</button>
            <button onclick="listAction()" style="background:#49454F">Обновить список</button>
        </div>
    </div>

    <div class="card">
        <h3>Список ключей</h3>
        <div id="list"></div>
    </div>

    <script>
        async function api(path, body) {
            const r = await fetch(path, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({...body, token: document.getElementById('token').value})
            });
            return await r.json();
        }

        async function genAction() {
            const custom = document.getElementById('customKey').value;
            const days = document.getElementById('days').value;
            const d = await api('/adm/gen', {key: custom, days: parseInt(days || 1)});
            if (d.error) alert("Ошибка: " + d.error); else {
                document.getElementById('customKey').value = '';
                listAction();
            }
        }

        async function listAction() {
            const d = await api('/adm/listall', {});
            if (d.error) return alert("Ошибка: " + d.error);
            document.getElementById('list').innerHTML = d.keys.map(k => `
                <div class="key-row">
                    <div>
                        <strong>${k.key}</strong><br>
                        <small>${k.days} дн. | ${k.created_at.split('T')[0]}</small>
                    </div>
                    <span class="status ${k.used ? 'used' : 'active'}">${k.used ? 'ИСПОЛЬЗОВАН' : 'АКТИВЕН'}</span>
                </div>
            `).reverse().join('');
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
    data = request.json
    if data.get('token') != ADMIN_TOKEN:
        return jsonify({"error": "Forbidden"}), 403
    
    key_val = data.get('key').strip().upper() if data.get('key') else gen_random_key()
    days = data.get('days', 1)
    
    new_key = {
        "key": key_val,
        "used": False,
        "days": int(days),
        "created_at": datetime.datetime.now().isoformat()
    }
    keys_db.append(new_key)
    return jsonify({"ok": True, "key": key_val})

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
