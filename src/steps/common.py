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
        self.node_alice = StatusNode(name="alice", port="8545")
        self.node_alice.start()
        self.node_charlie = StatusNode(name="charlie", port="8565")
        self.node_charlie.start()
        self.node_alice.wait_fully_started()
        self.node_charlie.wait_fully_started()
        self.alice_pubkey = self.node_alice.get_pubkey()
        self.charlie_pubkey = self.node_charlie.get_pubkey()
        yield
        logger.debug(f"Running fixture teardown: {inspect.currentframe().f_code.co_name}")
        self.node_alice.stop()
        self.node_charlie.stop()

    @pytest.fixture(scope="function", autouse=False)
    def add_latency(self):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        subprocess.Popen("sudo tc qdisc add dev eth0 root netem delay 1s 100ms distribution normal", shell=True)
        yield
        logger.debug(f"Running fixture teardown: {inspect.currentframe().f_code.co_name}")
        subprocess.Popen("sudo tc qdisc del dev eth0 root", shell=True)

    @pytest.fixture(scope="function", autouse=False)
    def add_packet_loss(self):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        subprocess.Popen("sudo tc qdisc add dev eth0 root netem loss 50%", shell=True)
        yield
        logger.debug(f"Running fixture teardown: {inspect.currentframe().f_code.co_name}")
        subprocess.Popen("sudo tc qdisc del dev eth0 root netem", shell=True)

    @pytest.fixture(scope="function", autouse=False)
    def add_low_bandwith(self):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        subprocess.Popen("sudo tc qdisc add dev eth0 root tbf rate 1kbit burst 1kbit", shell=True)
        yield
        logger.debug(f"Running fixture teardown: {inspect.currentframe().f_code.co_name}")
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
