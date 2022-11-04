import unittest

from eth_typing import HexStr

from gnosis.eth import EthereumClient, EthereumNetwork

from flaskr.services import get_ethereum_client, relay_transaction


class TestServices(unittest.TestCase):
    def test_get_ethereum_client(self):
        with self.assertRaises(ValueError):
            get_ethereum_client(EthereumNetwork.KOVAN)

        ethereum_client = get_ethereum_client(EthereumNetwork.XDAI)
        self.assertIsInstance(ethereum_client, EthereumClient)
        # Must be cached
        self.assertEqual(get_ethereum_client(EthereumNetwork.XDAI), ethereum_client)

    def test_relay_transaction(self):
        with self.assertRaisesRegex(
            ValueError, "Tx with safe-tx-hash .* was already executed on .*"
        ):
            relay_transaction(
                5,
                HexStr(
                    "0x2094d7db07419c03f640f3f904b5e56206e89b3b2bbf2dd53bdb4e5de3ec7c27"
                ),
            )
