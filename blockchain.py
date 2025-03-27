import sqlite3
import hashlib
import time
import json
import os

class Blockchain:
    def __init__(self, db_path):
        self.db_path = db_path
        self.create_table()
        if self.get_last_block() is None:
            self.create_genesis_block()

    def create_table(self):
        """Pravi tabelu ako ne postoji"""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS blocks (
                         hash TEXT PRIMARY KEY,
                         idx INTEGER,
                         timestamp REAL,
                         data TEXT,
                         prev_hash TEXT,
                         nonce INTEGER)''')
            c.execute("PRAGMA journal_mode=WAL;")  # Omogućava paralelne upise
            conn.commit()

    def create_genesis_block(self):
        """Kreira prvi blok u lancu"""
        genesis_block = {
            "idx": 0,
            "timestamp": time.time(),
            "data": "Genesis Block",
            "prev_hash": "0",
            "nonce": 0
        }
        genesis_block["hash"] = self.calculate_hash(genesis_block)
        self.add_block_to_db(genesis_block)

    def calculate_hash(self, block):
        """Računa hash bloka"""
        block_string = f'{block["idx"]}{block["timestamp"]}{block["data"]}{block["prev_hash"]}{block["nonce"]}'
        return hashlib.sha256(block_string.encode()).hexdigest()

    def get_last_block(self):
        """Vraća poslednji blok iz baze"""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM blocks ORDER BY idx DESC LIMIT 1")
            block = c.fetchone()
            if block:
                return {
                    "idx": block[1],
                    "timestamp": block[2],
                    "data": block[3],
                    "prev_hash": block[4],
                    "hash": block[0],
                    "nonce": block[5]
                }
            return None

    def proof_of_work(self, prev_hash, data):
        """Izračunava novi blok koristeći PoW"""
        last_block = self.get_last_block()
        idx = last_block["idx"] + 1 if last_block else 0
        nonce = 0
        while True:
            timestamp = time.time()
            block = {
                "idx": idx,
                "timestamp": timestamp,
                "data": data,
                "prev_hash": prev_hash,
                "nonce": nonce
            }
            block_hash = self.calculate_hash(block)
            if block_hash.startswith("0000"):  # Podešavanje težine PoW-a
                block["hash"] = block_hash
                return block
            nonce += 1

    def add_block_to_db(self, block):
        """Dodaje blok u bazu podataka"""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO blocks (idx, timestamp, data, prev_hash, hash, nonce) VALUES (?, ?, ?, ?, ?, ?)",
                      (block["idx"], block["timestamp"], block["data"], block["prev_hash"], block["hash"], block["nonce"]))
            conn.commit()
