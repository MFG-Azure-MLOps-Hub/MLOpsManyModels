import json
import os
import pandas as pd
from azureml.core.model import Model
from pathlib import Path
from sklearn.externals import joblib

models = {}


#  Read all model names from the config file
def get_model_names():
    model_names = []
    full_path = Path(__file__).absolute().parent.parent
    with open(str(full_path) + "/pipeline_config.json") as json_file:
        pipe_param = json.load(json_file)
        for param in pipe_param['pipeline_parameter']:
            model_names.append(param['model_name'])
    return model_names


def init():
    global models
    # model_names = ["nyc_energy_model", "diabetes_model"]
    # model_name_str = os.getenv("MODEL_NAMES")
    # model_names = list(model_name_str.split(','))
    # print(model_names)
    model_names = get_model_names()
    for model_name in model_names:
        model_path = Model.get_model_path(model_name=model_name)
        model = joblib.load(model_path)
        models[model_name] = model


# Note you can pass in multiple rows for scoring.
def run(raw_data):
    try:
        model_name = json.loads(raw_data)['model_name']
        model = models[model_name]
        data = json.loads(raw_data)['data']

        if(model_name == 'nyc_energy_model'):
            data = pd.DataFrame(columns=['timeStamp','precip','temp'], data=data)
            result = model.forecast(data, ignore_data_errors=True)
            return result[0].tolist()
        elif(model_name == 'diabetes_model'):
            data = pd.DataFrame(columns=['AGE','SEX','BMI','BP','S1','S2','S3','S4','S5','S6'], data=data)
            result = model.predict(data)
            return result.tolist()
        else:
            return "Model:{} not defined".format(model_name)
    except Exception as e:
        result = str(e)
        return result
