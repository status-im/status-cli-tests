from contextlib import contextmanager
import inspect
import os
import subprocess
import pytest
from src.libs.common import delay
from src.libs.custom_logger import get_custom_logger
from src.node.status_node import StatusNode
from datetime import datetime
from tenacity import retry, stop_after_delay, wait_fixed

logger = get_custom_logger(__name__)


class StepsCommon:
    @pytest.fixture(scope="function", autouse=False)
    def start_1_node(self):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        self.first_node = StatusNode(name="first_node")
        self.first_node.start()
        self.first_node.wait_fully_started()
        self.first_node_pubkey = self.first_node.get_pubkey()

    @pytest.fixture(scope="function", autouse=False)
    def start_2_nodes(self):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        self.first_node = StatusNode(name="first_node")
        self.first_node.start()
        self.second_node = StatusNode(name="second_node")
        self.second_node.start()
        self.first_node.wait_fully_started()
        self.second_node.wait_fully_started()
        self.first_node_pubkey = self.first_node.get_pubkey()
        self.second_node_pubkey = self.second_node.get_pubkey()

    @contextmanager
    def add_latency(self):
        logger.debug("Entering context manager: add_latency")
        subprocess.Popen("sudo tc qdisc add dev eth0 root netem delay 1s 100ms distribution normal", shell=True)
        try:
            yield
        finally:
            logger.debug(f"Exiting context manager: add_latency")
            subprocess.Popen("sudo tc qdisc del dev eth0 root", shell=True)

    @contextmanager
    def add_packet_loss(self):
        logger.debug("Entering context manager: add_packet_loss")
        subprocess.Popen("sudo tc qdisc add dev eth0 root netem loss 50%", shell=True)
        try:
            yield
        finally:
            logger.debug(f"Exiting context manager: add_packet_loss")
            subprocess.Popen("sudo tc qdisc del dev eth0 root netem", shell=True)

    @contextmanager
    def add_low_bandwith(self):
        logger.debug("Entering context manager: add_low_bandwith")
        subprocess.Popen("sudo tc qdisc add dev eth0 root tbf rate 1kbit burst 1kbit", shell=True)
        try:
            yield
        finally:
            logger.debug(f"Exiting context manager: add_low_bandwith")
            subprocess.Popen("sudo tc qdisc del dev eth0 root", shell=True)

    @contextmanager
    def node_pause(self, node):
        logger.debug("Entering context manager: node_pause")
        node.pause_process()
        try:
            yield
        finally:
            logger.debug(f"Exiting context manager: node_pause")
            node.resume_process()

    def send_with_timestamp(self, send_method, id, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        response = send_method(id, message)
        response_messages = response["result"]["messages"]
        message_id = None
        for m in response_messages:
            if m["text"] == message:
                message_id = m["id"]
                break
        return timestamp, message_id

    def create_group_chat_with_timestamp(self, sender_node, member_list, private_group_name):
        timestamp = datetime.now().strftime("%H:%M:%S")
        response = sender_node.create_group_chat_with_members(member_list, private_group_name)
        response_messages = response["result"]["messages"]
        message_id = None
        for m in response_messages:
            if private_group_name in m["text"]:
                message_id = m["id"]
                break
        return timestamp, message_id

    @retry(stop=stop_after_delay(40), wait=wait_fixed(0.5), reraise=True)
    def accept_contact_request(self, sending_node=None, receiving_node_pk=None):
        if not sending_node:
            sending_node = self.second_node
        if not receiving_node_pk:
            receiving_node_pk = self.first_node_pubkey
        sending_node.send_contact_request(receiving_node_pk, "hi")
        assert sending_node.wait_for_logs(["accepted your contact request"], timeout=10)

    @retry(stop=stop_after_delay(40), wait=wait_fixed(0.5), reraise=True)
    def join_private_group(self, sending_node=None, members_list=None):
        if not sending_node:
            sending_node = self.second_node
        if not members_list:
            members_list = [self.first_node_pubkey]
        response = sending_node.create_group_chat_with_members(members_list, "new_group")
        receiving_node = self.first_node if sending_node == self.second_node else self.second_node
        assert receiving_node.wait_for_logs(["created the group new_group"], timeout=10)
        self.private_group_id = response["result"]["chats"][0]["id"]
        return self.private_group_id

    @retry(stop=stop_after_delay(40), wait=wait_fixed(0.5), reraise=True)
    def create_communities(self, num_communities):
        self.community_id_list = []
        for i in range(num_communities):
            name = f"community_{i}"
            response = self.first_node.create_community(name)
            community_id = response["result"]["communities"][0]["id"]
            response = self.second_node.fetch_community(community_id)
            assert response["result"]["name"] == name
            self.community_id_list.append(community_id)
        return self.community_id_list

    def setup_community_nodes(self, node_limit=None):
        resources_folder = "./resources"
        tar_files = [f for f in os.listdir(resources_folder) if f.endswith(".tar")]

        # Use node_limit if you just need a limited number of nodes
        if node_limit is not None:
            tar_files = tar_files[:node_limit]

        # Extract the nodes from the tar file
        for tar_file in tar_files:
            tar_path = os.path.join(resources_folder, tar_file)
            command = f"tar -xvf {tar_path} -C ./"
            subprocess.run(command, shell=True, check=True)

        self.community_nodes = []
        for root, dirs, files in os.walk("."):
            for dir_name in dirs:
                if dir_name.startswith("test-0x"):
                    keystore_path = os.path.join(root, dir_name, "keystore")
                    if os.path.exists(keystore_path):
                        community_dirs = os.listdir(keystore_path)
                        if community_dirs:
                            node_uid = community_dirs[0]
                            node_name = dir_name.split("test-")[1]
                            community_id = node_name.split("_")[0]
                            port = node_name.split("_")[1]
                            status_node = StatusNode(name=node_name, port=port)
                            self.community_nodes.append({"node_uid": node_uid, "community_id": community_id, "status_node": status_node})

        # Start all nodes
        for _, community_node in enumerate(self.community_nodes):
            node_uid = community_node["node_uid"]
            status_node = community_node["status_node"]
            status_node.serve_account(node_uid)

        delay(4)

        return self.community_nodes

    def join_created_communities(self):
        self.community_join_requests = []
        for community_node in self.community_nodes:
            community_id = community_node["community_id"]
            self.first_node.fetch_community(community_id)
            response_to_join = self.first_node.request_to_join_community(community_id)
            target_community = [
                existing_community for existing_community in response_to_join["result"]["communities"] if existing_community["id"] == community_id
            ][0]
            initial_members = len(target_community["members"])
            request_to_join_id = response_to_join["result"]["requestsToJoinCommunity"][0]["id"]
            self.community_join_requests.append((community_id, request_to_join_id, community_node["status_node"], initial_members))
        delay(4)
        self.chat_id_list = []
        for _, request_to_join_id, community_node, _ in self.community_join_requests:
            response = community_node.accept_request_to_join_community(request_to_join_id)
            chats = response["result"]["communities"][0]["chats"]
            chat_id = list(chats.keys())[0]
            self.chat_id_list.append(chat_id)
