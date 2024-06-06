import requests
import json

from src.libs.custom_logger import get_custom_logger


logger = get_custom_logger(__name__)


class StatusNodeRPC:
    def __init__(self, port):
        self.base_url = f"http://127.0.0.1:{port}"

    def send_rpc_request(self, method, params=None):
        if params is None:
            params = []
        payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
        logger.debug(f"Sending RPC request: {json.dumps(payload)}")
        response = requests.post(self.base_url, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
        logger.debug(f"Received response: {response.text}")
        return response.json()
