from uuid import uuid4
import pytest
from src.env_vars import DELAY_BETWEEN_MESSAGES, NUM_MESSAGES
from src.libs.common import delay
from src.steps.common import StepsCommon


@pytest.mark.usefixtures("start_1_node")
class TestCommunityMessages(StepsCommon):
    @pytest.mark.flaky(reruns=2)
    def test_community_messages_baseline(self):
        if not self.community_nodes:
            self.setup_community_nodes(node_limit=1)
            self.join_created_communities()

        delay(10)

        messages = []
        message_chat_id = self.community_nodes[0]["community_id"] + self.chat_id_list[0]
        community_node = self.community_nodes[0]["status_node"]

        for i in range(NUM_MESSAGES):
            # Alternating which node sends the message
            if i % 2 == 0:
                sending_node = community_node
            else:
                sending_node = self.first_node

            message = f"{uuid4()}_message_from_{sending_node.name}_{i}"
            timestamp, message_id = self.send_with_timestamp(sending_node.send_community_chat_message, message_chat_id, message)
            messages.append((timestamp, message, message_id, sending_node.name))
            delay(DELAY_BETWEEN_MESSAGES)

        # Wait for 10 seconds to give all messages time to be received
        delay(10)

        # Validate that all messages were received
        missing_messages = []

        for timestamp, message, message_id, sender in messages:
            search_node = self.first_node if sender == community_node.name else community_node
            if not search_node.search_logs(f"message received: {message}"):
                missing_messages.append((timestamp, message, message_id, sender))

        if missing_messages:
            formatted_missing_messages = [f"Timestamp: {ts}, Message: {msg}, ID: {mid}, Sender: {snd}" for ts, msg, mid, snd in missing_messages]
            raise AssertionError(
                f"{len(missing_messages)} messages out of {NUM_MESSAGES} were not received: " + "\n".join(formatted_missing_messages)
            )

    def test_community_messages_with_latency(self):
        self.setup_community_nodes(node_limit=1)
        self.join_created_communities()
        with self.add_latency():
            self.test_community_messages_baseline()

    def test_community_messages_with_packet_loss(self):
        self.setup_community_nodes(node_limit=1)
        self.join_created_communities()
        with self.add_packet_loss():
            self.test_community_messages_baseline()

    def test_community_messages_with_low_bandwith(self):
        self.setup_community_nodes(node_limit=1)
        self.join_created_communities()
        with self.add_low_bandwith():
            self.test_community_messages_baseline()

    @pytest.mark.flaky(reruns=2)
    def test_community_messages_with_node_pause_10_seconds(self):
        self.setup_community_nodes(node_limit=1)
        self.join_created_communities()
        delay(10)
        message_chat_id = self.community_nodes[0]["community_id"] + self.chat_id_list[0]
        community_node = self.community_nodes[0]["status_node"]
        with self.node_pause(community_node):
            message = str(uuid4())
            self.first_node.send_community_chat_message(message_chat_id, message)
            delay(10)
        assert community_node.wait_for_logs([message])

    @pytest.mark.flaky(reruns=2)
    def test_community_messages_with_node_pause_30_seconds(self):
        self.setup_community_nodes(node_limit=1)
        self.join_created_communities()
        delay(10)
        message_chat_id = self.community_nodes[0]["community_id"] + self.chat_id_list[0]
        community_node = self.community_nodes[0]["status_node"]
        with self.node_pause(community_node):
            message = str(uuid4())
            self.first_node.send_community_chat_message(message_chat_id, message)
            delay(30)
        assert community_node.wait_for_logs([message])
