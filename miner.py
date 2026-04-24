"""
miner.py — OTCoin Miner
Mining OTC terus menerus ke wallet address kamu!
"""

import time
from blockchain import Blockchain

# ─────────────────────────────────────────────
# GANTI DENGAN WALLET ADDRESS KAMU!
# ─────────────────────────────────────────────
MINER_ADDRESS = "1892c373ab5ea6e6fcc9feb8622d1d424e3e38432"

print("=" * 55)
print("⛏️  OTCoin Miner Started!")
print("=" * 55)
print(f"💳 Mining ke wallet : {MINER_ADDRESS}")
print(f"🌍 Network          : OTCoin Mainnet")
print("=" * 55 + "\n")

bc = Blockchain()
block_count = 0
start_time = time.time()

while True:
    try:
        # Mining blok baru
        new_block = bc.mine_pending_transactions(MINER_ADDRESS)
        block_count += 1

        # Hitung saldo
        saldo = bc.get_balance(MINER_ADDRESS)
        elapsed = time.time() - start_time

        print(f"✅ Blok #{new_block.index} berhasil!")
        print(f"💰 Saldo kamu : {saldo:,.1f} OTC")
        print(f"⏱️  Uptime     : {elapsed/60:.1f} menit")
        print(f"📦 Total blok : {block_count}")
        print("-" * 40)

        time.sleep(1)

    except KeyboardInterrupt:
        print("\n⛏️  Mining dihentikan!")
        print(f"💰 Total OTC didapat: {bc.get_balance(MINER_ADDRESS):,.1f} OTC")
        break
    except Exception as e:
        print(f"⚠️  Error: {e}")
        time.sleep(5)
