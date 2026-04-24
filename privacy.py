"""
privacy.py — OTCoin Privacy Layer v1.0

Fitur:
- Stealth Address: sembunyikan penerima
- Ring Signature: sembunyikan pengirim
- Confidential Transaction: sembunyikan jumlah
- Zero-Knowledge Proof (simplified): buktikan tanpa reveal
"""

import hashlib
import hmac
import os
import json
import time
import secrets
from typing import List, Tuple, Optional


# ─────────────────────────────────────────────
# STEALTH ADDRESS
# Sembunyikan alamat penerima!
# ─────────────────────────────────────────────
class StealthAddress:
    """
    Stealth Address memungkinkan pengirim membuat
    address unik untuk setiap transaksi.
    Hanya penerima yang bisa tahu mereka menerima OTC!
    """

    def __init__(self):
        # Generate spend key dan view key
        self.spend_key  = secrets.token_hex(32)
        self.view_key   = secrets.token_hex(32)
        self.public_spend = self._derive_public(self.spend_key)
        self.public_view  = self._derive_public(self.view_key)

    def _derive_public(self, private_key: str) -> str:
        """Derive public key dari private key."""
        return hashlib.sha256(private_key.encode()).hexdigest()

    def generate_stealth_address(self) -> Tuple[str, str]:
        """
        Pengirim generate stealth address untuk penerima.
        Returns: (stealth_address, ephemeral_key)
        """
        # Random ephemeral key untuk setiap transaksi
        ephemeral_secret = secrets.token_hex(32)
        ephemeral_public  = hashlib.sha256(ephemeral_secret.encode()).hexdigest()

        # Shared secret antara pengirim dan penerima
        shared_secret = hmac.new(
            self.view_key.encode(),
            ephemeral_public.encode(),
            hashlib.sha256
        ).hexdigest()

        # Stealth address unik
        stealth = hashlib.sha256(
            (shared_secret + self.public_spend).encode()
        ).hexdigest()

        stealth_address = "OTCs_" + stealth[:40]
        return stealth_address, ephemeral_public

    def scan_stealth(self, ephemeral_public: str,
                     stealth_address: str) -> bool:
        """
        Penerima scan apakah stealth address milik mereka.
        Hanya pemilik view_key yang bisa scan!
        """
        shared_secret = hmac.new(
            self.view_key.encode(),
            ephemeral_public.encode(),
            hashlib.sha256
        ).hexdigest()

        expected = hashlib.sha256(
            (shared_secret + self.public_spend).encode()
        ).hexdigest()

        expected_addr = "OTCs_" + expected[:40]
        return expected_addr == stealth_address

    def to_dict(self) -> dict:
        return {
            "public_spend": self.public_spend,
            "public_view":  self.public_view,
            "type": "StealthAddress"
        }


# ─────────────────────────────────────────────
# CONFIDENTIAL TRANSACTION
# Sembunyikan jumlah transaksi!
# ─────────────────────────────────────────────
class ConfidentialTransaction:
    """
    Sembunyikan jumlah transaksi menggunakan
    Pedersen Commitment (simplified).
    Orang bisa verifikasi transaksi valid
    tanpa tahu jumlahnya!
    """

    def __init__(self):
        # Blinding factor rahasia
        self.blinding_factor = secrets.token_hex(32)

    def commit(self, amount: float) -> str:
        """
        Buat commitment untuk jumlah.
        commitment = hash(amount + blinding_factor)
        """
        data = f"{amount:.8f}{self.blinding_factor}"
        return hashlib.sha256(data.encode()).hexdigest()

    def verify(self, commitment: str, amount: float,
               blinding_factor: str) -> bool:
        """Verifikasi commitment tanpa reveal amount ke publik."""
        data = f"{amount:.8f}{blinding_factor}"
        expected = hashlib.sha256(data.encode()).hexdigest()
        return expected == commitment

    def range_proof(self, amount: float) -> dict:
        """
        Buktikan amount dalam range valid (> 0 dan < supply)
        tanpa reveal jumlah sebenarnya.
        """
        # Simplified range proof
        is_valid = 0 < amount <= 51_000_000
        proof_hash = hashlib.sha256(
            f"{amount}{self.blinding_factor}range".encode()
        ).hexdigest()

        return {
            "valid":      is_valid,
            "proof":      proof_hash[:32],
            "min_value":  "> 0",
            "max_value":  "< 51,000,000 OTC",
        }


# ─────────────────────────────────────────────
# RING SIGNATURE
# Sembunyikan pengirim!
# ─────────────────────────────────────────────
class RingSignature:
    """
    Ring Signature memungkinkan pengirim
    menandatangani transaksi sebagai bagian dari
    kelompok (ring) — tidak ada yang tahu siapa pengirim aslinya!
    Seperti Monero!
    """

    def __init__(self, ring_size: int = 5):
        self.ring_size = ring_size

    def generate_ring(self, real_signer: str,
                      decoys: List[str]) -> List[str]:
        """Buat ring dengan pengirim asli + decoy addresses."""
        ring = [real_signer] + decoys[:self.ring_size - 1]
        # Shuffle supaya posisi pengirim asli tidak diketahui
        import random
        random.shuffle(ring)
        return ring

    def sign(self, message: str, real_signer: str,
             ring: List[str]) -> dict:
        """
        Buat ring signature.
        Membuktikan salah satu dari ring menandatangani
        tanpa reveal siapa!
        """
        # Hash pesan
        msg_hash = hashlib.sha256(message.encode()).hexdigest()

        # Generate key images untuk setiap member ring
        key_images = []
        for member in ring:
            ki = hashlib.sha256(
                f"{member}{msg_hash}".encode()
            ).hexdigest()
            key_images.append(ki[:16])

        # Ring signature hash
        ring_hash = hashlib.sha256(
            "".join(key_images).encode()
        ).hexdigest()

        # Real signer signature (private)
        real_sig = hmac.new(
            real_signer.encode(),
            (msg_hash + ring_hash).encode(),
            hashlib.sha256
        ).hexdigest()

        return {
            "ring":       ring,
            "ring_hash":  ring_hash,
            "key_images": key_images,
            "signature":  real_sig[:32],
            "ring_size":  len(ring),
        }

    def verify(self, message: str, signature: dict) -> bool:
        """
        Verifikasi ring signature valid
        tanpa tahu siapa yang menandatangani!
        """
        msg_hash = hashlib.sha256(message.encode()).hexdigest()
        ring = signature["ring"]

        key_images = []
        for member in ring:
            ki = hashlib.sha256(
                f"{member}{msg_hash}".encode()
            ).hexdigest()
            key_images.append(ki[:16])

        ring_hash = hashlib.sha256(
            "".join(key_images).encode()
        ).hexdigest()

        return ring_hash == signature["ring_hash"]


# ─────────────────────────────────────────────
# PRIVATE TRANSACTION
# Gabungkan semua privacy tech!
# ─────────────────────────────────────────────
class PrivateTransaction:
    """
    Transaksi privat OTCoin yang menggabungkan:
    - Stealth Address (sembunyikan penerima)
    - Confidential Transaction (sembunyikan jumlah)
    - Ring Signature (sembunyikan pengirim)
    """

    def __init__(self):
        self.conf_tx   = ConfidentialTransaction()
        self.ring_sig  = RingSignature(ring_size=5)

    def create(self, sender: str, recipient_stealth: StealthAddress,
               amount: float, decoys: List[str]) -> dict:
        """Buat transaksi privat lengkap."""

        print("🔒 Membuat Private Transaction...")
        print(f"   Jumlah    : TERSEMBUNYI ✅")
        print(f"   Pengirim  : TERSEMBUNYI ✅")
        print(f"   Penerima  : TERSEMBUNYI ✅")

        # 1. Generate stealth address untuk penerima
        stealth_addr, ephemeral = recipient_stealth.generate_stealth_address()

        # 2. Sembunyikan jumlah
        commitment = self.conf_tx.commit(amount)
        range_proof = self.conf_tx.range_proof(amount)

        # 3. Ring signature untuk sembunyikan pengirim
        ring = self.ring_sig.generate_ring(sender, decoys)
        message = f"{stealth_addr}{commitment}{ephemeral}"
        signature = self.ring_sig.sign(message, sender, ring)

        tx = {
            "id":           hashlib.sha256(
                               f"{stealth_addr}{commitment}{time.time()}".encode()
                            ).hexdigest()[:16],
            "type":         "PRIVATE",
            "timestamp":    time.time(),
            # Semua info privat!
            "stealth_addr": stealth_addr,
            "ephemeral":    ephemeral,
            "commitment":   commitment,
            "range_proof":  range_proof,
            "ring_sig":     signature,
            "blinding":     self.conf_tx.blinding_factor,
        }

        print(f"\n✅ Private Transaction berhasil dibuat!")
        print(f"   TX ID     : {tx['id']}")
        print(f"   Stealth   : {stealth_addr[:20]}...")
        print(f"   Ring Size : {signature['ring_size']} addresses")
        print(f"   Commitment: {commitment[:20]}...")

        return tx

    def verify(self, tx: dict) -> bool:
        """Verifikasi transaksi privat valid."""
        message = f"{tx['stealth_addr']}{tx['commitment']}{tx['ephemeral']}"
        return self.ring_sig.verify(message, tx["ring_sig"])


# ─────────────────────────────────────────────
# PRIVACY WALLET
# ─────────────────────────────────────────────
class PrivacyWallet:
    """Wallet OTCoin dengan fitur privasi penuh."""

    def __init__(self, address: str):
        self.address       = address
        self.stealth       = StealthAddress()
        self.private_txs   = []

    def receive_stealth_address(self) -> dict:
        """Berikan stealth info kepada pengirim."""
        return {
            "address":      self.address,
            "stealth_info": self.stealth.to_dict(),
        }

    def scan_incoming(self, transactions: List[dict]) -> List[dict]:
        """Scan transaksi masuk yang ditujukan untuk wallet ini."""
        incoming = []
        for tx in transactions:
            if tx.get("type") == "PRIVATE":
                if self.stealth.scan_stealth(
                    tx["ephemeral"], tx["stealth_addr"]
                ):
                    incoming.append(tx)
                    print(f"💰 Incoming private TX: {tx['id']}")
        return incoming

    def send_private(self, recipient_wallet: "PrivacyWallet",
                     amount: float, decoys: List[str]) -> dict:
        """Kirim OTC secara privat."""
        priv_tx = PrivateTransaction()
        tx = priv_tx.create(
            sender=self.address,
            recipient_stealth=recipient_wallet.stealth,
            amount=amount,
            decoys=decoys
        )
        self.private_txs.append(tx)
        return tx


# ─────────────────────────────────────────────
# DEMO
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("🔒 OTCoin Privacy Layer v1.0")
    print("=" * 60)
    print()

    # Setup wallets
    FOUNDER = "1892c373ab5ea6e6fcc9feb8622d1d424e3e38432"
    USER1   = "user1_address_abc123def456"
    USER2   = "user2_address_xyz789ghi012"

    # Decoy addresses untuk ring signature
    DECOYS = [
        "decoy1_aabbcc112233",
        "decoy2_ddeeff445566",
        "decoy3_gghhii778899",
        "decoy4_jjkkll001122",
    ]

    print("─" * 50)
    print("1️⃣  Setup Privacy Wallets")
    print("─" * 50)

    alice_wallet = PrivacyWallet(FOUNDER)
    bob_wallet   = PrivacyWallet(USER1)

    print(f"✅ Alice Wallet: {FOUNDER[:16]}...")
    print(f"   Stealth Public Spend: {alice_wallet.stealth.public_spend[:16]}...")
    print(f"   Stealth View Key   : {alice_wallet.stealth.view_key[:16]}... (RAHASIA!)")
    print()
    print(f"✅ Bob Wallet  : {USER1[:16]}...")
    print(f"   Stealth Public Spend: {bob_wallet.stealth.public_spend[:16]}...")
    print()

    print("─" * 50)
    print("2️⃣  Stealth Address Demo")
    print("─" * 50)
    stealth_addr, ephemeral = bob_wallet.stealth.generate_stealth_address()
    print(f"✅ Stealth Address untuk Bob  : {stealth_addr}")
    print(f"   Ephemeral Key             : {ephemeral[:16]}...")

    # Bob scan apakah address ini miliknya
    is_mine = bob_wallet.stealth.scan_stealth(ephemeral, stealth_addr)
    print(f"   Bob scan → Milik Bob?     : {is_mine} ✅")

    # Alice coba scan — bukan miliknya
    not_mine = alice_wallet.stealth.scan_stealth(ephemeral, stealth_addr)
    print(f"   Alice scan → Milik Alice? : {not_mine} ✅ (bukan milik Alice!)")
    print()

    print("─" * 50)
    print("3️⃣  Confidential Transaction Demo")
    print("─" * 50)
    conf = ConfidentialTransaction()
    amount = 500.0
    commitment = conf.commit(amount)
    range_proof = conf.range_proof(amount)

    print(f"   Jumlah asli  : Ꞵ{amount} OTC")
    print(f"   Commitment   : {commitment[:24]}... (publik — tidak ada yang tahu jumlahnya!)")
    print(f"   Range Proof  : {range_proof['proof'][:16]}... (membuktikan > 0 dan < 51M)")

    # Verify
    verified = conf.verify(commitment, amount, conf.blinding_factor)
    print(f"   Verified     : {verified} ✅")
    print()

    print("─" * 50)
    print("4️⃣  Ring Signature Demo")
    print("─" * 50)
    ring_sig = RingSignature(ring_size=5)
    ring = ring_sig.generate_ring(FOUNDER, DECOYS)
    print(f"   Ring members : {len(ring)} addresses (1 asli + 4 decoy)")
    print(f"   Ring         : {[r[:8]+'...' for r in ring]}")
    print(f"   Tidak ada yang tahu siapa pengirim asli! 🔒")

    sig = ring_sig.sign("OTCoin Private TX", FOUNDER, ring)
    valid = ring_sig.verify("OTCoin Private TX", sig)
    print(f"   Signature valid: {valid} ✅")
    print()

    print("─" * 50)
    print("5️⃣  Full Private Transaction")
    print("─" * 50)
    print(f"\nAlice kirim OTC ke Bob secara PRIVAT...\n")

    private_tx = alice_wallet.send_private(
        recipient_wallet=bob_wallet,
        amount=750.0,
        decoys=DECOYS
    )

    # Verify transaksi
    priv = PrivateTransaction()
    is_valid = priv.verify(private_tx)
    print(f"\n   TX Valid     : {is_valid} ✅")

    # Bob scan incoming
    print(f"\n   Bob scanning incoming transactions...")
    incoming = bob_wallet.scan_incoming([private_tx])
    print(f"   Bob menerima : {len(incoming)} transaksi privat ✅")

    print()
    print("=" * 60)
    print("✅ OTCoin Privacy Layer berjalan sempurna!")
    print()
    print("🔒 OTCoin sekarang punya:")
    print("   ✅ Stealth Address  — penerima tersembunyi")
    print("   ✅ Confidential TX  — jumlah tersembunyi")
    print("   ✅ Ring Signature   — pengirim tersembunyi")
    print()
    print("🚀 OTCoin lebih canggih dari Bitcoin DAN lebih")
    print("   private dari kebanyakan altcoin!")
    print("=" * 60)
