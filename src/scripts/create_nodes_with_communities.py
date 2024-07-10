import os
import tarfile
from time import sleep
from src.node.status_node import StatusNode

num_communities = 10
root_folder = "."  # Set your root folder path here
archive_path = os.path.join(root_folder, "resources/nodes.tar")

for i in range(num_communities):
    port = str(6130 + i)
    node = StatusNode(name=f"node{i}", port=port)
    node.start(capture_logs=False)
    sleep(4)

    name = f"vac_qa_community_{i}"
    response = node.create_community(name)
    community_id = response["result"]["communities"][0]["id"]
    sleep(5)

    node.stop(remove_local_data=False)

    # Rename the folder to test-{community_id}_{port}
    old_folder_name = f"test-node{i}"
    new_folder_name = f"test-{community_id}_{port}"

    old_folder_path = os.path.join(root_folder, old_folder_name)
    new_folder_path = os.path.join(root_folder, new_folder_name)

    if os.path.exists(old_folder_path):
        os.rename(old_folder_path, new_folder_path)

# Archive all folders starting with 'test-0x'
with tarfile.open(archive_path, "w") as tar:
    for item in os.listdir(root_folder):
        if item.startswith("test-0x") and os.path.isdir(os.path.join(root_folder, item)):
            tar.add(os.path.join(root_folder, item), arcname=item)
