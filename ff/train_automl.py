import pandas as pd
import os

from multiprocessing import current_process
from pathlib import Path
import argparse
from azureml.core import Run
from azureml.train.automl import AutoMLConfig
import datetime
from azureml.automl.core.shared.exceptions import (AutoMLException,
                                                   ClientException)
import json
#import traceback
from opencensus.ext.azure.log_exporter import AzureLogHandler
import logging

current_step_run = Run.get_context()

parser = argparse.ArgumentParser("split")
parser.add_argument("--process_count_per_node", default=1, type=int,
                    help="number of processes per node")
args, _ = parser.parse_known_args()


# Read pipeline configuration which contains amlsettings
def read_pipeline_config():
    full_path = Path(__file__).absolute().parent
    with open(str(full_path) + "/pipeline_config.json") as json_file:
        return json.load(json_file)


pipe_param = read_pipeline_config()


def init():
    # EntryScriptHelper().config(LOG_NAME)
    # logger = logging.getLogger(LOG_NAME)
    # APPLICATIONINSIGHTS_CONNECTION_STRING needs to be set
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    logger.addHandler(AzureLogHandler())

    output_folder = os.path.join(
        os.environ.get("AZ_BATCHAI_INPUT_AZUREML", ""), "temp/output")
    working_dir = os.environ.get("AZ_BATCHAI_OUTPUT_logs", "")
    ip_addr = os.environ.get("AZ_BATCHAI_WORKER_IP", "")
    log_dir = os.path.join(
        working_dir, "user", ip_addr, current_process().name)
    t_log_dir = Path(log_dir)
    t_log_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"{__file__}.output_folder:{output_folder}")
    logger.info("init()")


def get_automl_settings(file_path):
    model_name = None
    automl_settings = None
    file_name = file_path.split('/')[-1]
    for param in pipe_param['pipeline_parameter']:
        data_file = param["data_file"].split('/')[-1]
        if data_file == file_name:  # if param['data_file'] in file_path
            model_name = param['model_name']
            automl_settings = param['automl_settings']
            automl_settings['many_models'] = True
            automl_settings['many_models_process_count_per_node'] = \
                args.process_count_per_node
    return model_name, automl_settings


def train_model(file_path, data, logger):
    file_name = file_path.split('/')[-1][:-4]
    model_name, automl_settings = get_automl_settings(file_path)

    print(file_name)
    logger.info("in train_model")
    logger.info(automl_settings)
    print('data')
    print(data.head(5))
    automl_config = AutoMLConfig(training_data=data,
                                 **automl_settings)

    logger.info("submit_child")
    local_run = current_step_run.submit_child(automl_config, show_output=False)
    logger.info(local_run)
    print(local_run)
    local_run.wait_for_completion(show_output=True)

    fitted_model = local_run.get_output()

    return fitted_model, model_name, local_run


def run(input_data):
    # logger = logging.getLogger(LOG_NAME)
    logger = logging.getLogger(__name__)
    os.makedirs('./outputs', exist_ok=True)
    resultList = []
    logger.info('parallel run')
    idx = 0
    model_name = ''

    # input_folder = os.environ.get("AZ_BATCHAI_INPUT_AZUREML","")+"/"

    for file in input_data:
        logs = []
        date1 = datetime.datetime.now()
        logger.info('start (' + file + ') ' + str(datetime.datetime.now()))
        file_path = file

        file_name, file_extension = os.path.splitext(os.path.basename(file_path))

        try:
            if file_extension.lower() == ".parquet":
                data = pd.read_parquet(file_path)
            else:
                # data = pd.read_csv(file_path, parse_dates=[timestamp_column])
                data = pd.read_csv(file_path)
            # train model
            fitted_model, model_name, current_run = train_model(file_path, data, logger)

            try:
                logger.info('done training')
                print('Trained best model ' + model_name)

                logger.info(fitted_model)
                logger.info(model_name)

                logger.info('register model, skip the outputs prefix')

                tags_dict = {'ModelType': 'AutoML'}
                # for column_name in group_column_names:
                #    tags_dict.update({column_name: str(data.iat[0, data.columns.get_loc(column_name)])})
                tags_dict.update({'InputData': file_path})

                current_run.register_model(model_name=model_name, description='AutoML', tags=tags_dict)
                print('Registered ' + model_name)
            except Exception as error:
                error_message = 'Failed to register the model. ' + 'Error message: ' + str(error)
                logger.info(error_message)

            date2 = datetime.datetime.now()

            logs.append('AutoML')
            logs.append(file_name)
            logs.append(model_name)
            logs.append(str(date1))
            logs.append(str(date2))
            logs.append(str(date2 - date1))
            logs.append(idx)
            logs.append(len(input_data))
            logs.append(current_run.get_status())
            idx += 1
            # logger_str='Pipeline:'+current_step_run.parent.id+',File:'+file_name+',Model:'+model_name+',Status:'+current_run.get_status()
            # logger_dict = {"pipeline":current_step_run.parent.id,"file":file_name+file_extension,"model":model_name,"status":current_run.get_status()}
            # logger_str = str(logger_dict)

            # Write the log in json format
            logger_str = '{\"pipeline\":\"' + current_step_run.parent.id +\
                         '\",\"file\":\"' + file_name + file_extension +\
                         '\",\"model\":\"' + model_name +\
                         '\",\"start\":\"' + str(date1) +\
                         '\",\"end\":\"' + str(date2) +\
                         '\",\"duration\":\"' + str(date2 - date1) +\
                         '\",\"status\":\"' + current_run.get_status() + '\"}'
            logger.info(logger_str)
            logger.info('ending (' + file_path + ') ' + str(date2))

        # 10.1 Log the error message if an exception occurs
        except (ValueError, UnboundLocalError, NameError, ModuleNotFoundError,
                AttributeError, ImportError, FileNotFoundError, KeyError,
                ClientException, AutoMLException) as error:
            date2 = datetime.datetime.now()
            error_message = 'Failed to train the model. ' +\
                            'Error message: ' + str(error)
            # trace_message = traceback.format_exc()

            logs.append('AutoML')
            logs.append(file_name)
            logs.append(model_name)
            logs.append(str(date1))
            logs.append(str(date2))
            logs.append(str(date2 - date1))
            logs.append(idx)
            logs.append(len(input_data))
            logs.append(error_message)
            idx += 1

            # Write the log in json format
            logger_str = '{\"pipeline\":\"' + current_step_run.parent.id +\
                         '\",\"file\":\"' + file_name + file_extension +\
                         '\",\"model\":\"' + model_name +\
                         '\",\"start\":\"' + str(date1) +\
                         '\",\"end\":\"' + str(date2) +\
                         '\",\"duration\":\"' + str(date2 - date1) +\
                         '\",\"status\":\"Failed\"}'
            logger.info(logger_str)

            logger.info(error_message)
            # logger.info(trace_message)
            logger.info('ending (' + file_path + ') ' + str(date2))

        resultList.append(logs)

    return resultList
