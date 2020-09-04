import argparse
import os
import numpy as np
from azureml.core.run import Run
from azureml.core import Dataset

print("Running prepare.py")

parser = argparse.ArgumentParser("prepare")
parser.add_argument("--data_file_path", type=str, help="data file path")
parser.add_argument("--data_file", type=str, help="data file name")
parser.add_argument("--target_column", type=str, help="target column")
parser.add_argument("--features", type=str, help="features")

args = parser.parse_args()
data_file_path = args.data_file_path
data_file = args.data_file
target_column = args.target_column
features = args.features

run = Run.get_context()
ws = run.experiment.workspace
ds = ws.get_default_datastore()

# sds = Dataset.get_by_name(workspace=ws, name=ds_name)
sds = Dataset.Tabular.from_delimited_files(
    path=[(ds, os.path.join(data_file_path, data_file))])
sdf = sds.to_pandas_dataframe()

# Extract actual dataset for feature selection and training, remove
# the rows which are NaN
adf = sdf
# Change blank cells to NaN
# df_actual[target_column].replace('', np.nan, inplace=True)
adf.replace('', np.nan, inplace=True)
adf.dropna(subset=[target_column], inplace=True)

keep_columns = features.split(',')
adf = adf[keep_columns]
print(adf)

# Create a new folder to save the file if needed
#path = os.path.dirname(data_file)
print(data_file_path)
if data_file_path:
    print('Creating a new folder')
    folder = os.path.exists(data_file_path)
    if not folder:
        os.makedirs(data_file_path)
adf.to_csv(data_file, index=False)

# Upload the file to update the dataset
# data_file: local saved file with path
# path: the target path in the data store
ds.upload_files(files=[data_file],
                target_path=data_file_path,
                overwrite=True,
                show_progress=True)
run.complete()
