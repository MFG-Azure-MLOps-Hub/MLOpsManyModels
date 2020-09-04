import json
import os
from waiting import wait
from azureml.core import Workspace, Environment
from azureml.core.dataset import Dataset
from azureml.core.runconfig import RunConfiguration
from azureml.pipeline.core.graph import PipelineParameter
from azureml.pipeline.steps import PythonScriptStep
from azureml.pipeline.core import Pipeline
from ml_service.util.attach_compute import get_compute
from ml_service.util.env_variables import Env
from ml_service.util.tools import are_all_runs_finished


def main():
    e = Env()
    # Get Azure machine learning workspace
    aml_workspace = Workspace.get(
        name=e.workspace_name,
        subscription_id=e.subscription_id,
        resource_group=e.resource_group
    )
    print(f"get_workspace: {aml_workspace}")

    # Get Azure machine learning cluster
    aml_compute = get_compute(
        aml_workspace,
        e.compute_name,
        e.vm_size)
    if aml_compute is not None:
        print(f"aml_compute: {aml_compute}")

    # Prepare the dataset input
    data_store = aml_workspace.get_default_datastore()
    print("data_store: %s" % data_store.name)

    # Parameters
    sources_directory_train = e.sources_directory_train
    build_id = e.build_id
    pipeline_name = 'Prepare Data Pipeline'
    train_ds_name = e.dataset_name
    train_data_path = e.datafile_path

    # Register the train dataset
    if (train_ds_name not in aml_workspace.datasets):
        train_path_on_datastore = train_data_path  # +'/*.csv'
        train_ds_data_path = [(data_store, train_path_on_datastore)]
        train_ds = Dataset.File.from_files(
            path=train_ds_data_path, validate=False)
        train_ds = train_ds.register(workspace=aml_workspace,
                                     name=train_ds_name,
                                     description='train data',
                                     tags={'format': 'CSV'},
                                     create_new_version=True)
    else:
        train_ds = Dataset.get_by_name(aml_workspace, train_ds_name)

    # Conda environment
    environment = Environment.from_conda_specification(
        "myenv",
        os.path.join(sources_directory_train,
                     "conda_dependencies.yml"))
    run_config = RunConfiguration()
    run_config.environment = environment

    with open(os.path.join(sources_directory_train, 'pipeline_config.json')) as json_file:
        pipe_param = json.load(json_file)
        for param in pipe_param['pipeline_parameter']:
            print(param)

    # Prepare pipeline parameters
    source_blob_url_param = PipelineParameter(
        name="source_blob_url", default_value="url")
    data_file_param = PipelineParameter(
        name="data_file", default_value="data_file")
    target_column_param = PipelineParameter(
        name="target_column", default_value="target_column")
    features_param = PipelineParameter(
        name="features", default_value="")

    # train_storage_connection_string = "DefaultEndpointsProtocol=https;AccountName=forecastingml8724233808;AccountKey=9o2ZH/5cLtmYmNyoHpoeKEA7Xjw0zi1fHLjI0Z0CZeQL5i4Ky2FZ9Wa6VpSYgK6uwLaHC3eamwnfEAscNTcgYw==;EndpointSuffix=core.windows.net"
    # Copy data step
    copy_step = PythonScriptStep(
        name="Copy Data",
        script_name="copy_data.py",
        arguments=[
            "--source_blob_url",
            source_blob_url_param,
            "--train_storage_connection_string",
            e.train_storage_connection_string,
            "--train_storage_container",
            e.train_storage_container,
            "--data_file",
            data_file_param,
            "--data_file_path",
            train_data_path],
        runconfig=run_config,
        compute_target=aml_compute,
        source_directory=sources_directory_train)
    print("Step Copy Data created")

    # Prepare data step
    prepare_step = PythonScriptStep(
        name="Prepare Data",
        script_name="prepare.py",
        arguments=["--data_file_path", train_data_path,
                   "--data_file", data_file_param,
                   "--target_column", target_column_param,
                   "--features", features_param],
        runconfig=run_config,
        compute_target=aml_compute,
        source_directory=sources_directory_train
    )
    print("Step Prepare created")

    # Publish the pipeline
    prepare_step.run_after(copy_step)
    pipeline_steps = [copy_step, prepare_step]
    pipeline = Pipeline(workspace=aml_workspace, steps=pipeline_steps)
    pipeline._set_experiment_name
    pipeline.validate()
    published_pipeline = pipeline.publish(
        name=pipeline_name,
        description="Prepare Data pipeline",
        version=build_id
    )
    print(f'Published pipeline: {published_pipeline.name}')
    print(f'for build {published_pipeline.version}')

    # Run the pipelines
    runs = []
    for param in pipe_param['pipeline_parameter']:
        # pipeline_parameters = {"model_name": "nyc_energy_model", "build_id": build_id}
        target_column = param['automl_settings']['label_column_name']
        param.pop('automl_settings')
        param.update({"target_column": target_column}) # Special process target_column
        print(param)
        pipeline_run = published_pipeline.submit(
            aml_workspace,
            e.experiment_name,
            param)
        runs.append(pipeline_run)
        print("Pipeline run initiated ", pipeline_run.id)

    # Wait for all runs to finish
    wait(lambda: are_all_runs_finished(runs), timeout_seconds=3600,
         sleep_seconds=5, waiting_for="all runs are finished")
    print("All prepare data pipeline runs done")


if __name__ == '__main__':
    main()
