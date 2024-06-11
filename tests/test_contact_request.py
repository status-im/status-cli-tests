import os
from src.env_vars import NUM_MESSAGES
from src.node.status_node import StatusNode
from src.steps.common import StepsCommon


class TestContacRequest(StepsCommon):
    def test_contact_request_baseline(self):
        num_contact_requests = NUM_MESSAGES  # Set the number of contact requests to send

        missing_contact_requests = []

        for index in range(num_contact_requests):
            contact_requests_successful = False
            first_node_name = f"alice_{index}"
            second_node_name = f"charlie_{index}"
            first_node = StatusNode(name=first_node_name, port="8545")
            first_node.start()
            second_node = StatusNode(name=second_node_name, port="8565")
            second_node.start()
            first_node.wait_fully_started()
            second_node.wait_fully_started()
            first_node_pubkey = first_node.get_pubkey()
            contact_request_message = f"contact_request_{index}"
            timestamp, message_id = self.send_with_timestamp(second_node.send_contact_request, first_node_pubkey, f"contact_request_{index}")
            if first_node.wait_for_logs([f"message received: {contact_request_message}", "AcceptContactRequest"]):
                contact_requests_successful = True
            first_node.stop()
            second_node.stop()
            if contact_requests_successful:
                # removing logs of nodes where contact request went fine
                os.remove(f"{first_node_name}.log")
                os.remove(f"{second_node_name}.log")
            else:
                missing_contact_requests.append((timestamp, contact_request_message, message_id))

        assert not missing_contact_requests, "Some contact requests didn't reach the peer node"
