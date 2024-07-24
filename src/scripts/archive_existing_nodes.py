import os
import tarfile

root_folder = "."  # Set your root folder path here
resources_folder = os.path.join(root_folder, "resources")

# Ensure the resources folder exists
os.makedirs(resources_folder, exist_ok=True)

# Iterate over all items in the resources folder
for item in os.listdir(resources_folder):
    item_path = os.path.join(resources_folder, item)
    if os.path.isdir(item_path):
        # Archive the folder
        archive_name = f"{item}.tar"
        archive_path = os.path.join(resources_folder, archive_name)

        with tarfile.open(archive_path, "w") as tar:
            tar.add(item_path, arcname=item)
