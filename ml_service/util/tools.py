import json


def are_all_runs_finished(runs):
    for run in runs:
        status = run.get_status()
        if status != 'Finished' and status != 'Failed' and status != 'Canceled':
            return False
    return True


#  Read all model names from the config file
def get_model_names(config_file):
    models = []
    with open(config_file) as json_file:
        pipe_param = json.load(json_file)
        for param in pipe_param['pipeline_parameter']:
            models.append(param['model_name'])
    return models
