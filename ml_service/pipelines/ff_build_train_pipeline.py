import os
from azureml.core import Workspace, Environment
from azureml.core.runconfig import RunConfiguration
from azureml.core.dataset import Dataset
from azureml.pipeline.core.graph import PipelineParameter
from azureml.pipeline.steps import PythonScriptStep
from azureml.pipeline.core import Pipeline
from ml_service.util.attach_compute import get_compute
from ml_service.util.env_variables import Env


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

    train_ds_name = e.dataset_name
    train_data_path = e.datafile_path
    sources_directory_train = e.sources_directory_train
    pipeline_name = e.pipeline_name
    build_id = e.build_id

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

    train_input = train_ds.as_named_input('train_input')

    # Conda environment
    environment = Environment.from_conda_specification(
                    "myenv",
                    os.path.join(sources_directory_train, 
                                 "conda_dependencies.yml"))
    # Logging into Azure Application Insights
    env = {
        "APPLICATIONINSIGHTS_CONNECTION_STRING":
        e.applicationinsights_connection_string
    }
    env['AZUREML_FLUSH_INGEST_WAIT'] = ''
    env['DISABLE_ENV_MISMATCH'] = True
    environment.environment_variables = env

    from ff.util.helper import build_parallel_run_config

    # PLEASE MODIFY the following three settings based on your compute and
    # experiment timeout.
    process_count_per_node = 6
    node_count = 3
    # this timeout(in seconds) is inline with AutoML experiment timeout or (no
    # of iterations * iteration timeout)
    run_invocation_timeout = 3700

    parallel_run_config = build_parallel_run_config(sources_directory_train,
                                                    environment,
                                                    aml_compute,
                                                    node_count,
                                                    process_count_per_node,
                                                    run_invocation_timeout)

    from azureml.pipeline.core import PipelineData

    output_dir = PipelineData(name="training_output",
                              datastore=data_store)

    #from azureml.contrib.pipeline.steps import ParallelRunStep
    from azureml.pipeline.steps import ParallelRunStep

    parallel_run_step = ParallelRunStep(
        name="many-models-training",
        parallel_run_config=parallel_run_config,
        allow_reuse=False,
        inputs=[train_input],
        output=output_dir
        # models=[],
        # arguments=[]
    )

    pipeline = Pipeline(workspace=aml_workspace, steps=parallel_run_step)
    pipeline._set_experiment_name
    pipeline.validate()
    published_pipeline = pipeline.publish(
        name=pipeline_name,
        description="FF AutomML pipeline",
        version=build_id
    )
    print(f'Published pipeline: {published_pipeline.name}')
    print(f'for build {published_pipeline.version}')


if __name__ == '__main__':
    main()
