import requests
import json

from src.env_vars import API_REQUEST_TIMEOUT
from src.libs.custom_logger import get_custom_logger
from tenacity import retry, stop_after_delay, wait_fixed

logger = get_custom_logger(__name__)


class StatusNodeRPC:
    def __init__(self, port, node_name):
        self.base_url = f"http://127.0.0.1:{port}"
        self.node_name = node_name

    @retry(stop=stop_after_delay(10), wait=wait_fixed(0.1), reraise=True)
    def send_rpc_request(self, method, params=None, timeout=API_REQUEST_TIMEOUT):
        if params is None:
            params = []
        payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
        logger.debug(f"Node: {self.node_name} sends request at address: {self.base_url} with payload: {json.dumps(payload)}")

        try:
            response = requests.post(self.base_url, headers={"Content-Type": "application/json"}, data=json.dumps(payload), timeout=timeout)
            logger.debug(f"Received response: {response.text}")
            response.raise_for_status()
            assert "result" in response.json(), "Response does not contain 'result' key."
            return response.json()

        except requests.exceptions.ReadTimeout:
            error_message = f"Request to {self.base_url} usig method {method} timed out after {timeout} seconds. Node: {self.node_name}"
            logger.error(error_message)
            raise RuntimeError(error_message)

        except requests.exceptions.RequestException as e:
            logger.error(f"An error occurred: {str(e)}")
            raise
