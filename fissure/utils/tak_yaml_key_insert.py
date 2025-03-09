#!/usr/bin/env python3

import yaml
import argparse
from fissure.utils import YAML_DIR
import os

# Instantiate the argument parser
parser = argparse.ArgumentParser(description='Update fissure_config.yaml with key and cert paths')
parser.add_argument('key', type=str, help='Path to key file')
parser.add_argument('cert', type=str, help='Path to cert file')
parser.add_argument('webadmin_cert', type=str, help='Path to webadmin cert file')
args = parser.parse_args()

# print(args.key)
# print(args.cert)
# print(args.webadmin_cert)

file_path = os.path.join(YAML_DIR, "fissure_config.yaml")
file_path2 = os.path.join(YAML_DIR, "User Configs", "default.yaml")

# print(file_path)
# print(file_path2)

# Function to safely update YAML files
def update_yaml(file_path, key_path, cert_path, webadmin_cert_path):
    try:
        # Read existing YAML data
        if os.path.exists(file_path):
            with open(file_path, "r") as fiss_yaml:
                doc = yaml.load(fiss_yaml, yaml.FullLoader) or {}
        else:
            doc = {}

        # Ensure "tak" key exists
        if "tak" not in doc:
            doc["tak"] = {}

        # Update the key and cert paths
        doc["tak"]["key"] = key_path
        doc["tak"]["cert"] = cert_path
        doc["tak"]["webadmin_cert"] = webadmin_cert_path

        # Write the updated data back to the file
        with open(file_path, "w") as fiss_yaml:
            yaml.dump(doc, fiss_yaml, default_flow_style=False)

        print(f"Successfully updated {file_path}")
    except Exception as e:
        print(f"Error updating YAML file: {e} - {file_path}")


# Update both config files
update_yaml(file_path, args.key, args.cert, args.webadmin_cert)
update_yaml(file_path2, args.key, args.cert, args.webadmin_cert)