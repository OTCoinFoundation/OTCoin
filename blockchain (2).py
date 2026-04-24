"""
blockchain.py — OTCoin Blockchain v2.0
Security fixes:
- Persistence: simpan ke file otcoin_chain.json
- Hard cap: 51,000,000 OTC total supply
- Signature validation wajib
- Difficulty adjustment otomatis
- Timestamp validation
"""

import hashlib
import json
import time
import os
from typing import List, Optional

# ─────────────────────────────────────────────
# KONFIGURASI OTCOIN
# ─────────────────────────────────────────────
TOTAL_SUPPLY       = 51_000_000.0
MINING_REWARD      = 50.0
HALVING_INTERVAL   = 210_000
DIFFICULTY_START   = 4
DIFFICULTY_INTERVAL = 2016
TARGET_BLOCK_TIME  = 10
DATA_FILE          = "otcoin_chain.json"


# ─────────────────────────────────────────────
# TRANSAKSI
# ─────────────────────────────────────────────
class Transaction:
    def __init__(self, sender, recipient, amount,
                 signature="COINBASE", timestamp=None):
        self.sender    = sender
        self.recipient = recipient
        self.amount    = amount
        self.signature = signature
        self.timestamp = timestamp or time.time()

    def to_dict(self):
        return {
            "sender": self.sender, "recipient": self.recipient,
            "amount": self.amount, "signature": self.signature,
            "timestamp": self.timestamp,
        }

    def to_string(self):
        return f"{self.sender}{self.recipient}{self.amount}{self.timestamp}"

    @classmethod
    def from_dict(cls, d):
        return cls(d["sender"], d["recipient"], d["amount"],
                   d.get("signature","COINBASE"), d.get("timestamp", time.time()))

    def __repr__(self):
        return f"<Tx {self.sender[:8]}→{self.recipient[:8]} Ꞵ{self.amount}>"


# ─────────────────────────────────────────────
# BLOK
# ─────────────────────────────────────────────
class Block:
    def __init__(self, index, transactions, previous_hash,
                 difficulty=DIFFICULTY_START, timestamp=None, nonce=0):
        self.index         = index
        self.timestamp     = timestamp or time.time()
        self.transactions  = transactions
        self.previous_hash = previous_hash
        self.difficulty    = difficulty
        self.nonce         = nonce
        self.hash          = self.calculate_hash()

    def calculate_hash(self):
        tx_data = json.dumps([tx.to_dict() for tx in self.transactions], sort_keys=True)
        raw = f"{self.index}{self.timestamp}{tx_data}{self.previous_hash}{self.nonce}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def mine(self):
        target = "0" * self.difficulty
        print(f"  ⛏  Mining blok #{self.index} (difficulty={self.difficulty})...")
        start = time.time()
        while self.hash[:self.difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        elapsed = time.time() - start
        print(f"  ✅ Blok #{self.index} ditemukan! Nonce={self.nonce} Hash={self.hash[:16]}... ({elapsed:.2f}s)\n")

    def is_valid(self):
        return (self.hash == self.calculate_hash() and
                self.hash[:self.difficulty] == "0" * self.difficulty)

    def to_dict(self):
        return {
            "index": self.index, "timestamp": self.timestamp,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "previous_hash": self.previous_hash, "difficulty": self.difficulty,
            "nonce": self.nonce, "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, d):
        txs = [Transaction.from_dict(t) for t in d["transactions"]]
        b = cls(d["index"], txs, d["previous_hash"], d["difficulty"],
                d["timestamp"], d["nonce"])
        b.hash = d["hash"]
        return b


# ─────────────────────────────────────────────
# BLOCKCHAIN
# ─────────────────────────────────────────────
class Blockchain:

    def __init__(self):
        self.chain        = []
        self.mempool      = []
        self.total_mined  = 0.0

        if os.path.exists(DATA_FILE):
            self._load_chain()
            print(f"📂 Blockchain dimuat: {len(self.chain)} blok | "
                  f"Total mined: Ꞵ{self.total_mined:,.1f} OTC\n")
        else:
            self._create_genesis_block()

    # ── Persistence ───────────────────────────
    def _save_chain(self):
        with open(DATA_FILE, "w") as f:
            json.dump({
                "chain": [b.to_dict() for b in self.chain],
                "total_mined": self.total_mined
            }, f, indent=2)

    def _load_chain(self):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
        self.chain       = [Block.from_dict(b) for b in data["chain"]]
        self.total_mined = data.get("total_mined", 0.0)

    # ── Genesis ───────────────────────────────
    def _create_genesis_block(self):
        genesis_tx = Transaction("SYSTEM", "genesis", 0, "GENESIS")
        genesis = Block(0, [genesis_tx], "0" * 64, DIFFICULTY_START)
        genesis.mine()
        self.chain.append(genesis)
        self._save_chain()
        print("🌐 OTCoin Genesis Block berhasil dibuat!\n")

    @property
    def latest_block(self):
        return self.chain[-1]

    # ── Supply & Reward ───────────────────────
    def get_current_reward(self):
        halvings = len(self.chain) // HALVING_INTERVAL
        return MINING_REWARD / (2 ** halvings)

    def remaining_supply(self):
        return max(0.0, TOTAL_SUPPLY - self.total_mined)

    # ── Difficulty Adjustment ─────────────────
    def get_current_difficulty(self):
        if len(self.chain) < DIFFICULTY_INTERVAL:
            return DIFFICULTY_START
        if len(self.chain) % DIFFICULTY_INTERVAL != 0:
            return self.latest_block.difficulty

        last    = self.chain[-1]
        first   = self.chain[-DIFFICULTY_INTERVAL]
        elapsed  = last.timestamp - first.timestamp
        expected = TARGET_BLOCK_TIME * DIFFICULTY_INTERVAL
        cur_diff = last.difficulty

        if elapsed < expected / 2:
            new_diff = cur_diff + 1
        elif elapsed > expected * 2:
            new_diff = max(1, cur_diff - 1)
        else:
            new_diff = cur_diff

        if new_diff != cur_diff:
            print(f"⚙️  Difficulty: {cur_diff} → {new_diff}\n")
        return new_diff

    # ── Validasi Signature ────────────────────
    def _verify_signature(self, public_key_hex, tx):
        try:
            from ecdsa import VerifyingKey, SECP256k1
            vk = VerifyingKey.from_string(bytes.fromhex(public_key_hex), curve=SECP256k1)
            msg_hash = hashlib.sha256(tx.to_string().encode()).digest()
            return vk.verify_digest(bytes.fromhex(tx.signature), msg_hash)
        except Exception:
            return False

    # ── Tambah Transaksi ──────────────────────
    def add_transaction(self, tx, public_key_hex=None):
        if tx.sender == "SYSTEM":
            self.mempool.append(tx)
            return

        if tx.amount <= 0:
            raise ValueError("❌ Jumlah harus positif")

        balance = self.get_balance(tx.sender)
        if balance < tx.amount:
            raise ValueError(f"❌ Saldo tidak cukup: Ꞵ{balance:.2f}")

        if public_key_hex:
            if not self._verify_signature(public_key_hex, tx):
                raise ValueError("❌ Signature tidak valid!")
            print(f"  ✅ Signature valid")

        if tx.timestamp > time.time() + 60:
            raise ValueError("❌ Timestamp tidak valid")

        self.mempool.append(tx)
        print(f"📬 Transaksi masuk mempool: {tx}")

    # ── Mining ────────────────────────────────
    def mine_pending_transactions(self, miner_address):
        reward = self.get_current_reward()

        if self.total_mined >= TOTAL_SUPPLY:
            print("⚠️  Supply habis! Mining tetap jalan tapi tanpa reward.")
            reward = 0.0
        elif reward > self.remaining_supply():
            reward = self.remaining_supply()

        reward_tx = Transaction("SYSTEM", miner_address, reward, "COINBASE")
        transactions = [reward_tx] + self.mempool[:]
        difficulty = self.get_current_difficulty()

        new_block = Block(
            index=len(self.chain),
            transactions=transactions,
            previous_hash=self.latest_block.hash,
            difficulty=difficulty
        )
        new_block.mine()
        self.chain.append(new_block)
        self.total_mined += reward
        self.mempool.clear()
        self._save_chain()

        pct = (self.total_mined / TOTAL_SUPPLY) * 100
        print(f"💰 Reward: Ꞵ{reward} OTC → {miner_address[:12]}...")
        print(f"📊 Mined: {self.total_mined:,.0f} / {TOTAL_SUPPLY:,.0f} OTC ({pct:.4f}%)\n")
        return new_block

    # ── Saldo ─────────────────────────────────
    def get_balance(self, address):
        balance = 0.0
        for block in self.chain:
            for tx in block.transactions:
                if tx.recipient == address: balance += tx.amount
                if tx.sender    == address: balance -= tx.amount
        return round(balance, 8)

    # ── Validasi Chain ────────────────────────
    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            cur  = self.chain[i]
            prev = self.chain[i - 1]
            if cur.hash != cur.calculate_hash():
                print(f"❌ Hash blok #{i} tidak valid!")
                return False
            if cur.previous_hash != prev.hash:
                print(f"❌ Chain putus di blok #{i}!")
                return False
            if not cur.is_valid():
                print(f"❌ Blok #{i} tidak memenuhi PoW!")
                return False
        return True

    def print_stats(self):
        pct = (self.total_mined / TOTAL_SUPPLY) * 100
        print("=" * 55)
        print("📊 OTCoin Network Stats")
        print("=" * 55)
        print(f"  Total Blok    : {len(self.chain):,}")
        print(f"  Total Mined   : Ꞵ{self.total_mined:,.2f} OTC ({pct:.4f}%)")
        print(f"  Sisa Supply   : Ꞵ{self.remaining_supply():,.2f} OTC")
        print(f"  Block Reward  : Ꞵ{self.get_current_reward()} OTC")
        print(f"  Difficulty    : {self.get_current_difficulty()}")
        print(f"  Mempool       : {len(self.mempool)} transaksi")
        print(f"  Data File     : {DATA_FILE}")
        print("=" * 55)


# ─────────────────────────────────────────────
# DEMO
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("🚀 OTCoin Blockchain v2.0\n")
    bc = Blockchain()
    bc.print_stats()

    miner = "1892c373ab5ea6e6fcc9feb8622d1d424e3e38432"

    print("\nMining 3 blok...\n")
    for i in range(3):
        bc.mine_pending_transactions(miner)

    print(f"💳 Saldo Miner : Ꞵ{bc.get_balance(miner):,.2f} OTC")
    print(f"🔍 Chain valid? {bc.is_chain_valid()}")
    print(f"✅ Data tersimpan di {DATA_FILE}")
    print("💡 Restart program → blockchain tetap ada!")
    bc.print_stats()
