import pytest
from src.env_vars import NUM_COMMUNITIES
from src.libs.common import delay
from src.steps.common import StepsCommon
from datetime import datetime

num_joins = NUM_COMMUNITIES  # Set the number of cummunities to join


@pytest.mark.usefixtures("start_2_nodes")
class TestJoinCommunity(StepsCommon):
    def test_join_community_baseline(self):
        try:
            self.community_id_list
        except:
            self.create_communities(num_joins, creating_node=self.first_node)

        community_join_requests = []
        for community_id in self.community_id_list:
            timestamp = datetime.now().strftime("%H:%M:%S")
            response_to_join = self.second_node.request_to_join_community(community_id)
            request_to_join_id = response_to_join["result"]["requestsToJoinCommunity"][0]["id"]
            community_join_requests.append((community_id, request_to_join_id, timestamp))

        delay(4)

        failed_community_joins = []
        for community_id, request_to_join_id, join_req_ts in community_join_requests:
            accept_ts = datetime.now().strftime("%H:%M:%S")
            response_accept_to_join = self.first_node.accept_request_to_join_community(request_to_join_id)
            try:
                target_community = [
                    existing_community
                    for existing_community in response_accept_to_join["result"]["communities"]
                    if existing_community["id"] == community_id
                ][0]
                assert len(target_community["members"]) == 2, "Comunity doesn't have 2 members so second node didn't managed to join"
            except Exception as ex:
                failed_community_joins.append((join_req_ts, accept_ts, community_id, str(ex)))

        if failed_community_joins:
            formatted_missing_requests = [
                f"Join Timestamp: {jts}, Accept Timestamp: {ats},Community ID: {cid}, Error: {er}" for jts, ats, cid, er in failed_community_joins
            ]
            raise AssertionError(f"{len(failed_community_joins)} community joins out of {num_joins}: " + "\n".join(formatted_missing_requests))

    def test_join_community_with_latency(self):
        self.create_communities(num_joins)
        with self.add_latency():
            self.test_join_community_baseline()

    def test_join_community_with_packet_loss(self):
        self.create_communities(num_joins)
        with self.add_packet_loss():
            self.test_join_community_baseline()

    def test_join_communityy_with_low_bandwith(self):
        self.create_communities(num_joins)
        with self.add_low_bandwith():
            self.test_join_community_baseline()
