import os
import subprocess
import re
import threading
import time
from tenacity import retry, stop_after_delay, wait_fixed

from src.libs.custom_logger import get_custom_logger
from src.node.rpc_client import StatusNodeRPC

logger = get_custom_logger(__name__)

class StatusNode:
    def __init__(self, name, port, pubkey=None):
        try:
            os.remove(f"{name}.log")
        except:
            pass
        self.name = name
        self.port = port
        self.pubkey = pubkey
        self.process = None
        self.log_thread = None
        self.logs = []

    def start(self):
        command = ['./status-cli', 'serve', '-n', self.name, '-p', self.port]
        logger.info(f"Starting node with command: {command}")
        if self.pubkey:
            command += ['-a', self.pubkey]
        
        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        self._capture_logs()
        self.api = StatusNodeRPC(self.port)

    def _capture_logs(self):
        def read_output(process, logs):
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                logs.append(line.strip())
                logger.debug(f"{self.name.upper()} - {line.strip()}")

        self.log_thread = threading.Thread(target=read_output, args=(self.process, self.logs))
        self.log_thread.start()
        time.sleep(2)  # Allow some time for the node to start and generate output

    def stop(self):
        if self.process:
            logger.info(f"Stopping node with name: {self.name}")
            self.process.kill()
            self.log_thread.join()  # Ensure log thread finishes

    def search_logs(self, string=None, regex_pattern=None):
        if string:
            for log in self.logs:
                if string in log:
                    return log
        if regex_pattern:
            regex = re.compile(regex_pattern)
            for log in self.logs:
                match = regex.search(log)
                if match:
                    return match.group(1)
        return None

    @retry(stop=stop_after_delay(10), wait=wait_fixed(0.1), reraise=True)
    def get_pubkey(self):
        pubkey = self.search_logs(regex_pattern=r'public key: (\b0x[0-9a-fA-F]+\b)')
        assert pubkey is not None, f"{self.name}'s public key was not found."
        return pubkey

    @retry(stop=stop_after_delay(10), wait=wait_fixed(0.1), reraise=True)
    def wait_fully_started(self):
        assert self.search_logs(string="retrieve messages...")

    def waku_info(self):
        return self.api.send_rpc_request("waku_info")

    def send_contact_request(self, pubkey, message):
        params = [{"id": pubkey, "message": message}]
        return self.api.send_rpc_request("wakuext_sendContactRequest", params)

    def send_message(self, pubkey, message):
        params = [{"id": pubkey, "message": message}]
        return self.api.send_rpc_request("wakuext_sendOneToOneMessage", params)