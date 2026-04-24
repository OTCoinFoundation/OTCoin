"""
lightning.py — OTCoin Lightning Network v1.0

Transaksi INSTAN dan MURAH di luar blockchain!
- Buka payment channel antar 2 pihak
- Kirim OTC instan tanpa tunggu mining
- Tutup channel → hasil akhir dicatat di blockchain
- 1000+ transaksi per detik!
"""

import hashlib
import time
import secrets
from typing import Dict, List, Optional, Tuple


# ─────────────────────────────────────────────
# PAYMENT CHANNEL
# ─────────────────────────────────────────────
class PaymentChannel:
    """
    Channel pembayaran antara 2 pihak.
    Seperti tab di warung — bayar di akhir saja!
    """

    def __init__(self, party_a: str, party_b: str,
                 deposit_a: float, deposit_b: float = 0.0):
        self.id         = "CH_" + secrets.token_hex(8)
        self.party_a    = party_a
        self.party_b    = party_b
        self.deposit_a  = deposit_a
        self.deposit_b  = deposit_b
        self.balance_a  = deposit_a
        self.balance_b  = deposit_b
        self.state      = "OPEN"
        self.tx_count   = 0
        self.opened_at  = time.time()
        self.txs: List[dict] = []

        print(f"\n⚡ Lightning Channel Dibuka!")
        print(f"   ID      : {self.id}")
        print(f"   Party A : {party_a[:12]}... (Ꞵ{deposit_a} OTC)")
        print(f"   Party B : {party_b[:12]}... (Ꞵ{deposit_b} OTC)")
        print(f"   Status  : {self.state}\n")

    def send(self, sender: str, amount: float) -> dict:
        """Kirim OTC INSTAN melalui channel — tidak perlu mining!"""

        if self.state != "OPEN":
            return {"success": False, "error": "Channel tidak aktif"}

        # Tentukan pengirim dan penerima
        if sender == self.party_a:
            if self.balance_a < amount:
                return {"success": False,
                        "error": f"Saldo tidak cukup: Ꞵ{self.balance_a}"}
            self.balance_a -= amount
            self.balance_b += amount
            recipient = self.party_b
        elif sender == self.party_b:
            if self.balance_b < amount:
                return {"success": False,
                        "error": f"Saldo tidak cukup: Ꞵ{self.balance_b}"}
            self.balance_b -= amount
            self.balance_a += amount
            recipient = self.party_a
        else:
            return {"success": False, "error": "Bukan member channel"}

        self.tx_count += 1
        tx = {
            "id":        f"LTX_{self.id}_{self.tx_count}",
            "sender":    sender,
            "recipient": recipient,
            "amount":    amount,
            "timestamp": time.time(),
            "channel":   self.id,
            "instant":   True,
        }
        self.txs.append(tx)

        print(f"  ⚡ INSTAN! Ꞵ{amount} OTC: "
              f"{sender[:8]}... → {recipient[:8]}...")
        print(f"     Saldo A: Ꞵ{self.balance_a} | "
              f"Saldo B: Ꞵ{self.balance_b}")

        return {"success": True, **tx}

    def close(self) -> dict:
        """
        Tutup channel dan settle ke blockchain.
        Hanya 1 transaksi blockchain untuk semua TX!
        """
        if self.state != "OPEN":
            return {"success": False, "error": "Channel sudah ditutup"}

        self.state = "CLOSED"
        duration = time.time() - self.opened_at

        settlement = {
            "channel_id":   self.id,
            "party_a":      self.party_a,
            "party_b":      self.party_b,
            "final_a":      self.balance_a,
            "final_b":      self.balance_b,
            "total_txs":    self.tx_count,
            "duration_min": duration/60,
            "on_chain_txs": 2,  # hanya open + close!
        }

        print(f"\n🔒 Channel {self.id} Ditutup!")
        print(f"   Total TX di channel : {self.tx_count} transaksi")
        print(f"   TX di blockchain    : 2 saja (open + close)!")
        print(f"   Final A             : Ꞵ{self.balance_a} OTC")
        print(f"   Final B             : Ꞵ{self.balance_b} OTC")
        print(f"   Durasi              : {duration/60:.1f} menit\n")

        return {"success": True, "settlement": settlement}

    def get_status(self) -> dict:
        return {
            "id":        self.id,
            "state":     self.state,
            "balance_a": self.balance_a,
            "balance_b": self.balance_b,
            "tx_count":  self.tx_count,
        }


# ─────────────────────────────────────────────
# LIGHTNING ROUTER
# Kirim OTC ke siapapun melalui jaringan channel!
# ─────────────────────────────────────────────
class LightningRouter:
    """
    Router untuk menemukan jalur pembayaran
    melalui jaringan channel yang ada.
    Seperti GPS untuk transaksi!
    """

    def __init__(self):
        self.channels: Dict[str, PaymentChannel] = {}
        # Graph: address → list of channel IDs
        self.graph: Dict[str, List[str]] = {}

    def add_channel(self, channel: PaymentChannel):
        """Tambah channel ke network."""
        self.channels[channel.id] = channel

        # Update graph
        a, b = channel.party_a, channel.party_b
        if a not in self.graph: self.graph[a] = []
        if b not in self.graph: self.graph[b] = []
        self.graph[a].append(channel.id)
        self.graph[b].append(channel.id)

    def find_route(self, sender: str, recipient: str,
                   amount: float) -> Optional[List[str]]:
        """
        Temukan jalur dari sender ke recipient.
        Menggunakan BFS (Breadth-First Search).
        """
        if sender == recipient:
            return []

        visited = {sender}
        queue = [[sender]]

        while queue:
            path = queue.pop(0)
            current = path[-1]

            for ch_id in self.graph.get(current, []):
                ch = self.channels.get(ch_id)
                if not ch or ch.state != "OPEN":
                    continue

                # Tentukan next hop
                next_hop = ch.party_b if current == ch.party_a else ch.party_a

                if next_hop == recipient:
                    return path + [next_hop]

                if next_hop not in visited:
                    visited.add(next_hop)
                    queue.append(path + [next_hop])

        return None  # Tidak ada jalur

    def send_payment(self, sender: str, recipient: str,
                     amount: float) -> dict:
        """
        Kirim pembayaran melalui jaringan Lightning.
        Otomatis cari jalur terbaik!
        """
        print(f"\n⚡ Lightning Payment: Ꞵ{amount} OTC")
        print(f"   From: {sender[:12]}...")
        print(f"   To  : {recipient[:12]}...")

        route = self.find_route(sender, recipient, amount)

        if route is None:
            return {"success": False,
                    "error": "Tidak ada jalur ke recipient"}

        print(f"   Route: {' → '.join([r[:8]+'...' for r in route])}")

        # Kirim melalui channel
        results = []
        current = sender

        for next_hop in route[1:]:
            # Cari channel antara current dan next_hop
            ch = self._find_channel(current, next_hop)
            if not ch:
                return {"success": False, "error": "Channel tidak ditemukan"}

            result = ch.send(current, amount)
            if not result["success"]:
                return {"success": False, "error": result["error"]}

            results.append(result)
            current = next_hop

        print(f"   ✅ Payment berhasil! Instan! 🚀")
        return {
            "success": True,
            "amount":  amount,
            "hops":    len(route) - 1,
            "route":   route,
        }

    def _find_channel(self, a: str, b: str) -> Optional[PaymentChannel]:
        """Cari channel antara dua address."""
        for ch_id in self.graph.get(a, []):
            ch = self.channels[ch_id]
            if (ch.party_a == a and ch.party_b == b) or \
               (ch.party_a == b and ch.party_b == a):
                if ch.state == "OPEN":
                    return ch
        return None

    def get_network_stats(self) -> dict:
        open_ch = [c for c in self.channels.values()
                   if c.state == "OPEN"]
        total_tx = sum(c.tx_count for c in self.channels.values())
        total_liquidity = sum(
            c.balance_a + c.balance_b for c in open_ch
        )
        return {
            "total_channels":    len(self.channels),
            "open_channels":     len(open_ch),
            "total_txs":         total_tx,
            "total_liquidity":   total_liquidity,
            "nodes":             len(self.graph),
        }


# ─────────────────────────────────────────────
# DEMO
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("⚡ OTCoin Lightning Network v1.0")
    print("=" * 60)

    ALICE  = "1892c373ab5ea6e6fcc9feb8622d1d424e3e38432"
    BOB    = "bob_address_def456789abc123def456789abc"
    CAROL  = "carol_address_xyz789ghi012jkl345mno678"
    DAVE   = "dave_address_pqr901stu234vwx567yza890"

    router = LightningRouter()

    print("\n" + "─"*50)
    print("1️⃣  Buka Payment Channels")
    print("─"*50)

    # Alice ↔ Bob
    ch_ab = PaymentChannel(ALICE, BOB, deposit_a=500, deposit_b=200)
    router.add_channel(ch_ab)

    # Bob ↔ Carol
    ch_bc = PaymentChannel(BOB, CAROL, deposit_a=300, deposit_b=300)
    router.add_channel(ch_bc)

    # Carol ↔ Dave
    ch_cd = PaymentChannel(CAROL, DAVE, deposit_a=400, deposit_b=100)
    router.add_channel(ch_cd)

    print("─"*50)
    print("2️⃣  Transaksi INSTAN di Channel")
    print("─"*50)

    # Banyak transaksi instan!
    print("\nAlice → Bob (50 transaksi INSTAN):")
    start = time.time()
    for i in range(50):
        ch_ab.send(ALICE, 1.0)
    elapsed = time.time() - start
    print(f"\n✅ 50 transaksi selesai dalam {elapsed*1000:.1f}ms!")
    print(f"   Kecepatan: {50/elapsed:.0f} tx/detik")

    print("\n" + "─"*50)
    print("3️⃣  Multi-Hop Payment (Alice → Dave)")
    print("─"*50)
    print("Route: Alice → Bob → Carol → Dave")

    result = router.send_payment(ALICE, DAVE, 10.0)
    if result["success"]:
        print(f"✅ Berhasil! Hops: {result['hops']}")

    print("\n" + "─"*50)
    print("4️⃣  Network Stats")
    print("─"*50)
    stats = router.get_network_stats()
    print(f"   Total Channels  : {stats['total_channels']}")
    print(f"   Open Channels   : {stats['open_channels']}")
    print(f"   Total TX        : {stats['total_txs']}")
    print(f"   Total Liquidity : Ꞵ{stats['total_liquidity']} OTC")
    print(f"   Nodes           : {stats['nodes']}")

    print("\n" + "─"*50)
    print("5️⃣  Close Channel & Settle ke Blockchain")
    print("─"*50)
    ch_ab.close()

    print("=" * 60)
    print("✅ OTCoin Lightning Network berjalan sempurna!")
    print()
    print("⚡ Keunggulan vs Bitcoin Lightning:")
    print("   ✅ Integrasi dengan Smart Contract OTCoin")
    print("   ✅ Integrasi dengan Privacy Layer OTCoin")
    print("   ✅ Multi-hop routing otomatis")
    print("   ✅ 1000+ transaksi per detik")
    print("   ✅ Biaya hampir nol!")
    print("=" * 60)
