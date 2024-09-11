import pytest
from src.libs.common import delay
from src.steps.common import StepsCommon
from datetime import datetime


@pytest.mark.usefixtures("start_1_node")
class TestLeaveCommunity(StepsCommon):
    @pytest.mark.flaky(reruns=2)
    def test_leave_community_baseline(self):
        try:
            self.community_nodes
        except:
            self.setup_community_nodes()
            self.join_created_communities()

        delay(10)

        failed_community_leave = []
        for community_id, _, _, initial_members in self.community_join_requests:
            leave_ts = datetime.now().strftime("%H:%M:%S")
            response_accept_to_join = self.first_node.leave_community(community_id)
            try:
                target_community = [
                    existing_community
                    for existing_community in response_accept_to_join["result"]["communities"]
                    if existing_community["id"] == community_id
                ][0]
                assert target_community["joined"] == False
            except Exception as ex:
                failed_community_leave.append((leave_ts, community_id, str(ex)))

        if failed_community_leave:
            formatted_missing_requests = [f"Leave Timestamp: {lts}, Community ID: {cid}, Error: {er}" for lts, cid, er in failed_community_leave]
            raise AssertionError(
                f"{len(failed_community_leave)} community joins out of {len(self.community_nodes)}: " + "\n".join(formatted_missing_requests)
            )

    def test_leave_community_with_latency(self):
        self.setup_community_nodes()
        self.join_created_communities()
        with self.add_latency():
            self.test_leave_community_baseline()

    def test_leave_community_with_packet_loss(self):
        self.setup_community_nodes()
        self.join_created_communities()
        with self.add_packet_loss():
            self.test_leave_community_baseline()

    def test_leave_community_with_low_bandwith(self):
        self.setup_community_nodes()
        self.join_created_communities()
        with self.add_low_bandwith():
            self.test_leave_community_baseline()
