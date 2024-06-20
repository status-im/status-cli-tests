import pytest
from src.env_vars import NUM_COMMUNITIES
from src.steps.common import StepsCommon
from datetime import datetime


@pytest.mark.usefixtures("start_2_nodes")
class TestCreateCommunity(StepsCommon):
    def test_create_and_fetch_community_baseline(self):
        num_communities = NUM_COMMUNITIES  # Set the number of communities to create

        community_fetch_failed = []

        for i in range(num_communities):
            name = f"community_{i}"
            response = self.second_node.create_community(name)
            community_id = response["result"]["communities"][0]["id"]
            timestamp = datetime.now().strftime("%H:%M:%S")

            for node in [self.first_node, self.second_node]:
                try:
                    response = node.fetch_community(community_id)
                    assert response["result"]["name"] == name
                except Exception:
                    community_fetch_failed.append((timestamp, name, community_id, node.name))

        if community_fetch_failed:
            formatted_community_fetch_failed = [
                f"Timestamp: {ts}, CommunityName: {name}, ID: {id}, Node: {node}" for ts, name, id, node in community_fetch_failed
            ]
            raise AssertionError(
                f"Issues with {len(formatted_community_fetch_failed)} community fetches out of {int(num_communities) * 2}: "
                + "\n".join(formatted_community_fetch_failed)
            )

    def test_create_and_fetch_community_with_latency(self):
        with self.add_latency():
            self.test_create_and_fetch_community_baseline()

    def test_create_and_fetch_community_with_packet_loss(self):
        with self.add_packet_loss():
            self.test_create_and_fetch_community_baseline()

    def test_create_and_fetch_community_with_low_bandwith(self):
        with self.add_low_bandwith():
            self.test_create_and_fetch_community_baseline()
