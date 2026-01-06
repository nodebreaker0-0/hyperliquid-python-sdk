"""
Example: Send a `validatorL1Vote` action signed with a Ledger (v-key) using the
Hyperliquid Python SDK.

Prereqs:
- pip : `python3 -m venv .venv && source .venv/bin/activate`
- Install deps: `pip install hyperliquid-python-sdk ledgereth eth-account msgpack`
- Ledger Ethereum app open, Blind signing/EIP-712 enabled.
"""

from eth_account._utils import encode_typed_data
from ledgereth.messages import sign_typed_data_draft

from hyperliquid.api import API
from hyperliquid.utils.constants import MAINNET_API_URL
from hyperliquid.utils.signing import action_hash, construct_phantom_agent, get_timestamp_ms, l1_payload

# Adjust derivation path if you use a different account on Ledger.
LEDGER_PATH = "44'/60'/0'/0/0"


def sign_with_ledger_eip712_hash(typed_data: dict, derivation_path: str) -> dict:
    """
    Ledgereth 0.10 uses sign_typed_data_draft(domain_hash, message_hash).
    We derive those from the EIP-712 typed data using eth-account helpers.
    """
    domain_hash = encode_typed_data.hash_domain(typed_data["domain"])
    # eth-account expects message types without the EIP712Domain entry.
    message_types = {k: v for k, v in typed_data["types"].items() if k != "EIP712Domain"}
    message_hash = encode_typed_data.hash_eip712_message(message_types, typed_data["message"])
    signed = sign_typed_data_draft(domain_hash, message_hash, sender_path=derivation_path)
    return {"r": hex(signed.r), "s": hex(signed.s), "v": signed.v}


def main():
    # For Testnet, swap MAINNET_API_URL for constants.TESTNET_API_URL.
    api = API(MAINNET_API_URL)
    is_mainnet = api.base_url == MAINNET_API_URL
    nonce = get_timestamp_ms()

    # The action you want to send (same shape you used with hl-node).
    action = {"type": "validatorL1Vote", "D": "FXS"}

    # Build the same L1 payload/signature used by Exchange.sign_l1_action.
    action_digest = action_hash(action, vault_address=None, nonce=nonce, expires_after=None)
    phantom_agent = construct_phantom_agent(action_digest, is_mainnet=is_mainnet)
    typed = l1_payload(phantom_agent)

    signature = sign_with_ledger_eip712_hash(typed, LEDGER_PATH)

    # Submit to /exchange. vaultAddress/expiresAfter are unused for this action.
    payload = {
        "action": action,
        "nonce": nonce,
        "signature": signature,
        "vaultAddress": None,
        "expiresAfter": None,
    }
    resp = api.post("/exchange", payload)
    print(resp)


if __name__ == "__main__":
    main()
