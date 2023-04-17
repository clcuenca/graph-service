## -------
## Imports

import sys
import json
import threading

from log import Log
from arguments import Arguments

REQUIRED_ARGUMENTS  = ['datasetsbucket', 'dataset', 'modelsbucket', 'model_name']#, 'endpoint', 'region']
# TODO: Make this into a parameter
retain              = ['body', 'createdAtFormatted', 'creator', 'datatype']

current_file        = None
current_file_read   = 0
current_file_size   = 0
current_file_lock   = threading.Lock()
lines_read          = 0

class OpenSearchWorker:

    ## -------------
    ## Static Fields

    Log          = None
    model_bucket = None
    model_name   = None
    Count        = 0

    ## --------------
    ## Static Methods

    @staticmethod
    def initialize_open_search_client(endpoint, region):

        # Import the required modules
        from import_modules import import_modules

        # Log
        if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Info(f'Importing required modules')

        # Import the specification
        import_modules(sys.modules[__name__], 0,
                       opensearchpy={
                           'package_name': 'opensearch-py',
                           'OpenSearch': {},
                           'RequestsHttpConnection': {}
                       },
                       requests_aws4auth={
                           'package_name': 'requests_aws4auth',
                           'AWS4Auth': {}
                       },
                       boto3={
                           'package_name': 'boto3',
                           'Session': {}
                       })

        Log.Info(f'Binding imported construct names')

        # Bind the names
        AWS4Auth                = sys.modules[__name__].AWS4Auth
        OpenSearch              = sys.modules[__name__].OpenSearch
        RequestsHttpConnection  = sys.modules[__name__].RequestsHttpConnection
        Session                 = sys.modules[__name__].Session

        Log.Info(f'Retrieving Credentials')

        # Retrieve the credentials
        credentials = Session().get_credentials()

        Log.Info(f'Initializing Signer')

        # Initialize authenticator (signer)
        auth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'es', session_token=credentials.token)

        Log.Info(f'Creating opensearch client')

        # Initialize the opensearch client
        return OpenSearch(
            hosts=[{'host': endpoint, 'port': 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )

    @staticmethod
    def initialize_language_model(model_bucket, model_name):

        # Log
        if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Info(f'Loading Language Model; Importing required modules')

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
                       spacy={
                           'package_name': 'spacy',
                           'util': {
                               'get_lang_class': {}
                           }
                       },
                       json={
                           'package_name': 'json',
                           'loads': {}
                       },
                       thinc={
                           'package_name': 'thinc',
                           'api': {
                               'Config': {}
                           }
                       })

        # Log
        if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Info(f'Modules loaded, binding names')

        # Initialize the names
        get_lang_class = sys.modules[__name__].get_lang_class
        resource = sys.modules[__name__].resource
        ClientError = sys.modules[__name__].ClientError
        Config = sys.modules[__name__].Config

        # Log
        if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Info(f'Retrieving \'{model_name}\' from {model_bucket}.')

        # Attempt
        try:

            # Model & config retrieval from the models bucket
            model = resource('s3').Object(model_bucket, f'{model_name}/model').get()['Body'].read()
            config = resource('s3').Object(model_bucket, f'{model_name}/config').get()['Body'].read().decode('utf-8')

        # Except
        except ClientError as clientError:

            if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Error(f'Error: Failed to retrieve \'{model_name}\' - {clientError.response["Error"]["Code"]}')

        # Log
        if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Info(f'Initializing Language Configuration')

        # Initialize the Config from string
        config = Config().from_str(config)

        # Log
        if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Info(f'Initializing Language Model')

        # Initialize the Language from the config
        language = get_lang_class(config['nlp']['lang']).from_config(config)
        language.from_bytes(model)

        # Log
        if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Info(f'Language model loaded.')

        # Return the result
        return language

    @staticmethod
    def read_line(streaming_body):

        # Initialize the result
        result = bytearray()

        # If we have a valid streaming body
        if streaming_body is not None:

            # Initialize the current
            current = streaming_body.read(amt=1)

            # While we haven't reached a line feed
            while current[0] != 0x0a:

                # Append to the result
                result.append(current[0])

                # Read the next byte
                current = streaming_body.read(amt=1)

        # Return the result
        return result.decode('utf-8')

    ## ------------
    ## Constructors

    def __init__(self, endpoint='', region=''):

        # If we have a valid model name and bucket
        if OpenSearchWorker.model_name is not None and OpenSearchWorker.model_bucket is not None:

            # Initialize the client
            #self.client = OpenSearchWorker.initialize_open_search_client(endpoint, region)

            # Initialize the model
            self.language = OpenSearchWorker.initialize_language_model(
                OpenSearchWorker.model_bucket, OpenSearchWorker.model_name)

            # Set the count
            self.count = OpenSearchWorker.Count

            # Increment the count
            OpenSearchWorker.Count += 1

    def ingest(self, retain_keys, language_key):

        global current_file
        global current_file_read
        global current_file_size
        global current_file_lock
        global lines_read

        previous_progress = 0

        terminate = False

        while self.language is not None:

            # Initialize the line
            line = None

            # Clear the current progress
            progress = 0

            # Attempt to acquire the file lock
            current_file_lock.acquire()

            # Attempt
            try:

                # Check if the file has finished
                if not current_file_read >= current_file_size:

                    # Retrieve the line
                    line = OpenSearchWorker.read_line(current_file)

                    # Update the amount of read lines
                    lines_read += 1

                    # Update the amount read
                    current_file_read += len(line) + 1

                    # Calculate the progress
                    progress = (current_file_read / current_file_size)*100

                # Otherwise
                else: terminate = True

            # Finally
            finally:

                # Release the lock
                current_file_lock.release()

            # Break condition
            if terminate: break

            # If we should display the progress
            if progress - previous_progress > 1:

                # Print out the progress
                OpenSearchWorker.Log.Info(f'Thread {self.count} - Lines Read: {lines_read}, {progress:.2f}%')

                # Set the previous progress
                previous_progress = progress

            # Initialize the entry
            entry = {key: value for key, value in json.loads(line).items() if key in retain_keys}

            # Brand it
            entry['dataset'] = OpenSearchWorker.model_name

            # Retrieve the categories for the text value
            categories = self.language(entry[language_key]).cats if language_key in entry else {}

            # Merge the results
            for key, value in categories.items():

                # Set the value
                entry[key] = value

            # TODO: Shove into open search here

if __name__ == "__main__":

    # Initialize the log
    OpenSearchWorker.Log    = log = Log()
    threads                 = 100

    # Consume the arguments
    arguments = Arguments(sys.argv)

    # Check the required arguments
    for required in REQUIRED_ARGUMENTS:

        # Check
        if required not in arguments.dictionary:

            # Log the error and exit
            log.Error(f'Error: Required argument \'{required}\' not specified.')

    # Import the required modules
    from import_modules import import_modules

    # Log
    log.Info(f'Importing required modules')

    # Import the specification
    import_modules(sys.modules[__name__], 0,
                   boto3={
                       'package_name': 'boto3',
                       'resource': {}
                   })

    Log.Info(f'Binding imported construct names')

    # Bind the names
    resource = sys.modules[__name__].resource

    # Initialize the static fields
    OpenSearchWorker.model_name     = arguments['model_name']
    OpenSearchWorker.model_bucket   = arguments['modelsbucket']

    # Initialize the datasets bucket
    datasets_bucket_name    = arguments['datasetsbucket']
    datasets_bucket         = resource('s3').Bucket(datasets_bucket_name)
    objects                 = datasets_bucket.objects.filter(Delimiter='/', Prefix=arguments['dataset'])
    objects                 = [{'key': object.key, 'size': object.size} for object in objects if object.size > 0]
    workers                 = [OpenSearchWorker() for index in range(threads)]

    # Initialize the threads
    threads = []

    # Iterate through the workers
    for worker in workers:

        # Initialize the thread with the worker
        thread = threading.Thread(target=worker.ingest,
                                  args=(['body', 'createdAtFormatted', 'creator', 'datatype'], 'body'))

        # Append the thread
        threads.append(thread)

    # Iterate through the object
    for object in objects:

        # Acquire the lock
        current_file_lock.acquire()

        # Attempt
        try:

            # If the current file is null
            if current_file is None:

                # Update the values
                current_file_read = 0
                lines_read        = 0
                current_file_size = object['size']

                # Initialize the current file
                current_file = resource('s3').Object(datasets_bucket_name, object['key']).get()['Body']

        finally:

            # Release the lock
            current_file_lock.release()

        # Start the threads
        [thread.start() for thread in threads]

        # Wait
        [thread.join() for thread in threads]
