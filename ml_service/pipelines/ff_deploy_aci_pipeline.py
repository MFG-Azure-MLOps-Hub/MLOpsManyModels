import argparse
import os
from azureml.core import Workspace, Environment
from azureml.core.model import Model
from azureml.core.model import InferenceConfig
from azureml.core.webservice import AciWebservice, Webservice
from azureml.exceptions import WebserviceException
from ml_service.util.env_variables import Env
from ml_service.util.tools import get_model_names

parser = argparse.ArgumentParser("deploy ACI")
parser.add_argument("--aci_deployment_name", type=str, help="ACI name")

args = parser.parse_args()
aci_service_name = args.aci_deployment_name

print("aci_deployment_name: %s" % aci_service_name)


def main():
    e = Env()
    # Get Azure machine learning workspace
    ws = Workspace.get(
        name=e.workspace_name,
        subscription_id=e.subscription_id,
        resource_group=e.resource_group
    )
    print(f"get_workspace: {ws}")

    # Parameters
    sources_directory_train = e.sources_directory_train

    # model_names = ["nyc_energy_model", "diabetes_model"]
    model_names = get_model_names(os.path.join(sources_directory_train,
                                               "pipeline_config.json"))
    models = []
    for model_name in model_names:
        models.append(Model(ws, name=model_name))

    # Conda environment
    myenv = Environment.from_conda_specification(
        "myenv",
        os.path.join(sources_directory_train, "conda_dependencies.yml"))
    # Enable Docker based environment
    myenv.docker.enabled = True

    # Deprecated: pass the model names string to score.py
    # score.py reads model names from pipeline_config.json directly.
    # model_names_str = ''
    # for name in model_names:
    #     model_names_str = model_names_str + name + ','
    # model_names_str = model_names_str[:-1]
    # myenv.environment_variables = {"MODEL_NAMES": model_names_str}

    inference_config = InferenceConfig(
        source_directory=sources_directory_train,
        entry_script="scoring/score.py",
        environment=myenv)

    deployment_config = AciWebservice.deploy_configuration(
        cpu_cores=1,
        memory_gb=2,
        tags={'area': "digits", 'type': aci_service_name},
        description=aci_service_name)

    try:
        # Check if the service is existed
        service = Webservice(ws, name=aci_service_name)
        if service:
            print("Found existing service: %s .. delete it" % aci_service_name)
            service.delete()
    except WebserviceException as e:
        print(e)

    service = Model.deploy(
        ws, aci_service_name, models, inference_config, deployment_config)

    service.wait_for_deployment(True)
    print(service.state)


if __name__ == '__main__':
    main()
