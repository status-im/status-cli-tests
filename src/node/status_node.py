import asyncio
import os
import random
import shutil
import signal
import string
import subprocess
import re
import threading
import time
from tenacity import retry, stop_after_delay, wait_fixed

from src.data_storage import DS
from src.libs.common import delay
from src.libs.custom_logger import get_custom_logger
from src.node.rpc_client import StatusNodeRPC

logger = get_custom_logger(__name__)


class StatusNode:
    def __init__(self, name=None, port=None, pubkey=None):
        try:
            os.remove(f"{name}.log")
        except:
            pass
        self.name = self.random_node_name() if not name else name.lower()
        self.port = str(random.randint(1024, 65535)) if not port else port
        self.pubkey = pubkey
        self.process = None
        self.log_thread = None
        self.capture_logs = True
        self.logs = []
        self.pid = None

    def start(self, capture_logs=True):
        self.capture_logs = capture_logs
        command = ["./status-cli", "serve", "-n", self.name, "-p", self.port]
        logger.info(f"Starting node with command: {command}")
        if self.pubkey:
            command += ["-a", self.pubkey]

        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        self.pid = self.process.pid
        if self.capture_logs:
            self._capture_logs()
        self.api = StatusNodeRPC(self.port, self.name)
        DS.nodes.append(self)

    def serve_account(self, key_uuid):
        command = ["./status-cli", "serve-account", "-n", self.name, "-kid", key_uuid]
        logger.info(f"Serving node with command: {command}")
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        self._capture_logs()
        self.api = StatusNodeRPC(self.port, self.name)
        DS.nodes.append(self)

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
        delay(2)  # Allow some time for the node to start and generate output

    def stop(self, remove_local_data=True):
        if self.process:
            logger.info(f"Stopping node with name: {self.name}")
            self.process.kill()
            if self.capture_logs:
                self.log_thread.join()  # Ensure log thread finishes
            node_dir = f"test-{self.name}"
            if remove_local_data and os.path.exists(node_dir):
                try:
                    shutil.rmtree(node_dir)
                except Exception as ex:
                    logger.warning(f"Couldn't delete node dir {node_dir} because of {str(ex)}")
            self.process = None

    def pause_process(self):
        if self.pid:
            logger.info(f"Pausing node with pid: {self.pid}")
            os.kill(self.pid, signal.SIGTSTP)

    def resume_process(self):
        if self.pid:
            logger.info(f"Resuming node with pid: {self.pid}")
            os.kill(self.pid, signal.SIGCONT)

    def clear_logs(self):
        log_name = f"{self.name}.log"
        if os.path.exists(log_name):
            try:
                os.remove(log_name)
            except Exception as ex:
                logger.warning(f"Couldn't delete log {log_name}.log because of {str(ex)}")

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
        pubkey = self.search_logs(regex_pattern=r"public key: (\b0x[0-9a-fA-F]+\b)")
        assert pubkey is not None, f"{self.name}'s public key was not found."
        return pubkey

    @retry(stop=stop_after_delay(20), wait=wait_fixed(0.1), reraise=True)
    def wait_fully_started(self):
        assert self.search_logs(string="retrieve messages...")

    def wait_for_logs(self, strings=None, timeout=10):
        if not isinstance(strings, list):
            raise ValueError("strings must be a list")
        start_time = time.time()
        while time.time() - start_time < timeout:
            all_found = True
            for string in strings:
                logs = self.search_logs(string=string)
                if not logs:  # If any string is not found
                    all_found = False
                    break
            if all_found:
                return True
            delay(0.5)
        return False  # Return False if not all logs were found within the timeout period

    async def wait_for_logs_async(self, strings=None, timeout=10):
        if not isinstance(strings, list):
            raise ValueError("strings must be a list")
        start_time = time.time()
        while time.time() - start_time < timeout:
            all_found = True
            for string in strings:
                logs = self.search_logs(string=string)
                if not logs:  # If any string is not found
                    all_found = False
                    break
            if all_found:
                return True
            await asyncio.sleep(0.5)  # Use asyncio.sleep for non-blocking delay
        return False  # Return False if not all logs were found within the timeout period

    def waku_info(self):
        return self.api.send_rpc_request("waku_info")

    def send_contact_request(self, pubkey, message):
        params = [{"id": pubkey, "message": message}]
        return self.api.send_rpc_request("wakuext_sendContactRequest", params)

    def send_message(self, pubkey, message):
        params = [{"id": pubkey, "message": message}]
        return self.api.send_rpc_request("wakuext_sendOneToOneMessage", params)

    def create_group_chat_with_members(self, pubkey_list, group_chat_name):
        if not isinstance(pubkey_list, list):
            raise TypeError("pubkey_list needs to be list")
        params = [None, group_chat_name, pubkey_list]
        return self.api.send_rpc_request("wakuext_createGroupChatWithMembers", params)

    def send_group_chat_message(self, group_id, message):
        params = [{"id": group_id, "message": message}]
        return self.api.send_rpc_request("wakuext_sendGroupChatMessage", params)

    def create_community(self, name):
        params = [{"membership": 3, "name": name, "color": "#ffffff", "description": name}]
        return self.api.send_rpc_request("wakuext_createCommunity", params)

    def set_community_shard(self, community_id, index=128, private_key=None):
        params = [{"communityId": community_id, "shard": {"cluster": 16, "index": index}}]
        if private_key is not None:
            params[0]["shard"]["privateKey"] = private_key
        return self.api.send_rpc_request("wakuext_setCommunityShard", params)

    @retry(stop=stop_after_delay(30), wait=wait_fixed(0.1), reraise=True)
    # wakuext_fetchCommunity times out sometimes so that's why we need this retry mechanism
    def fetch_community(self, community_key):
        params = [{"communityKey": community_key, "waitForResponse": True, "tryDatabase": True}]
        return self.api.send_rpc_request("wakuext_fetchCommunity", params, timeout=10)

    def request_to_join_community(self, community_id):
        params = [{"communityId": community_id, "addressesToReveal": ["fakeaddress"], "airdropAddress": "fakeaddress"}]
        return self.api.send_rpc_request("wakuext_requestToJoinCommunity", params)

    def accept_request_to_join_community(self, request_to_join_id):
        params = [{"id": request_to_join_id}]
        return self.api.send_rpc_request("wakuext_acceptRequestToJoinCommunity", params)

    def send_community_chat_message(self, chat_id, message):
        params = [{"chatId": chat_id, "text": message, "contentType": 1}]
        return self.api.send_rpc_request("wakuext_sendChatMessage", params)

    def leave_community(self, community_id):
        params = [community_id]
        return self.api.send_rpc_request("wakuext_leaveCommunity", params)

    def random_node_name(self, length=10):
        allowed_chars = string.ascii_lowercase + string.digits + "_-"
        return "".join(random.choice(allowed_chars) for _ in range(length))
