import os
import argparse
from azureml.core import Workspace
from azureml.core.model import Model
from azureml.core.environment import Environment
from azureml.core.model import InferenceConfig
from ml_service.util.env_variables import Env
from ml_service.util.tools import get_model_names


e = Env()

# Get Azure machine learning workspace
ws = Workspace.get(
    name=e.workspace_name,
    subscription_id=e.subscription_id,
    resource_group=e.resource_group
)

parser = argparse.ArgumentParser("create scoring image")
parser.add_argument(
    "--output_image_location_file",
    type=str,
    help=("Name of a file to write image location to, "
          "in format REGISTRY.azurecr.io/IMAGE_NAME:IMAGE_VERSION")
)
args = parser.parse_args()
sources_directory_train = e.sources_directory_train

# model_names = ["nyc_energy_model", "diabetes_model"]
model_names = get_model_names(os.path.join(sources_directory_train,
                                           "pipeline_config.json"))
print("models:")
print(model_names)
models = []
for model_name in model_names:
    models.append(Model(ws, name=model_name))

# Conda environment
myenv = Environment.from_conda_specification(
    "myenv",
    os.path.join(sources_directory_train, "conda_dependencies.yml"))
# Enable Docker based environment
myenv.docker.enabled = True

inference_config = InferenceConfig(
    source_directory=sources_directory_train,
    entry_script="scoring/score.py",
    environment=myenv)

package = Model.package(ws, models, inference_config)
package.wait_for_creation(show_output=True)
# Display the package location/ACR path
# print(package.location)
# location = get_location(package)
location = package.location
print("Image stored at {}".format(location))

# Save the Image Location for other AzDO jobs after script is complete
if args.output_image_location_file is not None:
    print("Writing image location to %s" % args.output_image_location_file)
    with open(args.output_image_location_file, "w") as out_file:
        out_file.write(location)
