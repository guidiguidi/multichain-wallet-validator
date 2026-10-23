#!/usr/bin/env python3
"""
Multi-Chain Wallet Validator & USD Balance Evaluator
Supports Ethereum (EVM) and Solana.
"""
import sys
import os
import argparse
import requests
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

from blockchain_api import BlockchainValidator, WalletInfo
from usd_prices import get_eth_sol_usd


def fetch_eth_rpc_balance(address: str) -> Optional[float]:
    """Fallback to public Ethereum RPC when no Etherscan key is provided."""
    try:
        url = "https://ethereum-rpc.publicnode.com"
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getBalance",
            "params": [address, "latest"],
            "id": 1
        }
        res = requests.post(url, json=payload, timeout=8).json()
        wei = int(res.get("result", "0x0"), 16)
        return wei / 1e18
    except Exception:
        return None


def fetch_sol_rpc_balance(address: str) -> Optional[float]:
    """Fallback to public Solana RPC when no Solscan key is provided."""
    try:
        url = "https://api.mainnet-beta.solana.com"
        payload = {
            "jsonrpc": "2.0",
            "method": "getBalance",
            "params": [address],
            "id": 1
        }
        res = requests.post(url, json=payload, timeout=8).json()
        lamports = res.get("result", {}).get("value", 0)
        return lamports / 1e9
    except Exception:
        return None


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate Ethereum & Solana wallet addresses and calculate live USD valuations."
    )
    parser.add_argument("addresses", nargs="*", help="Wallet addresses to validate")
    parser.add_argument("-f", "--file", help="File with wallet addresses (one per line)")
    parser.add_argument("-w", "--workers", type=int, default=8, help="Concurrent worker threads (default: 8)")
    parser.add_argument("--min-usd", type=float, default=0.0, help="Filter out wallets with balance below USD threshold")
    return parser.parse_args()


def validate_single_address(addr: str, validator: BlockchainValidator) -> Dict[str, Any]:
    chain = "ethereum" if addr.startswith("0x") else "solana"
    info = validator.validate_wallet(addr, chain)

    balance_float = 0.0
    if info.exists and info.balance:
        try:
            balance_float = float(info.balance)
        except ValueError:
            pass
    elif not info.exists:
        # Fallback to direct public RPC nodes
        if chain == "ethereum":
            rpc_bal = fetch_eth_rpc_balance(addr)
            if rpc_bal is not None:
                info.exists = True
                info.balance = f"{rpc_bal:.4f}"
                balance_float = rpc_bal
        elif chain == "solana":
            rpc_bal = fetch_sol_rpc_balance(addr)
            if rpc_bal is not None:
                info.exists = True
                info.balance = f"{rpc_bal:.4f}"
                balance_float = rpc_bal

    return {
        "address": addr,
        "chain": chain,
        "exists": info.exists,
        "balance": info.balance or "0.0",
        "balance_float": balance_float,
        "tx_count": info.transaction_count,
        "error": info.error
    }


def main():
    args = parse_args()
    addresses: List[str] = list(args.addresses)

    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File '{args.file}' not found.")
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if line and not line.startswith("#"):
                    addresses.append(line)

    if not addresses:
        print("Usage: python cli.py <address1> <address2> ... or python cli.py -f <addresses.txt>")
        sys.exit(1)

    print(f"[*] Validating {len(addresses)} wallet address(es) across Ethereum & Solana...")

    etherscan_key = os.getenv("ETHERSCAN_API_KEY")
    solana_key = os.getenv("SOLSCAN_API_KEY")
    validator = BlockchainValidator(
        etherscan_key=etherscan_key,
        solana_api_key=solana_key
    )

    prices = get_eth_sol_usd()
    eth_usd = prices[0] if prices else 0.0
    sol_usd = prices[1] if prices else 0.0

    print(f"[*] Live Spot Rates: ETH = ${eth_usd:,.2f} | SOL = ${sol_usd:,.2f}\n")

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda a: validate_single_address(a, validator), addresses))

    qualified_count = 0
    print(f"{'Address':<44} | {'Chain':<8} | {'Balance':<14} | {'USD Value':<12} | {'Txs':<6}")
    print("-" * 92)

    for r in results:
        addr = r["address"]
        chain = r["chain"].upper()
        bal_str = r["balance"]
        tx_count = str(r["tx_count"] if r["tx_count"] is not None else "-")

        usd_val = 0.0
        if r["chain"] == "ethereum":
            usd_val = r["balance_float"] * eth_usd
        elif r["chain"] == "solana":
            usd_val = r["balance_float"] * sol_usd

        if usd_val < args.min_usd:
            continue

        qualified_count += 1
        print(f"{addr:<44} | {chain:<8} | {bal_str:<14} | ${usd_val:>10,.2f} | {tx_count:<6}")

    print("-" * 92)
    print(f"[+] Total Qualified Wallets: {qualified_count} / {len(addresses)}")


if __name__ == "__main__":
    main()
