from flask import Flask, request, jsonify
import json, os

app = Flask(__name__)

# Храним ключи в файле
KEYS_FILE = "keys.json"

def load_keys():
    if os.path.exists(KEYS_FILE):
        with open(KEYS_FILE) as f:
            return json.load(f)
    return {"valid": [], "used": []}

def save_keys(data):
    with open(KEYS_FILE, "w") as f:
        json.dump(data, f)

@app.route('/check', methods=['POST'])
def check_key():
    key = request.json.get('key', '').strip().upper()
    data = load_keys()
    
    if key in data["valid"] and key not in data["used"]:
        data["used"].append(key)
        save_keys(data)
        return jsonify({"valid": True})
    
    return jsonify({"valid": False})

@app.route('/add', methods=['POST'])
def add_key():
    # Простая защита — секретный токен
    token = request.json.get('token')
    if token != os.environ.get('ADMIN_TOKEN', 'secret123'):
        return jsonify({"error": "Forbidden"}), 403
    
    key = request.json.get('key', '').upper()
    data = load_keys()
    data["valid"].append(key)
    save_keys(data)
    return jsonify({"ok": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
