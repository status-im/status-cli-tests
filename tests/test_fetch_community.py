from time import sleep
import pytest
from src.libs.common import delay
from src.steps.common import StepsCommon
from datetime import datetime


@pytest.mark.usefixtures("start_1_node")
class TestFetchCommunity(StepsCommon):
    def test_fetch_community_baseline(self):
        try:
            self.community_nodes
        except:
            self.setup_community_nodes()

        failed_community_fetches = []
        for community_node in self.community_nodes:
            community_id = community_node["community_id"]
            response = self.first_node.fetch_community(community_id)
            try:
                assert response["result"]["id"] == community_id
            except Exception as ex:
                failed_community_fetches.append((community_id, str(ex)))

        if failed_community_fetches:
            formatted_missing_requests = [f",Community ID: {cid}, Error: {er}" for cid, er in failed_community_fetches]
            raise AssertionError(
                f"{len(failed_community_fetches)} community fetches out of {len(self.community_nodes)}: " + "\n".join(formatted_missing_requests)
            )

    def test_fetch_community_with_latency(self):
        self.setup_community_nodes()
        with self.add_latency():
            self.test_fetch_community_baseline()

    def test_fetch_community_with_packet_loss(self):
        self.setup_community_nodes()
        with self.add_packet_loss():
            self.test_fetch_community_baseline()

    def test_fetch_community_with_low_bandwith(self):
        self.setup_community_nodes()
        with self.add_low_bandwith():
            self.test_fetch_community_baseline()
