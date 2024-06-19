import pytest
from src.env_vars import DELAY_BETWEEN_MESSAGES, NUM_MESSAGES
from src.libs.common import delay
from src.steps.common import StepsCommon


@pytest.mark.usefixtures("start_2_nodes")
class TestPrivateGroupMessages(StepsCommon):
    def test_group_chat_messages_baseline(self):
        num_private_groups = NUM_MESSAGES  # Set the number of private messages to send

        self.accept_contact_request()
        try:
            self.private_group_id
        except:
            self.join_private_group()

        messages = []

        for i in range(num_private_groups):
            # Alternating which node sends the message
            if i % 2 == 0:
                sending_node = self.second_node
            else:
                sending_node = self.first_node

            message = f"message_from_{sending_node.name}_{i}"
            timestamp, message_id = self.send_with_timestamp(sending_node.send_group_chat_message, self.private_group_id, message)
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
                f"{len(missing_messages)} messages out of {num_private_groups} were not received: " + "\n".join(formatted_missing_messages)
            )

    def test_group_chat_messages_with_latency(self):
        self.accept_contact_request()
        self.join_private_group()
        # we want to set latency only on the group creation requests
        with self.add_latency():
            self.test_group_chat_messages_baseline()

    def test_group_chat_messages_with_packet_loss(self):
        self.accept_contact_request()
        self.join_private_group()
        with self.add_packet_loss():
            self.test_group_chat_messages_baseline()

    def test_group_chat_messages_with_low_bandwith(self):
        self.accept_contact_request()
        self.join_private_group()
        with self.add_low_bandwith():
            self.test_group_chat_messages_baseline()
