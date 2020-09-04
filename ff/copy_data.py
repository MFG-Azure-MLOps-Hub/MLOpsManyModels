import os
import time
import argparse
from azure.storage.blob import BlobServiceClient
from azureml.core.run import Run
from azureml.core import Dataset

print("Running copy_data.py")

parser = argparse.ArgumentParser("prepare")
parser.add_argument("--source_blob_url", type=str, help="source_blob_url")
parser.add_argument("--train_storage_connection_string", type=str, help="train storage connection string")
parser.add_argument("--train_storage_container", type=str, help="train storage container")
parser.add_argument("--data_file", type=str, help="data file name")
parser.add_argument("--data_file_path", type=str, help="data file path")

args = parser.parse_args()
source_blob = args.source_blob_url
train_storage_connection_string = args.train_storage_connection_string
train_storage_connection_string = train_storage_connection_string.replace("\\;",";")
#train_storage_connection_string = "DefaultEndpointsProtocol=https;AccountName=forecastingml8724233808;AccountKey=9o2ZH/5cLtmYmNyoHpoeKEA7Xjw0zi1fHLjI0Z0CZeQL5i4Ky2FZ9Wa6VpSYgK6uwLaHC3eamwnfEAscNTcgYw==;EndpointSuffix=core.windows.net"
train_storage_container = args.train_storage_container
data_file = args.data_file
data_file_path = args.data_file_path


def main():
    print("train_storage_connection_string: %s" % train_storage_connection_string)
    status = None
    blob_service_client = BlobServiceClient.from_connection_string(train_storage_connection_string)
    copied_blob = blob_service_client.get_blob_client(
        train_storage_container,
        os.path.join(data_file_path, data_file))
    # Copy started
    copied_blob.start_copy_from_url(source_blob)
    for i in range(10):
        props = copied_blob.get_blob_properties()
        status = props.copy.status
        print("Copy status: " + status)
        if status == "success":
            # Copy finished
            break
        time.sleep(10)

    if status != "success":
        # if not finished after 100s, cancel the operation
        props = copied_blob.get_blob_properties()
        print(props.copy.status)
        copy_id = props.copy.id
        copied_blob.abort_copy(copy_id)
        props = copied_blob.get_blob_properties()
        print(props.copy.status)


if __name__ == "__main__":
    main()