import os
from functools import cache
from typing import Optional, Tuple

from eth_account import Account
from eth_account.signers.local import LocalAccount
from eth_typing import URI, ChecksumAddress, HexAddress, HexStr
from hexbytes import HexBytes
from web3.exceptions import BadFunctionCallOutput, ContractLogicError
from web3.types import Wei

from gnosis.eth import EthereumClient, EthereumNetwork
from gnosis.eth.constants import NULL_ADDRESS
from gnosis.safe import SafeTx
from gnosis.safe.api import TransactionServiceApi

from flaskr.abis import RELAYER_CONTRACT_ABI

RELAYER_CONTRACT_ADDRESS = ChecksumAddress(
    HexAddress(HexStr("0xeEB8eFAd68491066B5c4150112645190430e0e05"))
)
RELAYER_ACCOUNT: LocalAccount = Account.from_key(
    os.getenv(
        "PRIVATE_KEY",
        "0x4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d",
    )
)


@cache
def get_ethereum_client(ethereum_network: EthereumNetwork) -> EthereumClient:
    networks_with_node_url = {
        EthereumNetwork.RINKEBY: URI("https://rpc.ankr.com/eth_rinkeby"),
        EthereumNetwork.GOERLI: URI("https://rpc.ankr.com/eth_goerli"),
        EthereumNetwork.XDAI: URI("https://rpc.ankr.com/gnosis"),
    }

    node_url = networks_with_node_url.get(ethereum_network)
    if not node_url:
        raise ValueError(f"{ethereum_network} network not supported")

    return EthereumClient(node_url)


def get_transaction(
    chain_id: int, safe_tx_hash: HexStr
) -> Tuple[SafeTx, Optional[HexBytes]]:
    ethereum_network = EthereumNetwork(chain_id)
    ethereum_client = get_ethereum_client(ethereum_network)
    transaction_service_api = TransactionServiceApi(
        ethereum_network, ethereum_client=ethereum_client
    )
    return transaction_service_api.get_safe_transaction(safe_tx_hash)


def relay_transaction(chain_id: int, safe_tx_hash: HexStr) -> HexBytes:
    safe_tx, tx_hash = get_transaction(chain_id, safe_tx_hash)
    if not safe_tx:
        raise ValueError(f"Tx with safe-tx-hash {safe_tx_hash} not found")
    if tx_hash:
        raise ValueError(
            f"Tx with safe-tx-hash {safe_tx_hash} was already executed on {tx_hash.hex()}"
        )

    # Build execTransaction data
    if not safe_tx.call():
        raise ValueError(f"Tx with safe-tx-hash {safe_tx_hash} cannot be executed")

    function_data = safe_tx.w3_tx.build_transaction({"gas": 0, "gasPrice": 0})["data"]
    # Strip selector from data
    function_data = HexBytes(function_data)[4:].hex()

    ethereum_network = EthereumNetwork(chain_id)
    ethereum_client = get_ethereum_client(ethereum_network)

    relayer_contract = ethereum_client.w3.eth.contract(
        RELAYER_CONTRACT_ADDRESS, abi=RELAYER_CONTRACT_ABI
    )

    max_priority_fee = ethereum_client.w3.eth.max_priority_fee
    max_fee_per_gas = max_priority_fee + (
        2 * ethereum_client.w3.eth.get_block("latest")["baseFeePerGas"]
    )
    try:
        # If `maxFeePerGas` and `maxPriorityFeePerGas` are not set, `gas estimation will fail`
        relayer_tx = relayer_contract.functions.relay(
            safe_tx.safe_address, function_data, NULL_ADDRESS
        ).build_transaction(
            {
                "from": RELAYER_ACCOUNT.address,
                "maxFeePerGas": Wei(max_fee_per_gas),
                "maxPriorityFeePerGas": max_priority_fee,
            }
        )
    except (ContractLogicError, BadFunctionCallOutput, ValueError):
        raise ValueError(f"Tx with safe-tx-hash {safe_tx_hash} cannot be relayed")

    relayer_tx["nonce"] = ethereum_client.get_nonce_for_account(RELAYER_ACCOUNT.address)
    signed_transaction = RELAYER_ACCOUNT.sign_transaction(relayer_tx)
    return ethereum_client.send_raw_transaction(signed_transaction.rawTransaction)
