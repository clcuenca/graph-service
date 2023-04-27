"""
Top-level script to train & serialize machine learning models from datasets contained
in S3 buckets into serialized versions placed into another S3 bucket.another
@author Carlos L. Cuenca
"""

## -------
## Imports

import sys  # Command-line arguments
import re   # Regex
import json # Parse dataset

from arguments import Arguments
from log import Log
from mltrainer import MLTrainer
from spacy_trainer import SpacyTextCatTrainer

## ------
## Script

if __name__ == "__main__":

    # Initialize the log
    MLTrainer.Log = log = Log()
    SpacyTextCatTrainer.Log = log

    # Consume the arguments
    arguments = Arguments(sys.argv, ['datasetbucket', 'modelsbucket', 'dataset', 'spacy_model'])

    # Import the required modules
    from import_modules import import_modules

    # Import the required modules
    import_modules(sys.modules[__name__], 0,
                   boto3={
                       'package_name': 'boto3',
                       'resource': {}
                   },
                   botocore={
                       'package_name': 'botocore',
                       'exceptions': {
                           'ClientError': {}
                       }
                   },
                   io={
                       'package_name': 'io',
                       'BytesIO': {}
                   })

    # Initialize the names
    resource    = sys.modules[__name__].resource
    BytesIO     = sys.modules[__name__].BytesIO
    ClientError = sys.modules[__name__].ClientError

    # Initialize the dataset & output bucket
    dataset         = None
    models_bucket   = None

    try:

        # Retrieve the arguments
        spacy_model     = arguments['spacy_model']                                   # en_core_web_sm
        dataset_key     = re.sub(r'(\.[a-zA-Z0-9]+)+', '', arguments['dataset'])     # Hateful.csv

        log.Info(f'Retrieving dataset: {arguments["datasetbucket"]}/{dataset_key}')

        # Attempt to retrieve the data
        dataset = resource('s3').Object(arguments['datasetbucket'], arguments['dataset'])
        dataset = json.loads(dataset.get()['Body'].read())

        # Train the model
        trainer = SpacyTextCatTrainer(spacy_model, dataset)

        # Report to the user
        Log.Info(f'Retrieving models bucket: {arguments["modelsbucket"]}.')

        # Attempt to bind the bucket
        models_bucket = resource('s3').Bucket(arguments['modelsbucket'])

        # Retrieve the metrics
<<<<<<< HEAD
        metrics = {'dataset': dataset_key,
                   'spancat': trainer.spancat_metrics,
                   'textcat': trainer.textcat_metrics}
=======
        metrics = trainer.metrics()

        # Set the dataset field
        metrics['dataset'] = dataset_key
>>>>>>> 6c4e96d (Update training script)

        # Report to the user
        log.Info(f'{str(metrics)}')

        # Upload the config & data
        models_bucket.upload_fileobj(BytesIO(bytes(trainer.configuration().to_str(), 'utf-8')), f'{dataset_key}/config')
        models_bucket.upload_fileobj(BytesIO(trainer.bytes()), f'{dataset_key}/model')

        # TODO: Update the Table entry here

    # Catch the error
    except ClientError as error:

        # Report to the user
        log.Error(f'{error.response["Error"]["Code"]}')
