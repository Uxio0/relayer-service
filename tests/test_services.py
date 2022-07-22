import unittest

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
                4, "0x684bb3bf271db416fef707fe31050d4d79ce084e2c4281ca0219b85d5461118e"
            )
