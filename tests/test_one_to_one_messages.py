from time import sleep
from uuid import uuid4
import pytest
from src.env_vars import DELAY_BETWEEN_MESSAGES, NUM_MESSAGES
from src.libs.common import delay
from src.steps.common import StepsCommon


@pytest.mark.usefixtures("start_2_nodes")
class TestOneToOneMessages(StepsCommon):
    def test_one_to_one_message_baseline(self):
        num_messages = NUM_MESSAGES  # Set the number of messages to send

        self.accept_contact_request()

        messages = []

        for i in range(num_messages):
            # Alternating which node sends the message
            if i % 2 == 0:
                sending_node = self.second_node
                receiving_node_pubkey = self.first_node_pubkey
            else:
                sending_node = self.first_node
                receiving_node_pubkey = self.second_node_pubkey

            message = f"message_from_{sending_node.name}_{i}"
            timestamp, message_id = self.send_with_timestamp(sending_node.send_message, receiving_node_pubkey, message)
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
                f"{len(missing_messages)} messages out of {num_messages} were not received: " + "\n".join(formatted_missing_messages)
            )

    def test_one_to_one_message_with_latency(self):
        self.accept_contact_request()
        # we want to set latency only on the message sending requests
        with self.add_latency():
            self.test_one_to_one_message_baseline()

    def test_one_to_one_message_with_packet_loss(self):
        self.accept_contact_request()
        with self.add_packet_loss():
            self.test_one_to_one_message_baseline()

    def test_one_to_one_message_with_low_bandwith(self):
        self.accept_contact_request()
        with self.add_low_bandwith():
            self.test_one_to_one_message_baseline()

    def test_one_to_one_message_with_node_pause_5_seconds(self):
        self.accept_contact_request()
        with self.node_pause(self.first_node):
            message = str(uuid4())
            self.second_node.send_message(self.first_node_pubkey, message)
            delay(5)
        assert self.first_node.wait_for_logs([message])

    def test_one_to_one_message_with_node_pause_30_seconds(self):
        self.accept_contact_request()
        with self.node_pause(self.first_node):
            message = str(uuid4())
            self.second_node.send_message(self.first_node_pubkey, message)
            delay(30)
        assert self.first_node.wait_for_logs([message])
