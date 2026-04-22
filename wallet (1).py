"""
wallet.py — Wallet cryptocurrency dengan ECDSA (secp256k1 seperti Bitcoin)
Jalankan: pip install ecdsa
"""

import hashlib
import binascii
from ecdsa import SigningKey, VerifyingKey, SECP256k1, BadSignatureError
from blockchain import Blockchain, Transaction


# ─────────────────────────────────────────────
# WALLET
# ─────────────────────────────────────────────
class Wallet:
    def __init__(self):
        # Generate key pair baru
        self._signing_key = SigningKey.generate(curve=SECP256k1)
        self._verifying_key = self._signing_key.get_verifying_key()

    # ── Keys ──────────────────────────────────
    @property
    def private_key(self) -> str:
        return self._signing_key.to_string().hex()

    @property
    def public_key(self) -> str:
        return self._verifying_key.to_string().hex()

    @property
    def address(self) -> str:
        """
        Buat wallet address dari public key:
        public_key → SHA256 → RIPEMD160 → hex (simplified, tanpa Base58)
        """
        pub_bytes = self._verifying_key.to_string()
        sha256_hash = hashlib.sha256(pub_bytes).digest()
        ripemd160 = hashlib.new("ripemd160")
        ripemd160.update(sha256_hash)
        return "1" + ripemd160.hexdigest()   # prefix "1" seperti Bitcoin mainnet

    # ── Dari private key yang sudah ada ───────
    @classmethod
    def from_private_key(cls, private_key_hex: str) -> "Wallet":
        wallet = cls.__new__(cls)
        wallet._signing_key = SigningKey.from_string(
            bytes.fromhex(private_key_hex), curve=SECP256k1
        )
        wallet._verifying_key = wallet._signing_key.get_verifying_key()
        return wallet

    # ── Tanda Tangan ──────────────────────────
    def sign_transaction(self, tx: Transaction) -> str:
        """
        Tanda tangani transaksi dengan private key.
        Signature = ECDSA(SHA256(tx_string), private_key)
        """
        message = tx.to_string().encode()
        msg_hash = hashlib.sha256(message).digest()
        signature = self._signing_key.sign_digest(msg_hash)
        return signature.hex()

    def create_transaction(self, recipient: str, amount: float) -> Transaction:
        """Buat transaksi, tanda tangani, dan kembalikan."""
        tx = Transaction(
            sender=self.address,
            recipient=recipient,
            amount=amount,
        )
        tx.signature = self.sign_transaction(tx)
        return tx

    def print_info(self, label: str = "Wallet") -> None:
        print(f"\n{'─'*50}")
        print(f"🔑 {label}")
        print(f"{'─'*50}")
        print(f"  Address     : {self.address}")
        print(f"  Public Key  : {self.public_key[:32]}...")
        print(f"  Private Key : {self.private_key[:32]}... (RAHASIA!)")
        print(f"{'─'*50}\n")


# ─────────────────────────────────────────────
# VERIFIKASI SIGNATURE (digunakan oleh node/blockchain)
# ─────────────────────────────────────────────
def verify_signature(public_key_hex: str, tx: Transaction) -> bool:
    """
    Verifikasi bahwa transaksi benar-benar ditandatangani oleh pemilik public key.
    Bisa dijalankan oleh siapapun tanpa mengetahui private key.
    """
    if tx.sender == "SYSTEM":
        return True  # coinbase tidak perlu signature
    try:
        vk = VerifyingKey.from_string(bytes.fromhex(public_key_hex), curve=SECP256k1)
        message = tx.to_string().encode()
        msg_hash = hashlib.sha256(message).digest()
        sig_bytes = bytes.fromhex(tx.signature)
        return vk.verify_digest(sig_bytes, msg_hash)
    except (BadSignatureError, Exception):
        return False


# ─────────────────────────────────────────────
# BLOCKCHAIN DENGAN VALIDASI SIGNATURE
# ─────────────────────────────────────────────
class SecureBlockchain(Blockchain):
    """Blockchain yang memvalidasi signature setiap transaksi."""

    # Registry public key: address → public_key_hex
    _public_keys: dict = {}

    def register_public_key(self, address: str, public_key_hex: str) -> None:
        self._public_keys[address] = public_key_hex

    def add_transaction(self, tx: Transaction) -> None:
        if tx.sender != "SYSTEM":
            pub_key = self._public_keys.get(tx.sender)
            if not pub_key:
                raise ValueError(f"❌ Public key tidak ditemukan untuk {tx.sender[:14]}...")
            if not verify_signature(pub_key, tx):
                raise ValueError(f"❌ Signature tidak valid! Transaksi ditolak.")
            print(f"  ✅ Signature valid untuk {tx.sender[:14]}...")
        super().add_transaction(tx)


# ─────────────────────────────────────────────
# DEMO
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  🔐 MyCoin — Wallet & Digital Signature Demo")
    print("=" * 55)

    # Buat dua wallet
    alice = Wallet()
    bob   = Wallet()
    miner = Wallet()

    alice.print_info("Alice's Wallet")
    bob.print_info("Bob's Wallet")

    # Inisialisasi blockchain dengan validasi signature
    bc = SecureBlockchain()
    bc.register_public_key(alice.address, alice.public_key)
    bc.register_public_key(bob.address, bob.public_key)
    bc.register_public_key(miner.address, miner.public_key)

    # Beri Alice saldo awal (coinbase/SYSTEM tidak perlu signature)
    from blockchain import Transaction as Tx
    bc.add_transaction(Tx("SYSTEM", alice.address, 100.0))
    bc.mine_pending_transactions(miner.address)

    print(f"💳 Saldo Alice : Ꞵ{bc.get_balance(alice.address):.2f}")
    print(f"💳 Saldo Miner : Ꞵ{bc.get_balance(miner.address):.2f}\n")

    # Alice kirim ke Bob (dengan signature asli)
    print("📤 Alice mengirim Ꞵ25 ke Bob...")
    tx1 = alice.create_transaction(bob.address, 25.0)
    bc.add_transaction(tx1)
    bc.mine_pending_transactions(miner.address)

    print(f"\n💳 Saldo Alice : Ꞵ{bc.get_balance(alice.address):.2f}")
    print(f"💳 Saldo Bob   : Ꞵ{bc.get_balance(bob.address):.2f}")
    print(f"💳 Saldo Miner : Ꞵ{bc.get_balance(miner.address):.2f}\n")

    # Simulasi penipuan: Eve coba kirim dari address Alice tapi pakai key sendiri
    print("🔴 Simulasi penipuan: Eve mencoba kirim dari address Alice...")
    eve = Wallet()
    fake_tx = Transaction(alice.address, eve.address, 50.0)
    fake_tx.signature = eve.sign_transaction(fake_tx)  # tanda tangan Eve, bukan Alice!
    try:
        bc.add_transaction(fake_tx)
    except ValueError as e:
        print(f"  {e} ✅ Sistem berhasil menolak!\n")

    print("🔍 Blockchain valid:", bc.is_chain_valid())
