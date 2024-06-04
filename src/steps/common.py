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

    @pytest.fixture(scope="class", autouse=True)
    def start_2_nodes(self, common_setup, request):
        logger.debug(f"Running fixture setup: {inspect.currentframe().f_code.co_name}")
        self.node_alice = StatusNode(name="alice", port="8545")
        self.node_alice.start()
        self.node_charlie = StatusNode(name="charlie", port="8565")
        self.node_charlie.start()
        self.node_alice.wait_fully_started()
        self.node_charlie.wait_fully_started()
        request.cls.alice_pubkey = self.node_alice.get_pubkey()
        request.cls.node_alice = self.node_alice
        request.cls.charlie_pubkey = self.node_charlie.get_pubkey()
        request.cls.node_charlie = self.node_charlie
        # subprocess.Popen("sudo tc qdisc add dev eth0 root netem loss 20% 25%", shell=True)
        # sudo tc qdisc add dev eth0 root netem delay 1s 100ms distribution normal
        # 1 sec disconnects
        # subprocess.Popen("sudo tc qdisc add dev eth0 root tbf rate 50kbit burst 16kbit latency 200ms", shell=True)
        subprocess.Popen("sudo tc qdisc add dev eth0 root tbf rate 100kbit burst 32kbit", shell=True)

        yield
        subprocess.Popen("sudo tc qdisc del dev eth0 root netem", shell=True)
        self.node_alice.stop()
        self.node_charlie.stop()

    def send_message_with_timestamp(self, sender_node, receiver_pubkey, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        sender_node.send_message(receiver_pubkey, message)
        return timestamp, message
