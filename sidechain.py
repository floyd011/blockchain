from flask import Flask, request, jsonify
import requests
import sqlite3
import sys
import time
from blockchain import Blockchain
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
SIDECHAIN_NAME = sys.argv[1] if len(sys.argv) > 1 else "sidechain_default"
SIDECHAIN_PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5001
DB_PATH = f"{SIDECHAIN_NAME}-{SIDECHAIN_PORT}.db"
blockchain = Blockchain(DB_PATH)
peers = set()  # Skup drugih čvorova u istom sidechain-u
scheduler = BackgroundScheduler()

def init_db():
    """Inicijalizuje SQLite bazu i kreira tabelu ako ne postoji"""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS peers (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     node_url TEXT UNIQUE)''')
        c.execute("PRAGMA journal_mode=WAL;")  # Omogućava paralelne upise
        conn.commit()

def load_peers():
    """Učitava registrovane čvorove iz baze u memorijski skup"""
    global peers
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT node_url FROM peers")
        peers = {row[0] for row in c.fetchall()}


init_db()
load_peers()  # Učitaj poznate čvorove prilikom pokretanja aplikacije

@app.route('/mine', methods=['POST'])
def mine_block():
    data = request.json.get("data", "Default Data")
    last_block = blockchain.get_last_block()
    new_block = blockchain.proof_of_work(last_block["hash"], data)
    blockchain.add_block_to_db(new_block)

    # Obavesti ostale čvorove o novom bloku
    for peer in peers:
        try:
            requests.post(f"{peer}/sync", json=new_block)
        except:
            pass  # Ako čvor ne odgovara, ignoriši

    return jsonify(new_block), 201

@app.route('/sync', methods=['POST'])
def sync_block():
    """Prima novi blok i dodaje ga ako je validan"""
    block = request.json
    last_block = blockchain.get_last_block()
    print(block)
    # Validacija da je blok sledeći u lancu
    if block["prev_hash"] == last_block["hash"] and blockchain.calculate_hash(block) == block["hash"]:
        blockchain.add_block_to_db(block)
        return jsonify({"message": "Block added"}), 201
    return jsonify({"error": "Invalid block"}), 400

@app.route('/blocks', methods=['GET'])
def get_blocks():
    """Vraća sve blokove iz lokalnog sidechain-a"""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM blocks")
        columns = [col[0] for col in c.description]
        blocks = [dict(zip(columns, row)) for row in c.fetchall()]
    return jsonify(blocks)

@app.route('/register_node', methods=['POST'])
def register_node():
    """Dodaje novi node (čvor) u P2P mrežu ovog sidechain-a"""
    data = request.json
    node_url = data.get("node_url")

    if not node_url:
        return jsonify({"error": "Invalid data"}), 400

    peers.add(node_url)
   # Upis u bazu ako već ne postoji
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO peers (node_url) VALUES (?)", (node_url,))
        conn.commit()

    return jsonify({"message": "Node registered"}), 201

def sync_with_peers():
    """Periodično proverava nove blokove od drugih čvorova"""
    load_peers()
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT hash FROM blocks")
        local_hashes = {row[0] for row in c.fetchall()}  # Skup lokalnih hash-eva

    for peer in peers:
        try:
            response = requests.get(f"{peer}/blocks")
            remote_blocks = response.json()
            filtered_blocks = [block for block in remote_blocks if block["idx"] != 0 and block["hash"] not in local_hashes]
            for block in filtered_blocks:
                blockchain.add_block_to_db(block)
        except:
            pass  # Ako čvor ne odgovara, ignoriši

scheduler.add_job(sync_with_peers, 'interval', seconds=30)
scheduler.start()

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=SIDECHAIN_PORT)  # Menjaj port za svaki novi čvor
