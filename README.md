# 🪙 OTCoin (OTC)

> **One Transaction. All Chains.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Blockchain](https://img.shields.io/badge/Consensus-Proof%20of%20Work-orange.svg)]()
[![Supply](https://img.shields.io/badge/Total%20Supply-51%2C000%2C000%20OTC-gold.svg)]()

---

## 🌐 What is OTCoin?

**OTCoin** is an independent blockchain network designed to be a universal payment bridge — connecting Bitcoin, Ethereum, Solana, and Hyperliquid into one seamless ecosystem.

OTCoin is not a token on top of another blockchain. It is its own sovereign chain, built from the ground up with:

- ⛓️ **Independent Proof of Work blockchain**
- 🔐 **ECDSA secp256k1 cryptography** (same as Bitcoin)
- 🌉 **Cross-chain bridge** (Bitcoin, Ethereum, Solana, Hyperliquid)
- 🌍 **Fully decentralized P2P network**

---

## ⚙️ Technical Specifications

| Property | Details |
|---|---|
| **Ticker** | OTC |
| **Total Supply** | 51,000,000 OTC (hard cap) |
| **Consensus** | Proof of Work (SHA-256) |
| **Block Time** | ~10 minutes |
| **Block Reward** | 50 OTC (halving every 210,000 blocks) |
| **Cryptography** | ECDSA secp256k1 |
| **Network** | P2P WebSocket nodes |
| **Bridge Support** | Bitcoin, Ethereum, Solana, Hyperliquid |

---

## 📁 Repository Structure

```
OTCoin/
├── blockchain.py    # Core blockchain — blocks, mining, validation
├── wallet.py        # Wallet system with ECDSA cryptography
├── node.py          # P2P network node with WebSocket
├── index.html       # Official website
└── README.md        # This file
```

---

## 🚀 Quick Start

### 1. Install Requirements
```bash
pip install ecdsa websockets
```

### 2. Run the Blockchain
```bash
python blockchain.py
```

### 3. Run the Wallet
```bash
python wallet.py
```

### 4. Run a P2P Node
```bash
# First node
python node.py --port 6001

# Second node (connect to first)
python node.py --port 6002 --peers ws://localhost:6001
```

---

## 💰 Tokenomics

| Allocation | Percentage | Amount |
|---|---|---|
| Mining Rewards | 40% | 20,400,000 OTC |
| Ecosystem & Dev | 20% | 10,200,000 OTC |
| Founders & Team | 15% | 7,650,000 OTC |
| Community | 15% | 7,650,000 OTC |
| Reserve | 10% | 5,100,000 OTC |

### Halving Schedule

| Period | Block Reward |
|---|---|
| Block 0 – 210,000 | 50 OTC |
| Block 210,001 – 420,000 | 25 OTC |
| Block 420,001 – 630,000 | 12.5 OTC |
| Block 630,001+ | 6.25 OTC... |

---

## 🗺️ Roadmap

### ✅ Phase 1 — Foundation (Q1 2025)
- [x] Blockchain core (blocks, mining, validation)
- [x] Wallet system with ECDSA cryptography
- [x] P2P network node with WebSocket
- [x] Official whitepaper published
- [x] GitHub repository live

### 🔄 Phase 2 — Testnet (Q2–Q3 2025)
- [ ] Public testnet launch
- [ ] Community bug bounty program
- [ ] Independent security audit
- [ ] Desktop wallet beta release
- [ ] Official website live

### 🔜 Phase 3 — Mainnet Launch (Q4 2025)
- [ ] Genesis block — historic moment
- [ ] Public mining opens worldwide
- [ ] Block explorer launch
- [ ] First DEX listing

### 🔜 Phase 4 — Ecosystem (2026)
- [ ] Cross-chain bridge (Bitcoin & Ethereum)
- [ ] Solana & Hyperliquid integration
- [ ] CoinGecko & CoinMarketCap listing
- [ ] Mobile wallet (iOS & Android)
- [ ] Centralized exchange applications

---

## 🤝 Contributing

OTCoin is **open source** and welcomes contributions from developers worldwide.

1. Fork this repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 🔐 Security

OTCoin takes security seriously. If you discover a security vulnerability, please contact us at:

📧 **security@otcoin.io**

---

## 📬 Contact & Community

| Platform | Link |
|---|---|
| 🌐 Website | [otetcrime.github.io/OTCoin](https://otetcrime.github.io/OTCoin) |
| 🐙 GitHub | [github.com/otetcrime/OTCoin](https://github.com/otetcrime/OTCoin) |
| 📧 Email | foundation@otcoin.io |

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**© 2025 OTCoin Foundation. All Rights Reserved.**

*One Transaction. All Chains.*

⭐ Star this repository if you believe in the OTCoin vision!

</div>
