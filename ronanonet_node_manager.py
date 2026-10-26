import os
import hashlib
from web3 import Web3
from eth_account import Account

# ==========================================
# CONFIGURARE NOD & BLOCKCHAIN
# ==========================================
RPC_URL = os.getenv("WEB3_PROVIDER_URI", "https://rpc-amoy.polygon.technology/")  # Exemplu: Polygon Amoy Testnet
CONTRACT_ADDRESS = os.getenv("RONANONET_CONTRACT_ADDRESS", "0xYourContractAddressHere")
ADMIN_PRIVATE_KEY = os.getenv("ADMIN_PRIVATE_KEY", "0xYourAdminPrivateKeyHere")

# ABI-ul contractului RONANONETNode (extras direct din Solidity-ul tău)
CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "string", "name": "_name", "type": "string"},
            {"internalType": "string", "name": "_location", "type": "string"},
            {"internalType": "uint256", "name": "_totalShares", "type": "uint256"}
        ],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "_investor", "type": "address"},
            {"internalType": "uint256", "name": "_amount", "type": "uint256"}
        ],
        "name": "assignShares",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "_sampleHash", "type": "bytes32"},
            {"internalType": "string", "name": "_analysisType", "type": "string"}
        ],
        "name": "recordAudit",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "distributeRevenue",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "nodeName",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "nodeLocation",
        "outputs": [{"internalType": "string", "name": "", "type": "string"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalAuditsCompleted",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

class RONANONETNodeManager:
    def __init__(self, rpc_url, contract_address, private_key):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError(f"Nu s-a putut realiza conexiunea la nodul RPC: {rpc_url}")
        
        self.account = Account.from_key(private_key)
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=CONTRACT_ABI
        )
        print(f"[+] Conectat cu succes la blockchain. Cont operator: {self.account.address}")

    def compute_sample_hash(self, file_path: str) -> bytes:
        """Generează un hash SHA-256 criptografic pentru fișierul brut FE-SEM / EDS."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.digest()

    def assign_shares(self, investor_address: str, amount: int):
        """Alocă acțiuni unui investitor nou sau existent (doar owner-ul)."""
        nonce = self.w3.eth.get_transaction_count(self.account.address)
        
        txn = self.contract.functions.assignShares(
            Web3.to_checksum_address(investor_address),
            amount
        ).build_transaction({
            'from': self.account.address,
            'nonce': nonce,
            'gas': 100000,
            'gasPrice': self.w3.eth.gas_price
        })

        signed_txn = self.w3.eth.account.sign_transaction(txn, private_key=self.account.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(f"[+] Tranzacție trimisă (assignShares). Hash: {tx_hash.hex()}")
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"[✔] Acțiuni alocate cu succes în blocul {receipt.blockNumber}")

    def record_audit(self, file_path: str, analysis_type: str, fee_in_wei: int):
        """Calculează hash-ul probei SEM și înregistrează auditul pe blockchain."""
        sample_hash_bytes = self.compute_sample_hash(file_path)
        print(f"[i] Hash SHA-256 generat pentru {file_path}: 0x{sample_hash_bytes.hex()}")

        nonce = self.w3.eth.get_transaction_count(self.account.address)
        
        txn = self.contract.functions.recordAudit(
            sample_hash_bytes,
            analysis_type
        ).build_transaction({
            'from': self.account.address,
            'value': fee_in_wei,
            'nonce': nonce,
            'gas': 200000,
            'gasPrice': self.w3.eth.gas_price
        })

        signed_txn = self.w3.eth.account.sign_transaction(txn, private_key=self.account.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(f"[+] Tranzacție înregistrare audit trimisă. Hash: {tx_hash.hex()}")
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"[✔] Audit înregistrat cu succes on-chain în blocul {receipt.blockNumber}")

    def distribute_revenue(self):
        """Declanșează distribuirea automată a veniturilor contractului către acționari."""
        nonce = self.w3.eth.get_transaction_count(self.account.address)
        
        txn = self.contract.functions.distributeRevenue().build_transaction({
            'from': self.account.address,
            'nonce': nonce,
            'gas': 300000,
            'gasPrice': self.w3.eth.gas_price
        })

        signed_txn = self.w3.eth.account.sign_transaction(txn, private_key=self.account.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        print(f"[+] Tranzacție distribuire venituri trimisă. Hash: {tx_hash.hex()}")
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        print(f"[✔] Dividende distribuite cu succes în blocul {receipt.blockNumber}")

    def get_node_info(self):
        """Interoghează starea curentă a nodului de la distanță."""
        name = self.contract.functions.nodeName().call()
        location = self.contract.functions.nodeLocation().call()
        audits = self.contract.functions.totalAuditsCompleted().call()
        balance = self.w3.eth.get_balance(self.contract.address)

        print(f"--- Stare Nod RO-NANO-NET ---")
        print(f"Nume Nod: {name}")
        print(f"Locație: {location}")
        print(f"Audituri finalizate: {audits}")
        print(f"Sold contract (ETH/POL): {self.w3.from_wei(balance, 'ether')}")


# Exemplu de utilizare (dacă este rulat direct)
if __name__ == "__main__":
    # nod_manager = RONANONETNodeManager(RPC_URL, CONTRACT_ADDRESS, ADMIN_PRIVATE_KEY)
    # nod_manager.get_node_info()
    pass
