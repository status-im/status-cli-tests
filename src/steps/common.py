from contextlib import contextmanager
import inspect
import subprocess
import pytest
from src.libs.custom_logger import get_custom_logger
from src.node.status_node import StatusNode
from datetime import datetime

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

    def send_with_timestamp(self, send_method, receiver_pubkey, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        response = send_method(receiver_pubkey, message)
        response_messages = response["result"]["messages"]
        message_id = None
        for m in response_messages:
            if m["text"] == message:
                message_id = m["id"]
                break
        return timestamp, message_id
