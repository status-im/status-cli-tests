from contextlib import contextmanager
import inspect
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

    def join_created_communities(self):
        community_join_requests = []
        for community_id in self.community_id_list:
            response_to_join = self.second_node.request_to_join_community(community_id)
            request_to_join_id = response_to_join["result"]["requestsToJoinCommunity"][0]["id"]
            community_join_requests.append(request_to_join_id)
        delay(4)
        self.chat_id_list = []
        for request_to_join_id in community_join_requests:
            response = self.first_node.accept_request_to_join_community(request_to_join_id)
            chats = response["result"]["communities"][0]["chats"]
            chat_id = list(chats.keys())[0]
            self.chat_id_list.append(chat_id)
