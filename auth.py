import json
import time
import uuid
import base64
import logging

import base58
import jwt
import requests
from nacl.signing import SigningKey
from eth_account import Account
from eth_account.messages import encode_defunct

import config

logger = logging.getLogger(__name__)


class StandXAuth:
    def __init__(self):
        self.account = Account.from_key(config.bscPrivateKey)
        self.address = self.account.address
        if self.address.lower() != config.bscAddress.lower():
            logger.warning(
                "Configured address %s != derived address %s, using derived",
                config.bscAddress, self.address,
            )
        self.signingKey = SigningKey.generate()
        self.verifyKey = self.signingKey.verify_key
        self.requestId = base58.b58encode(bytes(self.verifyKey)).decode()
        self.token = None
        self.tokenExpiry = 0

    def login(self):
        signedData = self._prepareSignin()
        message = self._parseMessage(signedData)
        signature = self._signMessage(message)
        self.token = self._getToken(signature, signedData)
        self.tokenExpiry = time.time() + 604800 - 60
        logger.info("Login successful, token expires in 7 days")

    def _prepareSignin(self) -> str:
        logger.debug("Prepare signin: address=%s, requestId=%s", self.address, self.requestId)
        resp = requests.post(
            f"{config.AUTH_URL}/v1/offchain/prepare-signin",
            params={"chain": config.CHAIN},
            json={"address": self.address, "requestId": self.requestId},
            timeout=10,
        )
        if resp.status_code != 200:
            logger.error("Prepare signin failed [%d]: %s", resp.status_code, resp.text)
        resp.raise_for_status()
        return resp.json()["signedData"]

    def _parseMessage(self, signedData: str) -> str:
        payload = jwt.decode(signedData, options={"verify_signature": False})
        logger.debug("SIWE message to sign:\n%s", payload["message"])
        return payload["message"]

    def _signMessage(self, message: str) -> str:
        msgEncoded = encode_defunct(text=message)
        signed = self.account.sign_message(msgEncoded)
        sigHex = signed.signature.hex()
        if not sigHex.startswith("0x"):
            sigHex = f"0x{sigHex}"
        logger.debug("Signature: %s...%s", sigHex[:10], sigHex[-6:])
        return sigHex

    def _getToken(self, signature: str, signedData: str) -> str:
        logger.debug("Login payload: signature=%s..., signedData=%s...",
                      signature[:16], signedData[:32])
        resp = requests.post(
            f"{config.AUTH_URL}/v1/offchain/login",
            params={"chain": config.CHAIN},
            json={
                "signature": signature,
                "signedData": signedData,
                "expiresSeconds": 604800,
            },
            timeout=10,
        )
        if resp.status_code != 200:
            logger.error("Login failed [%d]: %s", resp.status_code, resp.text)
        resp.raise_for_status()
        return resp.json()["token"]

    def ensureAuth(self):
        if not self.token or time.time() > self.tokenExpiry:
            self.login()

    def getHeaders(self) -> dict:
        self.ensureAuth()
        return {"Authorization": f"Bearer {self.token}"}

    def getSignedRequest(self, payload: dict) -> tuple[dict, str]:
        self.ensureAuth()
        reqId = str(uuid.uuid4())
        timestamp = str(int(time.time() * 1000))
        payloadStr = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        message = f"v1,{reqId},{timestamp},{payloadStr}"
        signed = self.signingKey.sign(message.encode())
        sig = base64.b64encode(signed.signature).decode()
        headers = {
            "Authorization": f"Bearer {self.token}",
            "x-request-sign-version": "v1",
            "x-request-id": reqId,
            "x-request-timestamp": timestamp,
            "x-request-signature": sig,
            "Content-Type": "application/json",
        }
        return headers, payloadStr
