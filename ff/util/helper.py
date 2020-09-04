import sys
from azureml.pipeline.steps import ParallelRunConfig

sys.path.append("..")


def validate_parallel_run_config(parallel_run_config):
    max_concurrency = 20
    if (parallel_run_config.process_count_per_node * parallel_run_config.node_count) > max_concurrency:
        print("Please decrease concurrency to maximum of 20 as currently AutoML does not support it.")
        raise ValueError("node_count*process_count_per_node must be between 1 and max_concurrency {}"
                         .format(max_concurrency))


def build_parallel_run_config(source_directory, train_env, compute, nodecount, workercount, timeout):
    parallel_run_config = ParallelRunConfig(
        source_directory=source_directory,
        entry_script='train_automl.py',
        mini_batch_size="1",  # do not modify this setting
        run_invocation_timeout=timeout,
        run_max_try=3,
        error_threshold=-1,
        output_action="append_row",
        environment=train_env,
        process_count_per_node=workercount,
        compute_target=compute,
        node_count=nodecount)
    validate_parallel_run_config(parallel_run_config)
    return parallel_run_config
