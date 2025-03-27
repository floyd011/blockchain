from flask import Flask, request, jsonify
import sqlite3
import requests

app = Flask(__name__)
DB_PATH = "masterchain.db"

def init_db():
    """Pravi tabelu za registrovane sidechain-ove i njihove čvorove"""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS sidechains (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     name TEXT,
                     node_url TEXT)''')
        conn.commit()

init_db()

@app.route('/register_sidechain', methods=['POST'])
def register_sidechain():
    """Registruje novi sidechain čvor"""
    data = request.json
    name = data.get("name")
    node_url = data.get("node_url")

    if not name or not node_url:
        return jsonify({"error": "Invalid data"}), 400

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO sidechains (name, node_url) VALUES (?, ?)", (name, node_url))
        conn.commit()

    return jsonify({"message": "Sidechain node registered"}), 201

@app.route('/get_sidechains', methods=['GET'])
def get_sidechains():
    """Vraća sve registrovane sidechain-ove i njihove čvorove"""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM sidechains")
        sidechains = [{"id": row[0], "name": row[1], "node_url": row[2]} for row in c.fetchall()]
    
    return jsonify(sidechains)

@app.route('/sync_sidechains', methods=['GET'])
def sync_sidechains():
    """Povlači podatke iz svih registrovanih sidechain-ova"""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT node_url FROM sidechains")
        sidechains = [row[0] for row in c.fetchall()]
    
    all_blocks = {}
    for sidechain_url in sidechains:
        try:
            response = requests.get(f"{sidechain_url}/blocks")
            if response.status_code == 200:
                all_blocks[sidechain_url] = response.json()
        except:
            continue  # Ako neki čvor ne odgovara, preskoči

    return jsonify(all_blocks)

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=4000)
