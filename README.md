# Multi-Chain Wallet Validator & USD Balance Evaluator

A high-performance Python toolkit and CLI utility for validating, profiling, and calculating real-time USD balances for **Ethereum** and **Solana** wallet addresses.

## 🚀 Key Features

- **Multi-Chain Support:** Auto-detects EVM (`0x...`) and Solana (Base58) address formats.
- **On-Chain Profiling:** Queries Etherscan and Solana RPC/Solscan for native balances and transaction counts.
- **Live FX Conversion:** Fetches real-time ETH/USD and SOL/USD spot prices from CoinGecko with monotonic TTL caching.
- **Concurrent Batch Processing:** Validates hundreds of addresses in seconds using `ThreadPoolExecutor`.
- **Threshold Filtering:** Filter out dust/empty wallets with `--min-usd`.

## 📦 Installation

```bash
pip install -r requirements.txt
cp .env.example .env
```

## 🛠️ Usage

### 1. Command Line (CLI)

Single or multiple addresses:
```bash
python cli.py 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
```

Batch evaluation from file with USD balance threshold:
```bash
python cli.py -f wallets.txt --min-usd 100.0 --workers 16
```

### 2. Python API

```python
from blockchain_api import BlockchainValidator
from usd_prices import get_eth_sol_usd

validator = BlockchainValidator(max_workers=8)
wallets = ["0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"]

results = validator.validate_batch(wallets)
for w in results:
    print(f"Address: {w.address} | Chain: {w.chain} | Balance: {w.balance}")
```
