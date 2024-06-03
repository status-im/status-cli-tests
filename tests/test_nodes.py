from time import sleep
from src.env_vars import DELAY_BETWEEN_MESSAGES, NUM_MESSAGES
from src.steps.common import StepsCommon


class TestNodes(StepsCommon):
    def test_one_to_one_messages(self):
        num_messages = NUM_MESSAGES  # Set the number of messages to send

        # Send contact request from Charlie to Alice
        self.node_charlie.send_contact_request(self.alice_pubkey, "test1")
        sleep(4)

        messages = []

        # Send messages from Charlie to Alice and from Alice to Charlie
        for i in range(num_messages):
            timestamp_charlie, message_charlie = self.send_message_with_timestamp(self.node_charlie, self.alice_pubkey, f"message_from_charlie_{i}")
            sleep(DELAY_BETWEEN_MESSAGES)
            timestamp_alice, message_alice = self.send_message_with_timestamp(self.node_alice, self.charlie_pubkey, f"message_from_alice_{i}")
            sleep(DELAY_BETWEEN_MESSAGES)
            messages.append((timestamp_charlie, message_charlie, "charlie"))
            messages.append((timestamp_alice, message_alice, "alice"))

        # Validate that all messages were received
        missing_messages = {"alice": [], "charlie": []}

        for timestamp, message, sender in messages:
            if sender == "charlie":
                log_message = f"message received: {message}"
                if not self.node_alice.search_logs(log_message):
                    missing_messages["alice"].append((timestamp, message))
            elif sender == "alice":
                log_message = f"message received: {message}"
                if not self.node_charlie.search_logs(log_message):
                    missing_messages["charlie"].append((timestamp, message))

        # Check for missing messages and collect assertion errors
        errors = []
        if missing_messages["alice"]:
            errors.append(f"Alice didn't receive the following messages from Charlie: {missing_messages['alice']}")
        if missing_messages["charlie"]:
            errors.append(f"Charlie didn't receive the following messages from Alice: {missing_messages['charlie']}")

        # Raise a combined assertion error if there are any missing messages
        if errors:
            raise AssertionError("\n".join(errors))
