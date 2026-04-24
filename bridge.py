"""
bridge.py — OTCoin Cross-Chain Bridge v1.0

One Transaction. All Chains.
Hubungkan OTCoin ke Bitcoin, Ethereum, Solana!
"""

import hashlib
import time
import secrets
from typing import Dict, Optional


SUPPORTED_CHAINS = ["OTC", "BTC", "ETH", "SOL", "BNB"]

EXCHANGE_RATES = {
    ("OTC", "BTC"): 0.000002,
    ("OTC", "ETH"): 0.00003,
    ("OTC", "SOL"): 0.0005,
    ("OTC", "BNB"): 0.0001,
    ("BTC", "OTC"): 500000,
    ("ETH", "OTC"): 33333,
    ("SOL", "OTC"): 2000,
    ("BNB", "OTC"): 10000,
}

BRIDGE_FEE = 0.001  # 0.1% fee


class CrossChainBridge:
    """
    Bridge untuk swap OTC ↔ chain lain.
    One Transaction. All Chains!
    """

    def __init__(self):
        self.pending:   Dict[str, dict] = {}
        self.completed: Dict[str, dict] = {}
        self.total_volume = 0.0

    def get_rate(self, from_chain: str, to_chain: str) -> float:
        return EXCHANGE_RATES.get((from_chain, to_chain), 0.0)

    def get_quote(self, from_chain: str, to_chain: str,
                  amount: float) -> dict:
        rate = self.get_rate(from_chain, to_chain)
        if not rate:
            return {"success": False, "error": "Pair tidak didukung"}

        output = amount * rate
        fee    = output * BRIDGE_FEE
        net    = output - fee

        return {
            "success":    True,
            "from":       f"{amount} {from_chain}",
            "to":         f"{net:.8f} {to_chain}",
            "rate":       rate,
            "fee":        f"{fee:.8f} {to_chain}",
            "output":     net,
        }

    def initiate_swap(self, from_chain: str, to_chain: str,
                      amount: float, sender: str,
                      recipient: str) -> dict:
        if from_chain not in SUPPORTED_CHAINS or \
           to_chain not in SUPPORTED_CHAINS:
            return {"success": False, "error": "Chain tidak didukung"}

        quote = self.get_quote(from_chain, to_chain, amount)
        if not quote["success"]:
            return quote

        swap_id = "SWAP_" + secrets.token_hex(8)
        secret  = secrets.token_hex(32)
        secret_hash = hashlib.sha256(secret.encode()).hexdigest()

        swap = {
            "id":          swap_id,
            "from_chain":  from_chain,
            "to_chain":    to_chain,
            "amount_in":   amount,
            "amount_out":  quote["output"],
            "sender":      sender,
            "recipient":   recipient,
            "secret_hash": secret_hash,
            "secret":      secret,
            "status":      "PENDING",
            "created_at":  time.time(),
            "expires_at":  time.time() + 3600,
        }

        self.pending[swap_id] = swap

        print(f"\n🌉 Cross-Chain Swap Initiated!")
        print(f"   Swap ID   : {swap_id}")
        print(f"   From      : {amount} {from_chain}")
        print(f"   To        : {quote['output']:.6f} {to_chain}")
        print(f"   Fee       : {quote['fee']}")
        print(f"   Recipient : {recipient[:16]}...")
        print(f"   Status    : PENDING ⏳")

        return {"success": True, "swap_id": swap_id, **quote}

    def complete_swap(self, swap_id: str) -> dict:
        swap = self.pending.get(swap_id)
        if not swap:
            return {"success": False, "error": "Swap tidak ditemukan"}

        if time.time() > swap["expires_at"]:
            swap["status"] = "EXPIRED"
            return {"success": False, "error": "Swap expired"}

        swap["status"]       = "COMPLETED"
        swap["completed_at"] = time.time()
        self.completed[swap_id] = swap
        del self.pending[swap_id]
        self.total_volume += swap["amount_in"]

        print(f"\n✅ Swap {swap_id} COMPLETED!")
        print(f"   {swap['amount_in']} {swap['from_chain']} → "
              f"{swap['amount_out']:.6f} {swap['to_chain']}")
        print(f"   Recipient: {swap['recipient'][:16]}...")

        return {"success": True, "swap": swap}

    def get_stats(self) -> dict:
        return {
            "supported_chains": SUPPORTED_CHAINS,
            "pending_swaps":    len(self.pending),
            "completed_swaps":  len(self.completed),
            "total_volume_otc": self.total_volume,
            "bridge_fee":       f"{BRIDGE_FEE*100}%",
        }


if __name__ == "__main__":
    print("=" * 60)
    print("🌉 OTCoin Cross-Chain Bridge v1.0")
    print("    One Transaction. All Chains.")
    print("=" * 60)

    bridge = CrossChainBridge()
    ALICE = "1892c373ab5ea6e6fcc9feb8622d1d424e3e38432"
    BOB   = "bob_eth_address_0x1234567890abcdef"

    print("\n📊 Supported Chains:", " | ".join(SUPPORTED_CHAINS))

    print("\n" + "─"*50)
    print("1️⃣  Get Quote: 1000 OTC → ETH")
    print("─"*50)
    quote = bridge.get_quote("OTC", "ETH", 1000)
    print(f"   Input  : {quote['from']}")
    print(f"   Output : {quote['to']}")
    print(f"   Fee    : {quote['fee']}")
    print(f"   Rate   : 1 OTC = {quote['rate']} ETH")

    print("\n" + "─"*50)
    print("2️⃣  Swap: OTC → BTC")
    print("─"*50)
    swap1 = bridge.initiate_swap("OTC","BTC",500,ALICE,"btc_recipient_addr")
    if swap1["success"]:
        bridge.complete_swap(swap1["swap_id"])

    print("\n" + "─"*50)
    print("3️⃣  Swap: OTC → SOL")
    print("─"*50)
    swap2 = bridge.initiate_swap("OTC","SOL",200,ALICE,"sol_recipient_addr")
    if swap2["success"]:
        bridge.complete_swap(swap2["swap_id"])

    print("\n" + "─"*50)
    print("4️⃣  Swap: ETH → OTC")
    print("─"*50)
    swap3 = bridge.initiate_swap("ETH","OTC",0.1,BOB,ALICE)
    if swap3["success"]:
        bridge.complete_swap(swap3["swap_id"])

    print("\n" + "─"*50)
    print("5️⃣  Bridge Stats")
    print("─"*50)
    stats = bridge.get_stats()
    print(f"   Chains          : {' | '.join(stats['supported_chains'])}")
    print(f"   Completed Swaps : {stats['completed_swaps']}")
    print(f"   Total Volume    : Ꞵ{stats['total_volume_otc']} OTC")
    print(f"   Bridge Fee      : {stats['bridge_fee']}")

    print("\n" + "="*60)
    print("✅ OTCoin Cross-Chain Bridge berjalan sempurna!")
    print()
    print("🌉 OTCoin bisa swap dengan:")
    for c in SUPPORTED_CHAINS[1:]:
        rate = EXCHANGE_RATES.get(("OTC", c), 0)
        print(f"   OTC ↔ {c}: 1 OTC = {rate} {c}")
    print("="*60)
