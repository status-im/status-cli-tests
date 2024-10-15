from uuid import uuid4
import asyncio
import pytest
from src.env_vars import NUM_CONTACT_REQUESTS
from src.libs.common import delay
from src.node.status_node import StatusNode
from src.steps.common import StepsCommon


class TestContacRequest(StepsCommon):
    @pytest.mark.asyncio
    async def test_contact_request_baseline(self, recover_network_fn=None):
        timeout_secs = 180
        reset_network_in_secs = 30
        num_contact_requests = NUM_CONTACT_REQUESTS

        # start all nodes
        nodes: list[tuple[StatusNode, StatusNode, int]] = []
        for index in range(num_contact_requests):
            first_node = StatusNode()
            first_node.start()
            second_node = StatusNode()
            second_node.start()
            first_node.wait_fully_started()
            second_node.wait_fully_started()
            nodes.append((first_node, second_node, index))

        tasks = []
        for first_node, second_node, index in nodes:
            tasks.append(asyncio.create_task(self.send_and_wait_for_message((first_node, second_node), index, timeout_secs)))

        done, pending = await asyncio.wait(tasks, timeout=reset_network_in_secs)
        if pending:
            if recover_network_fn is not None:
                # after `reset_network_in_secs` the network will recover and MVDS will eventually deliver the messages
                recover_network_fn()
            done2, _ = await asyncio.wait(pending)
            done.update(done2)
        else:
            print("no pending tasks")

        missing_contact_requests = []
        for task in done:
            if task.exception():
                print(f"Task raised an exception: {task.exception()}")
            else:
                res = task.result()
                if res is not None:
                    missing_contact_requests.append(res)

        if missing_contact_requests:
            formatted_missing_requests = [f"Timestamp: {ts}, Message: {msg}, ID: {mid}" for ts, msg, mid in missing_contact_requests]
            raise AssertionError(
                f"{len(missing_contact_requests)} contact requests out of {num_contact_requests} didn't reach the peer node: "
                + "\n".join(formatted_missing_requests)
            )

    async def send_and_wait_for_message(self, nodes: tuple[StatusNode, StatusNode], index: int, timeout: int = 45):
        first_node, second_node = nodes
        first_node_pubkey = first_node.get_pubkey()
        contact_request_message = f"contact_request_{index}"
        timestamp, message_id = self.send_with_timestamp(second_node.send_contact_request, first_node_pubkey, contact_request_message)

        contact_requests_successful = await first_node.wait_for_logs_async(
            [f"message received: {contact_request_message}", "AcceptContactRequest"], timeout
        )
        first_node.stop()
        second_node.stop()
        if contact_requests_successful:
            # removing logs of nodes where contact request went fine
            first_node.clear_logs()
            second_node.clear_logs()
            return None
        else:
            # return missing contact request
            return (timestamp, contact_request_message, message_id)

    @pytest.mark.asyncio
    async def test_contact_request_with_latency(self):
        with self.add_latency() as recover_network_fn:
            await self.test_contact_request_baseline(recover_network_fn)

    @pytest.mark.asyncio
    async def test_contact_request_with_packet_loss(self):
        with self.add_packet_loss() as recover_network_fn:
            await self.test_contact_request_baseline(recover_network_fn)

    @pytest.mark.asyncio
    async def test_contact_request_with_low_bandwith(self):
        with self.add_low_bandwith() as recover_network_fn:
            await self.test_contact_request_baseline(recover_network_fn)

    def test_contact_request_with_node_pause(self, start_2_nodes):
        with self.node_pause(self.second_node):
            message = str(uuid4())
            self.first_node.send_contact_request(self.second_node_pubkey, message)
        assert self.second_node.wait_for_logs([message], 60)
