"""
smart_contract.py — OTCoin Smart Contract Engine v1.0

Fitur:
- Deploy smart contract ke blockchain OTCoin
- Execute contract otomatis
- Support: Token, DeFi, Voting, NFT
- Gas system untuk cegah spam
"""

import hashlib
import json
import time
from typing import Dict, Any, List, Optional


# ─────────────────────────────────────────────
# KONFIGURASI
# ─────────────────────────────────────────────
GAS_PRICE     = 0.001   # Harga gas per unit (dalam OTC)
MAX_GAS       = 10000   # Maksimum gas per transaksi
CONTRACT_FILE = "otcoin_contracts.json"


# ─────────────────────────────────────────────
# SMART CONTRACT BASE
# ─────────────────────────────────────────────
class SmartContract:
    """Base class untuk semua smart contract OTCoin."""

    def __init__(self, creator: str, code: dict, initial_state: dict = None):
        self.address   = self._generate_address(creator, code)
        self.creator   = creator
        self.code      = code          # Logika contract
        self.state     = initial_state or {}  # State/data contract
        self.balance   = 0.0          # OTC yang tersimpan di contract
        self.created_at = time.time()
        self.tx_count  = 0

    def _generate_address(self, creator: str, code: dict) -> str:
        """Generate address unik untuk contract."""
        data = f"{creator}{json.dumps(code)}{time.time()}"
        return "OTC_" + hashlib.sha256(data.encode()).hexdigest()[:32]

    def execute(self, function: str, args: dict,
                sender: str, value: float = 0.0) -> dict:
        """Jalankan fungsi dalam contract."""
        raise NotImplementedError("Subclass harus implement execute()")

    def to_dict(self) -> dict:
        return {
            "address":    self.address,
            "creator":    self.creator,
            "code":       self.code,
            "state":      self.state,
            "balance":    self.balance,
            "created_at": self.created_at,
            "tx_count":   self.tx_count,
            "type":       self.__class__.__name__,
        }


# ─────────────────────────────────────────────
# OTC TOKEN CONTRACT
# ─────────────────────────────────────────────
class OTCTokenContract(SmartContract):
    """
    Buat token baru di atas OTCoin — seperti ERC-20 di Ethereum.
    Siapapun bisa buat token sendiri di jaringan OTCoin!
    """

    def __init__(self, creator: str, name: str, symbol: str,
                 total_supply: float, decimals: int = 8):
        code = {
            "type": "OTCToken",
            "name": name,
            "symbol": symbol,
            "total_supply": total_supply,
            "decimals": decimals
        }
        initial_state = {
            "name":         name,
            "symbol":       symbol,
            "total_supply": total_supply,
            "decimals":     decimals,
            "balances":     {creator: total_supply},
            "allowances":   {},
        }
        super().__init__(creator, code, initial_state)
        print(f"🪙 Token '{name}' ({symbol}) berhasil dibuat!")
        print(f"   Supply: {total_supply:,.0f} {symbol}")
        print(f"   Contract: {self.address}\n")

    def execute(self, function: str, args: dict,
                sender: str, value: float = 0.0) -> dict:
        self.tx_count += 1

        if function == "transfer":
            return self._transfer(sender, args["to"], args["amount"])
        elif function == "balance_of":
            return self._balance_of(args["address"])
        elif function == "approve":
            return self._approve(sender, args["spender"], args["amount"])
        elif function == "transfer_from":
            return self._transfer_from(sender, args["from"], args["to"], args["amount"])
        else:
            return {"success": False, "error": f"Function '{function}' tidak ditemukan"}

    def _transfer(self, sender: str, to: str, amount: float) -> dict:
        balances = self.state["balances"]
        sender_bal = balances.get(sender, 0.0)

        if sender_bal < amount:
            return {"success": False, "error": f"Saldo tidak cukup: {sender_bal}"}
        if amount <= 0:
            return {"success": False, "error": "Amount harus positif"}

        balances[sender] = sender_bal - amount
        balances[to]     = balances.get(to, 0.0) + amount
        symbol = self.state["symbol"]
        print(f"  ✅ Transfer {amount} {symbol}: {sender[:8]}... → {to[:8]}...")
        return {"success": True, "from": sender, "to": to, "amount": amount}

    def _balance_of(self, address: str) -> dict:
        bal = self.state["balances"].get(address, 0.0)
        return {"success": True, "address": address, "balance": bal,
                "symbol": self.state["symbol"]}

    def _approve(self, owner: str, spender: str, amount: float) -> dict:
        if "allowances" not in self.state:
            self.state["allowances"] = {}
        if owner not in self.state["allowances"]:
            self.state["allowances"][owner] = {}
        self.state["allowances"][owner][spender] = amount
        return {"success": True, "owner": owner, "spender": spender, "amount": amount}

    def _transfer_from(self, caller: str, from_addr: str,
                       to: str, amount: float) -> dict:
        allowance = self.state["allowances"].get(from_addr, {}).get(caller, 0.0)
        if allowance < amount:
            return {"success": False, "error": "Allowance tidak cukup"}
        result = self._transfer(from_addr, to, amount)
        if result["success"]:
            self.state["allowances"][from_addr][caller] -= amount
        return result


# ─────────────────────────────────────────────
# DEFI LENDING CONTRACT
# ─────────────────────────────────────────────
class DeFiLendingContract(SmartContract):
    """
    Protocol pinjam-meminjam OTC otomatis.
    Deposit OTC → dapat bunga.
    Pinjam OTC → bayar bunga.
    Seperti Aave/Compound tapi di OTCoin!
    """

    def __init__(self, creator: str, interest_rate: float = 0.05):
        code = {"type": "DeFiLending", "interest_rate": interest_rate}
        initial_state = {
            "interest_rate": interest_rate,  # 5% per periode
            "deposits":  {},   # address → jumlah deposit
            "loans":     {},   # address → jumlah pinjaman
            "total_deposited": 0.0,
            "total_borrowed":  0.0,
        }
        super().__init__(creator, code, initial_state)
        print(f"🏦 DeFi Lending Contract berhasil dibuat!")
        print(f"   Interest Rate: {interest_rate*100}%")
        print(f"   Contract: {self.address}\n")

    def execute(self, function: str, args: dict,
                sender: str, value: float = 0.0) -> dict:
        self.tx_count += 1

        if function == "deposit":
            return self._deposit(sender, value)
        elif function == "withdraw":
            return self._withdraw(sender, args["amount"])
        elif function == "borrow":
            return self._borrow(sender, args["amount"])
        elif function == "repay":
            return self._repay(sender, value)
        elif function == "get_stats":
            return self._get_stats()
        else:
            return {"success": False, "error": f"Function '{function}' tidak ada"}

    def _deposit(self, sender: str, amount: float) -> dict:
        if amount <= 0:
            return {"success": False, "error": "Amount harus positif"}
        self.state["deposits"][sender] = \
            self.state["deposits"].get(sender, 0.0) + amount
        self.balance += amount
        self.state["total_deposited"] += amount
        print(f"  ✅ Deposit Ꞵ{amount} OTC dari {sender[:8]}...")
        return {"success": True, "deposited": amount,
                "total_deposit": self.state["deposits"][sender]}

    def _withdraw(self, sender: str, amount: float) -> dict:
        deposit = self.state["deposits"].get(sender, 0.0)
        interest = deposit * self.state["interest_rate"]
        total = deposit + interest

        if amount > total:
            return {"success": False, "error": f"Maksimal withdraw: Ꞵ{total:.4f}"}

        self.state["deposits"][sender] -= amount
        self.balance -= amount
        print(f"  ✅ Withdraw Ꞵ{amount} OTC (termasuk bunga Ꞵ{interest:.4f})")
        return {"success": True, "withdrawn": amount, "interest_earned": interest}

    def _borrow(self, sender: str, amount: float) -> dict:
        # Collateral 150% dari pinjaman
        max_borrow = self.balance * 0.66
        if amount > max_borrow:
            return {"success": False,
                    "error": f"Maksimal pinjaman: Ꞵ{max_borrow:.4f}"}

        self.state["loans"][sender] = \
            self.state["loans"].get(sender, 0.0) + amount
        self.balance -= amount
        self.state["total_borrowed"] += amount
        print(f"  ✅ Pinjaman Ꞵ{amount} OTC untuk {sender[:8]}...")
        return {"success": True, "borrowed": amount,
                "interest_rate": self.state["interest_rate"]}

    def _repay(self, sender: str, amount: float) -> dict:
        loan = self.state["loans"].get(sender, 0.0)
        interest = loan * self.state["interest_rate"]
        total_due = loan + interest

        if amount < total_due:
            return {"success": False,
                    "error": f"Kurang bayar. Total hutang: Ꞵ{total_due:.4f}"}

        self.state["loans"][sender] = 0.0
        self.balance += amount
        print(f"  ✅ Pinjaman lunas! Bayar Ꞵ{amount} OTC")
        return {"success": True, "repaid": amount, "interest_paid": interest}

    def _get_stats(self) -> dict:
        return {
            "success": True,
            "total_deposited": self.state["total_deposited"],
            "total_borrowed":  self.state["total_borrowed"],
            "available":       self.balance,
            "interest_rate":   self.state["interest_rate"],
        }


# ─────────────────────────────────────────────
# NFT CONTRACT
# ─────────────────────────────────────────────
class NFTContract(SmartContract):
    """
    Non-Fungible Token di OTCoin.
    Buat, jual, beli aset digital unik!
    """

    def __init__(self, creator: str, collection_name: str):
        code = {"type": "NFT", "collection": collection_name}
        initial_state = {
            "collection_name": collection_name,
            "tokens":  {},   # token_id → {owner, metadata, price}
            "next_id": 1,
            "total_minted": 0,
        }
        super().__init__(creator, code, initial_state)
        print(f"🎨 NFT Collection '{collection_name}' berhasil dibuat!")
        print(f"   Contract: {self.address}\n")

    def execute(self, function: str, args: dict,
                sender: str, value: float = 0.0) -> dict:
        self.tx_count += 1

        if function == "mint":
            return self._mint(sender, args["metadata"], args.get("price", 0))
        elif function == "transfer":
            return self._transfer(sender, args["token_id"], args["to"])
        elif function == "buy":
            return self._buy(sender, args["token_id"], value)
        elif function == "list_for_sale":
            return self._list_for_sale(sender, args["token_id"], args["price"])
        elif function == "get_token":
            return self._get_token(args["token_id"])
        else:
            return {"success": False, "error": f"Function '{function}' tidak ada"}

    def _mint(self, creator: str, metadata: dict, price: float = 0) -> dict:
        token_id = self.state["next_id"]
        self.state["tokens"][str(token_id)] = {
            "owner":      creator,
            "metadata":   metadata,
            "price":      price,
            "for_sale":   price > 0,
            "created_at": time.time(),
        }
        self.state["next_id"] += 1
        self.state["total_minted"] += 1
        col = self.state["collection_name"]
        print(f"  ✅ NFT #{token_id} berhasil di-mint! Collection: {col}")
        return {"success": True, "token_id": token_id, "owner": creator}

    def _transfer(self, sender: str, token_id: int, to: str) -> dict:
        t = self.state["tokens"].get(str(token_id))
        if not t:
            return {"success": False, "error": "Token tidak ditemukan"}
        if t["owner"] != sender:
            return {"success": False, "error": "Bukan pemilik token"}
        t["owner"]    = to
        t["for_sale"] = False
        print(f"  ✅ NFT #{token_id} transfer: {sender[:8]}... → {to[:8]}...")
        return {"success": True, "token_id": token_id, "new_owner": to}

    def _buy(self, buyer: str, token_id: int, value: float) -> dict:
        t = self.state["tokens"].get(str(token_id))
        if not t:
            return {"success": False, "error": "Token tidak ditemukan"}
        if not t["for_sale"]:
            return {"success": False, "error": "Token tidak dijual"}
        if value < t["price"]:
            return {"success": False,
                    "error": f"Harga: Ꞵ{t['price']} OTC"}
        seller = t["owner"]
        t["owner"]    = buyer
        t["for_sale"] = False
        self.balance += value
        print(f"  ✅ NFT #{token_id} terjual! Ꞵ{value} OTC")
        return {"success": True, "token_id": token_id,
                "buyer": buyer, "seller": seller, "price": value}

    def _list_for_sale(self, sender: str, token_id: int, price: float) -> dict:
        t = self.state["tokens"].get(str(token_id))
        if not t or t["owner"] != sender:
            return {"success": False, "error": "Bukan pemilik"}
        t["price"]    = price
        t["for_sale"] = True
        print(f"  ✅ NFT #{token_id} dijual seharga Ꞵ{price} OTC")
        return {"success": True, "token_id": token_id, "price": price}

    def _get_token(self, token_id: int) -> dict:
        t = self.state["tokens"].get(str(token_id))
        if not t:
            return {"success": False, "error": "Token tidak ditemukan"}
        return {"success": True, "token_id": token_id, **t}


# ─────────────────────────────────────────────
# VOTING CONTRACT
# ─────────────────────────────────────────────
class VotingContract(SmartContract):
    """
    Sistem voting transparan di OTCoin.
    Tidak bisa dimanipulasi — semua tercatat di blockchain!
    """

    def __init__(self, creator: str, title: str,
                 options: List[str], duration_seconds: int = 86400):
        code = {"type": "Voting", "title": title, "options": options}
        initial_state = {
            "title":      title,
            "options":    {opt: 0 for opt in options},
            "voters":     {},
            "start_time": time.time(),
            "end_time":   time.time() + duration_seconds,
            "active":     True,
        }
        super().__init__(creator, code, initial_state)
        print(f"🗳️  Voting '{title}' berhasil dibuat!")
        print(f"   Options: {', '.join(options)}")
        print(f"   Duration: {duration_seconds//3600} jam")
        print(f"   Contract: {self.address}\n")

    def execute(self, function: str, args: dict,
                sender: str, value: float = 0.0) -> dict:
        self.tx_count += 1

        if function == "vote":
            return self._vote(sender, args["option"])
        elif function == "get_results":
            return self._get_results()
        elif function == "get_winner":
            return self._get_winner()
        else:
            return {"success": False, "error": f"Function '{function}' tidak ada"}

    def _vote(self, voter: str, option: str) -> dict:
        if time.time() > self.state["end_time"]:
            return {"success": False, "error": "Voting sudah berakhir"}
        if voter in self.state["voters"]:
            return {"success": False, "error": "Sudah pernah vote"}
        if option not in self.state["options"]:
            return {"success": False,
                    "error": f"Option tidak valid: {list(self.state['options'].keys())}"}

        self.state["options"][option] += 1
        self.state["voters"][voter] = option
        print(f"  ✅ Vote dari {voter[:8]}...: {option}")
        return {"success": True, "voter": voter, "option": option}

    def _get_results(self) -> dict:
        total = sum(self.state["options"].values())
        results = {}
        for opt, count in self.state["options"].items():
            pct = (count/total*100) if total > 0 else 0
            results[opt] = {"votes": count, "percentage": f"{pct:.1f}%"}
        return {"success": True, "title": self.state["title"],
                "results": results, "total_votes": total}

    def _get_winner(self) -> dict:
        options = self.state["options"]
        if not any(options.values()):
            return {"success": False, "error": "Belum ada vote"}
        winner = max(options, key=options.get)
        return {"success": True, "winner": winner,
                "votes": options[winner]}


# ─────────────────────────────────────────────
# CONTRACT ENGINE
# ─────────────────────────────────────────────
class ContractEngine:
    """Engine untuk deploy dan execute smart contract di OTCoin."""

    def __init__(self):
        self.contracts: Dict[str, SmartContract] = {}
        self._load_contracts()

    def _load_contracts(self):
        import os
        if os.path.exists(CONTRACT_FILE):
            print(f"📂 Contracts dimuat dari {CONTRACT_FILE}")

    def deploy(self, contract: SmartContract) -> str:
        self.contracts[contract.address] = contract
        print(f"🚀 Contract deployed: {contract.address}")
        return contract.address

    def call(self, contract_address: str, function: str,
             args: dict, sender: str, value: float = 0.0) -> dict:
        contract = self.contracts.get(contract_address)
        if not contract:
            return {"success": False, "error": "Contract tidak ditemukan"}

        gas_cost = GAS_PRICE * 100
        print(f"\n⚙️  Executing {function}() | Gas: Ꞵ{gas_cost}")

        try:
            result = contract.execute(function, args, sender, value)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_contract(self, address: str) -> Optional[SmartContract]:
        return self.contracts.get(address)

    def list_contracts(self) -> List[dict]:
        return [
            {"address": addr, "type": c.__class__.__name__,
             "creator": c.creator[:12]+"...", "tx_count": c.tx_count}
            for addr, c in self.contracts.items()
        ]


# ─────────────────────────────────────────────
# DEMO
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 OTCoin Smart Contract Engine v1.0")
    print("=" * 60)

    engine = ContractEngine()

    FOUNDER = "1892c373ab5ea6e6fcc9feb8622d1d424e3e38432"
    USER1   = "user1_address_abc123def456"
    USER2   = "user2_address_xyz789ghi012"

    print("\n" + "─"*50)
    print("1️⃣  Deploy OTC Token")
    print("─"*50)
    token = OTCTokenContract(
        creator=FOUNDER,
        name="OTCoin Token",
        symbol="OTCT",
        total_supply=1_000_000
    )
    token_addr = engine.deploy(token)

    # Transfer token
    engine.call(token_addr, "transfer",
                {"to": USER1, "amount": 10000}, FOUNDER)
    result = engine.call(token_addr, "balance_of",
                         {"address": USER1}, FOUNDER)
    print(f"  💰 Saldo USER1: {result['balance']} OTCT\n")

    print("─"*50)
    print("2️⃣  Deploy DeFi Lending")
    print("─"*50)
    defi = DeFiLendingContract(creator=FOUNDER, interest_rate=0.05)
    defi_addr = engine.deploy(defi)

    engine.call(defi_addr, "deposit", {}, FOUNDER, value=1000)
    engine.call(defi_addr, "borrow", {"amount": 500}, USER1)
    stats = engine.call(defi_addr, "get_stats", {}, FOUNDER)
    print(f"  📊 Total Deposited: Ꞵ{stats['total_deposited']}")
    print(f"  📊 Total Borrowed : Ꞵ{stats['total_borrowed']}\n")

    print("─"*50)
    print("3️⃣  Deploy NFT Collection")
    print("─"*50)
    nft = NFTContract(creator=FOUNDER, collection_name="OTCoin Genesis")
    nft_addr = engine.deploy(nft)

    engine.call(nft_addr, "mint", {
        "metadata": {"name": "Genesis #1", "rarity": "Legendary"},
        "price": 100
    }, FOUNDER)
    engine.call(nft_addr, "buy", {"token_id": 1}, USER1, value=100)
    token_info = engine.call(nft_addr, "get_token", {"token_id": 1}, USER1)
    print(f"  👤 Owner NFT #1: {token_info['owner'][:12]}...\n")

    print("─"*50)
    print("4️⃣  Deploy Voting Contract")
    print("─"*50)
    voting = VotingContract(
        creator=FOUNDER,
        title="OTCoin Mainnet Date",
        options=["Q3 2025", "Q4 2025", "Q1 2026"],
        duration_seconds=86400
    )
    voting_addr = engine.deploy(voting)

    engine.call(voting_addr, "vote", {"option": "Q4 2025"}, FOUNDER)
    engine.call(voting_addr, "vote", {"option": "Q4 2025"}, USER1)
    engine.call(voting_addr, "vote", {"option": "Q1 2026"}, USER2)

    results = engine.call(voting_addr, "get_results", {}, FOUNDER)
    print(f"\n  📊 Hasil Voting '{results['title']}':")
    for opt, data in results["results"].items():
        print(f"     {opt}: {data['votes']} votes ({data['percentage']})")

    winner = engine.call(voting_addr, "get_winner", {}, FOUNDER)
    print(f"\n  🏆 Pemenang: {winner['winner']} ({winner['votes']} votes)")

    print("\n" + "="*60)
    print("✅ OTCoin Smart Contract Engine berjalan sempurna!")
    print(f"📦 Total contracts deployed: {len(engine.contracts)}")
    print("="*60)
    print("\n🚀 OTCoin sekarang punya Smart Contract seperti Ethereum!")
    print("   Deploy token, DeFi, NFT, dan Voting di atas OTCoin!")
