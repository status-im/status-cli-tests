import asyncio
from uuid import uuid4
import pytest
from src.env_vars import DELAY_BETWEEN_MESSAGES, NUM_MESSAGES
from src.libs.common import delay
from src.node.status_node import StatusNode
from src.steps.common import StepsCommon


@pytest.mark.usefixtures("start_2_nodes")
class TestOneToOneMessages(StepsCommon):
    @pytest.mark.asyncio
    async def test_one_to_one_message_baseline(self, recover_network_fn=None):
        timeout_secs = 180
        reset_network_in_secs = 10
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

        # Validate that all messages were received
        tasks = []
        for msg in messages:
            search_node = self.first_node if msg[3] == self.second_node.name else self.second_node
            tasks.append(asyncio.create_task(self.wait_for_message_async(search_node, msg, timeout_secs)))

        done, pending = await asyncio.wait(tasks, timeout=reset_network_in_secs)
        if pending:
            if recover_network_fn is not None:
                # after `reset_network_in_secs` the network will recover and MVDS will eventually deliver the messages
                recover_network_fn()
            print("waiting for pending tasks")
            done2, _ = await asyncio.wait(pending)
            done.update(done2)
        else:
            print("no pending tasks")

        missing_messages = []
        for task in done:
            if task.exception():
                print(f"Task raised an exception: {task.exception()}")
                raise task.exception()
            else:
                res = task.result()
                if res is not None:
                    missing_messages.append(res)

        if missing_messages:
            formatted_missing_messages = [f"Timestamp: {ts}, Message: {msg}, ID: {mid}, Sender: {snd}" for ts, msg, mid, snd in missing_messages]
            raise AssertionError(
                f"{len(missing_messages)} messages out of {num_messages} were not received: " + "\n".join(formatted_missing_messages)
            )

    async def test_one_to_one_message_with_latency(self):
        self.accept_contact_request()
        # we want to set latency only on the message sending requests
        with self.add_latency() as recover_network_fn:
            await self.test_one_to_one_message_baseline(recover_network_fn)

    async def test_one_to_one_message_with_packet_loss(self):
        self.accept_contact_request()
        with self.add_packet_loss() as recover_network_fn:
            await self.test_one_to_one_message_baseline(recover_network_fn)

    async def test_one_to_one_message_with_low_bandwith(self):
        self.accept_contact_request()
        with self.add_low_bandwith() as recover_network_fn:
            await self.test_one_to_one_message_baseline(recover_network_fn)

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

    async def wait_for_message_async(self, node: StatusNode, msg: tuple[int, str, str, str], timeout_secs: int = 45):
        res = await node.wait_for_logs_async([f"message received: {msg[1]}"], timeout_secs)
        if res:
            return None
        else:
            # return missing
            return msg
