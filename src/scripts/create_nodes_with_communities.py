import os
import tarfile
from time import sleep
from src.node.status_node import StatusNode

num_communities = 10
root_folder = "."  # Set your root folder path here
resources_folder = os.path.join(root_folder, "resources")

# Ensure the resources folder exists
os.makedirs(resources_folder, exist_ok=True)

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

    # Archive the renamed folder
    archive_name = f"{new_folder_name}.tar"
    archive_path = os.path.join(resources_folder, archive_name)

    with tarfile.open(archive_path, "w") as tar:
        tar.add(new_folder_path, arcname=new_folder_name)
