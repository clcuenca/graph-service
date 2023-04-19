# Graph Service

## System Architecture

![alt text](system_architecture.svg)

## CodeCommit & CodePipeline

The service code including the Typescript CDK code, Machine Learning Training scripts, Ingestion Scripts, & Graph
algorithms scripts are stored in a CodeCommit repository. A poll trigger was aggregated to the pipeline, which allows
the pipeline to run through the CDK code build commands, self-mutate, deploy the described infrastructure, & deploy
the Machine Learning Training, Ingestion, & algorithms to the corresponding EC2 instances.

## Machine Learning

The service deploys a t2.micro EC2 instance to train neural networks in order to enrich data for ingestion and/or
prediction of time-series data. Alternatives include SageMaker, however, EC2 was chosen to support configurations not
readily available to SageMaker as well as the option to speed up training time with instances that contain more
resources.

### Machine Learning Scripts S3 Bucket

Several scripts are available for the Machine Learning Training EC2 instance to train a model, since data enrichment &
ingestion can be considered different use-cases depending on the graph datasets to be ingested. The following 
methodologies have been implemented for the service to train models:

#### Natural Language Processing - Text Classification - SpaCy

SpaCy is a natural language processing framework that allows training of pipeline components to achieve various tasks
involving natural language processing. One of the service's use-cases involves text classification in order to enrich
datasets so graphs can be properly generated & encode time-series data.

The [textcat_train.py](https://github.com/clcuenca/graph-service/lib/mlscripts/textcat_train.py) script handles the 
task of training a SpaCy textcat pipe (pipeline component) & executes the following steps:

1. 

### Machine Learning Datasets S3 Bucket

An S3 Bucket is used to store training data that is available to the service. In the event that a new model need be
trained or re-trained, training and serialization of a model can be executed via an event emitted by EventBridge to
Systems Manager, which contains the corresponding Run Document to commence training. Each EC2 instance has a
corresponding Run Document that facilitates execution. In the case of the Machine Learning EC2 instances, the
Run Document allows for specifying which training script to run, labels, & datasets.

### Machine Learning Models Index

When a Model is trained, the EC2 training instance writes an entry into a DynamoDB Table, that contains data pertaining
to the results of the training (as well as training metrics). Each dataset contained in the Machine Learning Datasets
S3 Bucket corresponds to a model, & consequently an entry in the Machine Learning Models Index DynamoDB Table.

## Useful commands

* `npm run build`   compile typescript to js
* `npm run watch`   watch for changes and compile
* `npm run test`    perform the jest unit tests
* `cdk deploy`      deploy this stack to your default AWS account/region
* `cdk diff`        compare deployed stack with current state
* `cdk synth`       emits the synthesized CloudFormation template
