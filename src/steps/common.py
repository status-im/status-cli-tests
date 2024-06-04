import inspect
import subprocess
import pytest
from src.libs.custom_logger import get_custom_logger
from src.node.status_node import StatusNode
from datetime import datetime

logger = get_custom_logger(__name__)


class StepsCommon:
    @pytest.fixture(scope="class", autouse=True)
    def common_setup(self):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")

    @pytest.fixture(scope="function", autouse=True)
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
    def add_latency(self, start_2_nodes):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        subprocess.Popen("sudo tc qdisc add dev eth0 root netem delay 1s 100ms distribution normal", shell=True)
        yield
        logger.debug(f"Running fixture teardown: {inspect.currentframe().f_code.co_name}")
        subprocess.Popen("sudo tc qdisc del dev eth0 root", shell=True)

    @pytest.fixture(scope="function", autouse=False)
    def add_packet_loss(self, start_2_nodes):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        subprocess.Popen("sudo tc qdisc add dev eth0 root netem loss 20% 25%", shell=True)
        yield
        logger.debug(f"Running fixture teardown: {inspect.currentframe().f_code.co_name}")
        subprocess.Popen("sudo tc qdisc del dev eth0 root netem", shell=True)

    @pytest.fixture(scope="function", autouse=False)
    def add_low_bandwith(self, start_2_nodes):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        subprocess.Popen("sudo tc qdisc add dev eth0 root tbf rate 1bit burst 1bit", shell=True)
        yield
        logger.debug(f"Running fixture teardown: {inspect.currentframe().f_code.co_name}")
        subprocess.Popen("sudo tc qdisc del dev eth0 root", shell=True)

    def send_message_with_timestamp(self, sender_node, receiver_pubkey, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        sender_node.send_message(receiver_pubkey, message)
        return timestamp, message
