import pytest
from src.env_vars import DELAY_BETWEEN_MESSAGES, NUM_MESSAGES
from src.libs.common import delay
from src.steps.common import StepsCommon


@pytest.mark.usefixtures("start_2_nodes")
class TestOneToOneMessages(StepsCommon):
    def test_one_to_one_baseline(self):
        num_messages = NUM_MESSAGES  # Set the number of messages to send

        # Send contact request from second_node to first_node
        self.second_node.send_contact_request(self.first_node_pubkey, "test1")
        delay(4)

        messages = []

        # Send messages from second_node to first_node and from first_node to second_node
        for i in range(num_messages):
            message_second_node = f"message_from_second_node_{i}"
            message_first_node = f"message_from_first_node_{i}"
            timestamp_second_node, message_id_second_node = self.send_with_timestamp(
                self.second_node.send_message, self.first_node_pubkey, message_second_node
            )
            delay(DELAY_BETWEEN_MESSAGES)
            timestamp_first_node, message_id_first_node = self.send_with_timestamp(
                self.first_node.send_message, self.second_node_pubkey, message_first_node
            )
            delay(DELAY_BETWEEN_MESSAGES)
            messages.append((timestamp_second_node, message_second_node, message_id_second_node, "second_node"))
            messages.append((timestamp_first_node, message_first_node, message_id_first_node, "first_node"))

        # Wait for 10 seconds to give all messages time to be received
        delay(10)

        # Validate that all messages were received
        missing_messages = {"first_node": [], "second_node": []}

        for timestamp, message, message_id, sender in messages:
            if sender == "second_node":
                log_message = f"message received: {message}"
                if not self.first_node.search_logs(log_message):
                    missing_messages["first_node"].append((timestamp, message, message_id))
            elif sender == "first_node":
                log_message = f"message received: {message}"
                if not self.second_node.search_logs(log_message):
                    missing_messages["second_node"].append((timestamp, message, message_id))

        # Check for missing messages and collect assertion errors
        errors = []
        if missing_messages["first_node"]:
            errors.append(
                f"first_node didn't receive {len(missing_messages['first_node'])} out of {num_messages} messages from second_node: {missing_messages['first_node']}"
            )
            errors.append(
                f"second_node didn't receive {len(missing_messages['second_node'])} out of {num_messages} messages from first_node: {missing_messages['second_node']}"
            )

        # Raise a combined assertion error if there are any missing messages
        if errors:
            raise AssertionError("\n".join(errors))

    def test_one_to_one_with_latency(self, add_latency):
        self.test_one_to_one_baseline()

    def test_one_to_one_with_packet_loss(self, add_packet_loss):
        self.test_one_to_one_baseline()

    def test_one_to_one_with_low_bandwith(self, add_low_bandwith):
        self.test_one_to_one_baseline()
