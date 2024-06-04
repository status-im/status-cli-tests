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
        # Run the shell script
        process = subprocess.Popen(["./aaaa.sh"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        # Read and print stdout and stderr line by line
        for stdout_line in iter(process.stdout.readline, ""):
            logger.debug(stdout_line)
            # Do something with the stdout_line if needed

        for stderr_line in iter(process.stderr.readline, ""):
            logger.debug(stderr_line)
            # Do something with the stderr_line if needed

        # Wait for the process to terminate and get the return code
        process.wait()

        # Print the return code
        logger.debug(f"Return code: {process.returncode}")
        yield
        self.node_alice.stop()
        self.node_charlie.stop()

    def send_message_with_timestamp(self, sender_node, receiver_pubkey, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        sender_node.send_message(receiver_pubkey, message)
        return timestamp, message
