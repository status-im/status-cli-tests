import os
import tarfile
from time import sleep
from src.node.status_node import StatusNode

num_communities = 10
sharded_community_pk = "0x4c0883a69102937d62341493bd663cdbe3d7d0cf8d59ae34d49bdf57b582f8c4"
root_folder = "."  # Set your root folder path here
resources_folder = os.path.join(root_folder, "resources")

# Ensure the resources folder exists
os.makedirs(resources_folder, exist_ok=True)


def create_community(node: StatusNode, i: int, in_shard: bool = False) -> tuple[str, str]:
    if in_shard:
        name = f"vac_qa_community_{i}_shard"
    else:
        name = f"vac_qa_community_{i}"
    response = node.create_community(name)
    community_id = response["result"]["communities"][0]["id"]
    if in_shard:
        sleep(5)
        node.set_community_shard(community_id, 128, sharded_community_pk)
    return community_id, name


for i in range(num_communities):
    port = str(6130 + i)
    node = StatusNode(name=f"node{i}", port=port)
    node.start(capture_logs=False)
    sleep(4)

    # create the first community in shard 128
    community_id, name = create_community(node, i, i == 0)
    sleep(5)
    print(f"Created community: {name} with ID: {community_id}")

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
