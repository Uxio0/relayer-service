import pytest


@pytest.mark.parametrize("expected", [{"version": "0.0.1"}])
def test_view_about(client, expected):
    response = client.get("/about/").json
    assert expected == response


@pytest.mark.parametrize(
    "chain_id,safe_tx_hash,expected",
    [
        (
            4,
            "0x684bb3bf271db416fef707fe31050d4d79ce084e2c4281ca0219b85d5461118e",
            {
                "code": 422,
                "name": "ServiceError",
                "description": "Tx with safe-tx-hash 0x684bb3bf271db416fef707fe31050d4d79ce084e2c4281ca0219b85d5461118e was already executed on 0x31048de6de288edc6642eac933f6b0cffa9e05bee9dfaa2ad3b4ca0148178f26",
            },
        ),
        (
            4,
            "0x684bb3bf271db416fef707fe31050d4d79ce084e2c4281ca0219b85d5461118a",
            {
                "code": 422,
                "name": "ServiceError",
                "description": "Tx with safe-tx-hash 0x684bb3bf271db416fef707fe31050d4d79ce084e2c4281ca0219b85d5461118a not found",
            },
        ),
        (
            4815,
            "0x684bb3bf271db416fef707fe31050d4d79ce084e2c4281ca0219b85d5461118e",
            {
                "code": 422,
                "description": "EthereumNetwork.UNKNOWN network not supported",
                "name": "ServiceError",
            },
        ),
    ],
)
def test_view_relay(
    client, chain_id: int, safe_tx_hash: str, expected: dict[str, str | int]
):
    response = client.post(f"/v1/{chain_id}/relayed-transactions/{safe_tx_hash}/").json
    assert expected == response
