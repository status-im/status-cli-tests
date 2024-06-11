import pytest
from src.env_vars import DELAY_BETWEEN_MESSAGES, NUM_MESSAGES
from src.libs.common import delay
from src.steps.common import StepsCommon


@pytest.mark.usefixtures("start_2_nodes")
class TestOneToOneMessages(StepsCommon):
    def test_one_to_one_baseline(self):
        num_messages = NUM_MESSAGES  # Set the number of messages to send

        # Send contact request from Charlie to Alice
        self.node_charlie.send_contact_request(self.alice_pubkey, "test1")
        delay(4)

        messages = []

        # Send messages from Charlie to Alice and from Alice to Charlie
        for i in range(num_messages):
            message_charlie = f"message_from_charlie_{i}"
            message_alice = f"message_from_alice_{i}"
            timestamp_charlie, message_id_charlie = self.send_with_timestamp(self.node_charlie.send_message, self.alice_pubkey, message_charlie)
            delay(DELAY_BETWEEN_MESSAGES)
            timestamp_alice, message_id_alice = self.send_with_timestamp(self.node_alice.send_message, self.charlie_pubkey, message_alice)
            delay(DELAY_BETWEEN_MESSAGES)
            messages.append((timestamp_charlie, message_charlie, message_id_charlie, "charlie"))
            messages.append((timestamp_alice, message_alice, message_id_alice, "alice"))

        # Wait for 10 seconds to give all messages time to be received
        delay(10)

        # Validate that all messages were received
        missing_messages = {"alice": [], "charlie": []}

        for timestamp, message, message_id, sender in messages:
            if sender == "charlie":
                log_message = f"message received: {message}"
                if not self.node_alice.search_logs(log_message):
                    missing_messages["alice"].append((timestamp, message, message_id))
            elif sender == "alice":
                log_message = f"message received: {message}"
                if not self.node_charlie.search_logs(log_message):
                    missing_messages["charlie"].append((timestamp, message, message_id))

        # Check for missing messages and collect assertion errors
        errors = []
        if missing_messages["alice"]:
            errors.append(
                f"Alice didn't receive {len(missing_messages['alice'])} out of {num_messages} messages from Charlie: {missing_messages['alice']}"
            )
            errors.append(
                f"Charlie didn't receive {len(missing_messages['charlie'])} out of {num_messages} messages from Alice: {missing_messages['charlie']}"
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
