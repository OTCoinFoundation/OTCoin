"""
blockchain.py — Inti blockchain sederhana seperti Bitcoin
"""

import hashlib
import json
import time
from typing import List, Optional


# ─────────────────────────────────────────────
# TRANSAKSI
# ─────────────────────────────────────────────
class Transaction:
    def __init__(self, sender: str, recipient: str, amount: float, signature: str = "COINBASE"):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.signature = signature  # akan diisi oleh Wallet
        self.timestamp = time.time()

    def to_dict(self) -> dict:
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "signature": self.signature,
            "timestamp": self.timestamp,
        }

    def to_string(self) -> str:
        """String yang akan di-hash dan ditandatangani."""
        return f"{self.sender}{self.recipient}{self.amount}{self.timestamp}"

    def __repr__(self):
        return f"<Tx {self.sender[:8]}→{self.recipient[:8]} Ꞵ{self.amount}>"


# ─────────────────────────────────────────────
# BLOK
# ─────────────────────────────────────────────
class Block:
    def __init__(
        self,
        index: int,
        transactions: List[Transaction],
        previous_hash: str,
        difficulty: int = 4,
    ):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.difficulty = difficulty
        self.nonce = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        tx_data = json.dumps([tx.to_dict() for tx in self.transactions], sort_keys=True)
        raw = f"{self.index}{self.timestamp}{tx_data}{self.previous_hash}{self.nonce}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def mine(self) -> None:
        """Proof of Work: cari nonce agar hash dimulai dengan '0' * difficulty."""
        target = "0" * self.difficulty
        print(f"  ⛏  Mining blok #{self.index} (difficulty={self.difficulty})...")
        start = time.time()
        while self.hash[: self.difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        elapsed = time.time() - start
        print(f"  ✅ Blok #{self.index} ditemukan! Nonce={self.nonce} Hash={self.hash[:16]}... ({elapsed:.2f}s)\n")

    def is_valid(self) -> bool:
        return (
            self.hash == self.calculate_hash()
            and self.hash[: self.difficulty] == "0" * self.difficulty
        )

    def __repr__(self):
        return f"<Block #{self.index} hash={self.hash[:10]}... txs={len(self.transactions)}>"


# ─────────────────────────────────────────────
# BLOCKCHAIN
# ─────────────────────────────────────────────
class Blockchain:
    MINING_REWARD = 50.0   # reward untuk miner (seperti coinbase Bitcoin)
    DIFFICULTY = 4         # jumlah leading zero pada hash

    def __init__(self):
        self.chain: List[Block] = []
        self.mempool: List[Transaction] = []   # transaksi menunggu konfirmasi
        self._create_genesis_block()

    def _create_genesis_block(self) -> None:
        genesis_tx = Transaction("SYSTEM", "genesis", 0)
        genesis = Block(0, [genesis_tx], "0" * 64, self.DIFFICULTY)
        genesis.mine()
        self.chain.append(genesis)
        print("🌐 Genesis block berhasil dibuat!\n")

    @property
    def latest_block(self) -> Block:
        return self.chain[-1]

    def add_transaction(self, tx: Transaction) -> None:
        """Tambah transaksi ke mempool setelah validasi dasar."""
        if tx.sender != "SYSTEM":
            if self.get_balance(tx.sender) < tx.amount:
                raise ValueError(f"❌ Saldo tidak cukup: {tx.sender[:12]}... punya Ꞵ{self.get_balance(tx.sender):.2f}")
            if tx.amount <= 0:
                raise ValueError("❌ Jumlah transaksi harus positif")
        self.mempool.append(tx)
        print(f"📬 Transaksi masuk mempool: {tx}")

    def mine_pending_transactions(self, miner_address: str) -> Block:
        """Kumpulkan transaksi dari mempool, tambahkan reward, mining."""
        # Coinbase transaction = reward untuk miner
        reward_tx = Transaction("SYSTEM", miner_address, self.MINING_REWARD)
        transactions = [reward_tx] + self.mempool[:]

        new_block = Block(
            index=len(self.chain),
            transactions=transactions,
            previous_hash=self.latest_block.hash,
            difficulty=self.DIFFICULTY,
        )
        new_block.mine()
        self.chain.append(new_block)
        self.mempool.clear()  # bersihkan mempool
        print(f"💰 Miner {miner_address[:12]}... mendapat reward Ꞵ{self.MINING_REWARD}\n")
        return new_block

    def get_balance(self, address: str) -> float:
        """Hitung saldo address dengan scan seluruh chain (seperti UTXO sederhana)."""
        balance = 0.0
        for block in self.chain:
            for tx in block.transactions:
                if tx.recipient == address:
                    balance += tx.amount
                if tx.sender == address:
                    balance -= tx.amount
        return balance

    def is_chain_valid(self) -> bool:
        """Validasi integritas seluruh chain."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]

            if current.hash != current.calculate_hash():
                print(f"❌ Hash blok #{i} tidak valid!")
                return False
            if current.previous_hash != previous.hash:
                print(f"❌ Rantai putus antara blok #{i-1} dan #{i}!")
                return False
            if not current.is_valid():
                print(f"❌ Blok #{i} tidak memenuhi syarat Proof of Work!")
                return False
        return True

    def get_transaction_history(self, address: str) -> List[Transaction]:
        history = []
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender == address or tx.recipient == address:
                    history.append(tx)
        return history

    def print_chain(self) -> None:
        print("=" * 60)
        print("📦 BLOCKCHAIN")
        print("=" * 60)
        for block in self.chain:
            print(f"\nBlok #{block.index}")
            print(f"  Hash      : {block.hash[:24]}...")
            print(f"  Prev Hash : {block.previous_hash[:24]}...")
            print(f"  Nonce     : {block.nonce}")
            print(f"  Transaksi : {len(block.transactions)}")
            for tx in block.transactions:
                print(f"    {tx}")
        print("\n" + "=" * 60)


# ─────────────────────────────────────────────
# DEMO
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("🚀 Memulai MyCoin Blockchain...\n")

    bc = Blockchain()

    # Simulasi alamat wallet (nanti akan dari Wallet.py yang asli)
    alice = "alice_address_abc123"
    bob   = "bob_address_def456"
    miner = "miner_address_xyz789"

    # Tambah transaksi genesis manual agar alice punya saldo awal
    bc.add_transaction(Transaction("SYSTEM", alice, 100.0))
    bc.mine_pending_transactions(miner)

    print(f"💳 Saldo Alice : Ꞵ{bc.get_balance(alice):.2f}")
    print(f"💳 Saldo Miner : Ꞵ{bc.get_balance(miner):.2f}\n")

    # Alice kirim ke Bob
    bc.add_transaction(Transaction(alice, bob, 30.0))
    bc.add_transaction(Transaction(alice, bob, 10.0))
    bc.mine_pending_transactions(miner)

    print(f"💳 Saldo Alice : Ꞵ{bc.get_balance(alice):.2f}")
    print(f"💳 Saldo Bob   : Ꞵ{bc.get_balance(bob):.2f}")
    print(f"💳 Saldo Miner : Ꞵ{bc.get_balance(miner):.2f}\n")

    bc.print_chain()

    print(f"\n🔍 Chain valid? {bc.is_chain_valid()}")

    # Simulasi manipulasi
    print("\n🔴 Simulasi serangan: mengubah jumlah transaksi di blok #1...")
    bc.chain[1].transactions[1].amount = 99999
    bc.chain[1].hash = bc.chain[1].calculate_hash()  # update hash manual
    print(f"🔍 Chain valid setelah serangan? {bc.is_chain_valid()}")
