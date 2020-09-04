---
page_type: sample
languages:
- python
products:
- azure
- azure-machine-learning-service
- azure-devops
description: "Sample code"
---

# Machine Learning DevOps for Many Models
## /.pipelines
Azure DevOps Pipelines
- ff-build-train.yml
- ff-variables.yml 
- ff-deploy-aci.yml
- ff-deploy-webapp.yml


## /experimentation
Experimentation notebook files & Python scripts
- ff
- 01_Train_AutoML_ParallelRunStep_log.ipynb

## /ff
Python scripts
- scoring/score.py
- util/helper.py
- conda_dependencies.yml
- pipeline_config.json (configuration for differnt use cases/models)
- train_automl.py

## /ml_service
Azure ML pipelines & tools
- pipelines/ff_build_train_pipeline.py
- pipelines/ff_run_train_pipeline.py
- pipelines/ff_deploy_aci_pipeline.py

## Get Started
### Create a Variable Group for your Pipeline
Create a variable group 'mmmo-vg' with the following variables:
| Variable Name               | Suggested Value                    |
| --------------------------- | -----------------------------------|
| BASE_NAME                   | [unique base name]                 |
| LOCATION                    | [resrouce group location]          |
| RESOURCE_GROUP              | mmmo-RG                            |
| WORKSPACE_NAME              | mmmo-AML-WS                        |
| WORKSPACE_SVC_CONNECTION    | aml-workspace-connection           | 
| ACI_DEPLOYMENT_NAME         | mmmo-aci                           |
| AZURE_RM_SVC_CONNECTION     | azure-resource-connection          |
| WEBAPP_DEPLOYMENT_NAME      | mmmo-webapp                        |
| TRAIN_STORAGE_CONNECTION_STRING | [train storage connection string] |
| TRAIN_STORAGE_CONTAINER         | [train storage container]         |
| APPLICATIONINSIGHTS_CONNECTION_STRING | [applicationinsights connection string] |
### Create AZURE_RM_SVC_CONNECTION	
azure-resource-connection

### Create Resources with Azure Pipelines
Run /environment_setup/iac-create-environment.yml

### Create WORKSPACE_SVC_CONNECTION
Service connection for the machine learning workspace
aml-workspace-connection

### Create Docker Registry service connection
acrconnection

### Run Docker Image Pipeline
Run /environment_setup/docker-image-pipeline.yml

### Run Build Train Pipeline
Run /.pipelines/ff-build-train.yml
ff-build-train.yml -> ff_build_train_pipeline.py & ff_run_train_pipeline.py -> train_automl.py

### Run Deploy ACI Pipeline
Run /.pipelines/ff-deploy-aci.yml
ff-deploy-aci.yml -> ff_deploy_aci_pipeline.py -> score.py

### Run Deploy Webapp Pipeline
Run /.pipelines/ff-deploy-webapp.yml
ff-deploy-webapp.yml -> ff_create_scoring_image.py -> score.py

### Consume Web Services
#### Use web browsers
- http://xxx.eastasia.azurecontainer.io/score?model_name=nyc_energy_model&data=[["2017-8-12 7:00",0,70],["2017-8-12 19:00",0,50]]
- http://xxx.eastasia.azurecontainer.io/score?model_name=diabetes_model&data=[[1,2,3,4,5,6,7,8,9,0],[56,33,11,88,0,43,6,8,1,68]]
#### Use Postman
- URL: https://mmmo-webapp.azurewebsites.net/score
- Body-raw:
{
	"model_name": "nyc_energy_model",
    "data": [
        [
            "2017-08-13 06:00",
            0,
            50
        ]
    ]
}
#### Source code
- ml_service/util/ff_smoke_test_scoring_service.py

