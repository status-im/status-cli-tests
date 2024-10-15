from uuid import uuid4
import pytest
from src.env_vars import DELAY_BETWEEN_MESSAGES, NUM_MESSAGES
from src.libs.common import delay
from src.steps.common import StepsCommon


@pytest.mark.usefixtures("start_2_nodes")
class TestCreatePrivateGroups(StepsCommon):
    def test_create_group_chat_baseline(self):
        num_private_groups = NUM_MESSAGES  # Set the number of private groups to create

        private_groups = []

        self.accept_contact_request()

        for i in range(num_private_groups):
            # Alernating which node creates the private group
            if i % 2 == 0:
                node = self.second_node
                other_node_pubkey = self.first_node_pubkey
            else:
                node = self.first_node
                other_node_pubkey = self.second_node_pubkey

            private_group_name = f"private_group_from_{node.name}_{i}"
            timestamp, message_id = self.create_group_chat_with_timestamp(node, [other_node_pubkey], private_group_name)
            private_groups.append((timestamp, private_group_name, message_id, node.name))
            delay(DELAY_BETWEEN_MESSAGES)

        delay(10)

        missing_private_groups = []

        for timestamp, private_group_name, message_id, node_name in private_groups:
            search_node = self.first_node if node_name == self.second_node.name else self.second_node
            if not search_node.search_logs(f"created the group {private_group_name}"):
                missing_private_groups.append((timestamp, private_group_name, message_id, node_name))

        if missing_private_groups:
            formatted_missing_groups = [
                f"Timestamp: {ts}, GroupName: {msg}, ID: {mid}, Node: {node}" for ts, msg, mid, node in missing_private_groups
            ]
            raise AssertionError(
                f"{len(missing_private_groups)} private groups out of {num_private_groups} were not created: " + "\n".join(formatted_missing_groups)
            )

    #  for creating private group we don't have realiability protocol, therefore skipping the tests for latency, packet loss and low bandwith

    def test_create_group_with_node_pause(self):
        self.accept_contact_request()
        with self.node_pause(self.second_node):
            group_name = str(uuid4())
            self.first_node.create_group_chat_with_members([self.second_node_pubkey], group_name)
            delay(10)
        assert self.second_node.wait_for_logs([group_name])
