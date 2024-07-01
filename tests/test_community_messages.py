import pytest
from src.env_vars import DELAY_BETWEEN_MESSAGES, NUM_MESSAGES
from src.libs.common import delay
from src.steps.common import StepsCommon


@pytest.mark.usefixtures("start_2_nodes")
class TestCommunityMessages(StepsCommon):
    def test_community_messages_baseline(self):
        try:
            self.community_id_list
        except:
            self.create_communities(1)
            self.join_created_communities()

        delay(5)

        messages = []
        message_chat_id = self.community_id_list[0] + self.chat_id_list[0]

        for i in range(NUM_MESSAGES):
            # Alternating which node sends the message
            if i % 2 == 0:
                sending_node = self.second_node
            else:
                sending_node = self.first_node

            message = f"message_from_{sending_node.name}_{i}"
            timestamp, message_id = self.send_with_timestamp(sending_node.send_community_chat_message, message_chat_id, message)
            messages.append((timestamp, message, message_id, sending_node.name))
            delay(DELAY_BETWEEN_MESSAGES)

        # Wait for 10 seconds to give all messages time to be received
        delay(10)

        # Validate that all messages were received
        missing_messages = []

        for timestamp, message, message_id, sender in messages:
            search_node = self.first_node if sender == self.second_node.name else self.second_node
            if not search_node.search_logs(f"message received: {message}"):
                missing_messages.append((timestamp, message, message_id, sender))

        if missing_messages:
            formatted_missing_messages = [f"Timestamp: {ts}, Message: {msg}, ID: {mid}, Sender: {snd}" for ts, msg, mid, snd in missing_messages]
            raise AssertionError(
                f"{len(missing_messages)} messages out of {NUM_MESSAGES} were not received: " + "\n".join(formatted_missing_messages)
            )

    def test_community_messages_with_latency(self):
        self.create_communities(1)
        self.join_created_communities()
        with self.add_latency():
            self.test_community_messages_baseline()

    def test_community_messages_with_packet_loss(self):
        self.create_communities(1)
        self.join_created_communities()
        with self.add_packet_loss():
            self.test_community_messages_baseline()

    def test_community_messages_with_low_bandwith(self):
        self.create_communities(1)
        self.join_created_communities()
        with self.add_low_bandwith():
            self.test_community_messages_baseline()
