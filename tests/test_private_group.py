import pytest
from src.env_vars import DELAY_BETWEEN_MESSAGES, NUM_MESSAGES
from src.libs.common import delay
from src.steps.common import StepsCommon


@pytest.mark.usefixtures("start_2_nodes")
class TestPrivateGroup(StepsCommon):
    def test_create_group_chat(self):
        num_private_groups = NUM_MESSAGES  # Set the number of private groups to create

        private_groups = []

        self.second_node.send_contact_request(self.first_node_pubkey, "hi")
        assert self.second_node.wait_for_logs(["accepted your contact request"], timeout=20)

        for i in range(num_private_groups):
            private_group_name = f"private_group_{i}"
            timestamp, message_id = self.create_group_chat_with_timestamp(self.second_node, [self.first_node_pubkey], private_group_name)
            private_groups.append((timestamp, private_group_name, message_id))
            delay(DELAY_BETWEEN_MESSAGES)

        delay(10)

        missing_private_groups = []

        for timestamp, private_group_name, message_id in private_groups:
            if not self.first_node.search_logs(f"created the group {private_group_name}"):
                missing_private_groups.append((timestamp, private_group_name, message_id))

        if missing_private_groups:
            formatted_missing_requests = [f"Timestamp: {ts}, GroupName: {msg}, ID: {mid}" for ts, msg, mid in missing_private_groups]
            raise AssertionError(
                f"{len(missing_private_groups)} private groups out of {num_private_groups} were not created: " + "\n".join(formatted_missing_requests)
            )

    def test_create_group_chat_with_latency(self):
        self.second_node.send_contact_request(self.first_node_pubkey, "hi")
        assert self.second_node.wait_for_logs(["accepted your contact request"], timeout=20)
        # we want to set latency only on the group creation requests
        with self.add_latency():
            self.test_create_group_chat()

    def test_create_group_chat_with_packet_loss(self):
        self.second_node.send_contact_request(self.first_node_pubkey, "hi")
        assert self.second_node.wait_for_logs(["accepted your contact request"], timeout=20)
        with self.add_packet_loss():
            self.test_create_group_chat()

    def test_create_group_chat_with_low_bandwith(self):
        self.second_node.send_contact_request(self.first_node_pubkey, "hi")
        assert self.second_node.wait_for_logs(["accepted your contact request"], timeout=20)
        with self.add_low_bandwith():
            self.test_create_group_chat()
