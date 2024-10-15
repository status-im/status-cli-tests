from time import sleep
import pytest
from src.libs.common import delay
from src.steps.common import StepsCommon
from datetime import datetime


@pytest.mark.usefixtures("start_1_node")
class TestJoinCommunity(StepsCommon):
    @pytest.mark.flaky(reruns=2)
    def test_join_community_baseline(self):
        if not self.community_nodes:
            self.setup_community_nodes()

        community_join_requests = []
        for community_node in self.community_nodes:
            community_id = community_node["community_id"]
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.first_node.fetch_community(community_id)
            response_to_join = self.first_node.request_to_join_community(community_id)
            target_community = [
                existing_community for existing_community in response_to_join["result"]["communities"] if existing_community["id"] == community_id
            ][0]
            initial_members = len(target_community["members"])
            request_to_join_id = response_to_join["result"]["requestsToJoinCommunity"][0]["id"]
            community_join_requests.append((community_id, request_to_join_id, timestamp, community_node["status_node"], initial_members))

        delay(10)

        failed_community_joins = []
        for community_id, request_to_join_id, join_req_ts, status_node, initial_members in community_join_requests:
            accept_ts = datetime.now().strftime("%H:%M:%S")
            response_accept_to_join = status_node.accept_request_to_join_community(request_to_join_id)
            try:
                target_community = [
                    existing_community
                    for existing_community in response_accept_to_join["result"]["communities"]
                    if existing_community["id"] == community_id
                ][0]
                assert target_community["joined"] == True
            except Exception as ex:
                failed_community_joins.append((join_req_ts, accept_ts, community_id, str(ex)))

        if failed_community_joins:
            formatted_missing_requests = [
                f"Join Timestamp: {jts}, Accept Timestamp: {ats},Community ID: {cid}, Error: {er}" for jts, ats, cid, er in failed_community_joins
            ]
            raise AssertionError(
                f"{len(failed_community_joins)} community joins out of {len(self.community_nodes)}: " + "\n".join(formatted_missing_requests)
            )

    def test_join_community_with_latency(self):
        self.setup_community_nodes()
        with self.add_latency():
            self.test_join_community_baseline()

    def test_join_community_with_packet_loss(self):
        self.setup_community_nodes()
        with self.add_packet_loss():
            self.test_join_community_baseline()

    def test_join_community_with_low_bandwith(self):
        self.setup_community_nodes()
        with self.add_low_bandwith():
            self.test_join_community_baseline()

    @pytest.mark.flaky(reruns=2)
    def test_join_community_with_node_pause(self):
        self.setup_community_nodes(node_limit=1)
        community_id = self.community_nodes[0]["community_id"]
        community_node = self.community_nodes[0]["status_node"]
        with self.node_pause(community_node):
            self.first_node.fetch_community(community_id)
            response_to_join = self.first_node.request_to_join_community(community_id)
            target_community = [
                existing_community for existing_community in response_to_join["result"]["communities"] if existing_community["id"] == community_id
            ][0]
            initial_members = len(target_community["members"])
            request_to_join_id = response_to_join["result"]["requestsToJoinCommunity"][0]["id"]
            delay(10)
        response_accept_to_join = community_node.accept_request_to_join_community(request_to_join_id)
        target_community = [
            existing_community for existing_community in response_accept_to_join["result"]["communities"] if existing_community["id"] == community_id
        ][0]
