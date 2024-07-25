import os
from uuid import uuid4
from src.env_vars import NUM_CONTACT_REQUESTS
from src.libs.common import delay
from src.node.status_node import StatusNode
from src.steps.common import StepsCommon


class TestContacRequest(StepsCommon):
    def test_contact_request_baseline(self):
        num_contact_requests = NUM_CONTACT_REQUESTS  # Set the number of contact requests to send

        missing_contact_requests = []

        for index in range(num_contact_requests):
            contact_requests_successful = False
            first_node = StatusNode()
            first_node.start()
            second_node = StatusNode()
            second_node.start()
            first_node.wait_fully_started()
            second_node.wait_fully_started()
            first_node_pubkey = first_node.get_pubkey()
            contact_request_message = f"contact_request_{index}"
            timestamp, message_id = self.send_with_timestamp(second_node.send_contact_request, first_node_pubkey, contact_request_message)
            if first_node.wait_for_logs([f"message received: {contact_request_message}", "AcceptContactRequest"]):
                contact_requests_successful = True
            first_node.stop()
            second_node.stop()
            if contact_requests_successful:
                # removing logs of nodes where contact request went fine
                first_node.clear_logs()
                second_node.clear_logs()
            else:
                missing_contact_requests.append((timestamp, contact_request_message, message_id))

        if missing_contact_requests:
            formatted_missing_requests = [f"Timestamp: {ts}, Message: {msg}, ID: {mid}" for ts, msg, mid in missing_contact_requests]
            raise AssertionError(
                f"{len(missing_contact_requests)} contact requests out of {num_contact_requests} didn't reach the peer node: "
                + "\n".join(formatted_missing_requests)
            )

    def test_contact_request_with_latency(self):
        with self.add_latency():
            self.test_contact_request_baseline()

    def test_contact_request_with_packet_loss(self):
        with self.add_packet_loss():
            self.test_contact_request_baseline()

    def test_contact_request_with_low_bandwith(self):
        with self.add_low_bandwith():
            self.test_contact_request_baseline()

    def test_contact_request_with_node_pause(self, start_2_nodes):
        with self.node_pause(self.second_node):
            message = str(uuid4())
            self.first_node.send_contact_request(self.second_node_pubkey, message)
            delay(10)
        assert self.second_node.wait_for_logs([message])
