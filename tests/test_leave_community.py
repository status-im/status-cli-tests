import pytest
from src.env_vars import NUM_COMMUNITIES
from src.libs.common import delay
from src.steps.common import StepsCommon
from datetime import datetime

num_joins = NUM_COMMUNITIES  # Set the number of cummunities to join


@pytest.mark.usefixtures("start_2_nodes")
class TestLeaveCommunity(StepsCommon):
    def test_leave_community_baseline(self):
        try:
            self.community_id_list
        except:
            self.create_communities(num_joins)
            self.join_created_communities()

        delay(5)

        failed_community_leave = []
        for community_id in self.community_id_list:
            leave_ts = datetime.now().strftime("%H:%M:%S")
            response_accept_to_join = self.second_node.leave_community(community_id)
            try:
                target_community = [
                    existing_community
                    for existing_community in response_accept_to_join["result"]["communities"]
                    if existing_community["id"] == community_id
                ][0]
                assert len(target_community["members"]) == 1, "Comunity doesn't have 1 members so second node didn't managed to leave"
            except Exception as ex:
                failed_community_leave.append((leave_ts, community_id, str(ex)))

        if failed_community_leave:
            formatted_missing_requests = [f"Leave Timestamp: {lts}, Community ID: {cid}, Error: {er}" for lts, cid, er in failed_community_leave]
            raise AssertionError(f"{len(failed_community_leave)} community joins out of {num_joins}: " + "\n".join(formatted_missing_requests))

    def test_leave_community_with_latency(self):
        self.create_communities(num_joins)
        self.join_created_communities()
        with self.add_latency():
            self.test_leave_community_baseline()

    def test_leave_community_with_packet_loss(self):
        self.create_communities(num_joins)
        self.join_created_communities()
        with self.add_packet_loss():
            self.test_leave_community_baseline()

    def test_leave_communityy_with_low_bandwith(self):
        self.create_communities(num_joins)
        self.join_created_communities()
        with self.add_low_bandwith():
            self.test_leave_community_baseline()
