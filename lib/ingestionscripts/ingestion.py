## -------
## Imports

import sys
import json
import threading

from log import Log
from arguments import Arguments

REQUIRED_ARGUMENTS = ['datasetsbucket', 'dataset', 'modelsbucket', 'model_name', 'threads']  # , 'endpoint', 'region']
# TODO: Make this into a parameter
retain = ['username',
          'creator',
          'parent',
          'createdAt',
          'createdAtformatted',
          'verified',
          'impressions',
          'reposts',
          'state',
          'followers',
          'following',
          'depth',
          'comments',
          'body',
          'bodywithurls',
          'datatype',
          'hashtags']


class OpenSearchWorker:

    ## -------------
    ## Static Fields

    Log = None
    Count = 0

    ## --------------
    ## Static Methods

    @staticmethod
    def initialize_open_search_client(endpoint, region):

        # Import the required modules
        from import_modules import import_modules

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

        # Bind the names
        AWS4Auth = sys.modules[__name__].AWS4Auth
        OpenSearch = sys.modules[__name__].OpenSearch
        RequestsHttpConnection = sys.modules[__name__].RequestsHttpConnection
        Session = sys.modules[__name__].Session

        # Retrieve the credentials
        credentials = Session().get_credentials()

        # Initialize authenticator (signer)
        auth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'es', session_token=credentials.token)

        # Initialize the opensearch client
        return OpenSearch(
            hosts=[{'host': endpoint, 'port': 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )

    @staticmethod
    def download_language_model(model_bucket, model_name):

        # Log
        if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Info(
            f'Downloading Language Model; Importing required modules')

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
                       })

        # Log
        if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Info(f'Modules loaded, binding names')

        # Initialize the names
        get_lang_class = sys.modules[__name__].get_lang_class
        resource = sys.modules[__name__].resource
        ClientError = sys.modules[__name__].ClientError

        # Log
        if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Info(
            f'Retrieving \'{model_name}\' from {model_bucket}.')

        # Attempt
        try:

            # Model & config retrieval from the models bucket
            model   = resource('s3').Object(model_bucket, f'{model_name}/model').get()['Body'].read()
            config  = resource('s3').Object(model_bucket, f'{model_name}/config').get()['Body'].read().decode('utf-8')

        # Except
        except ClientError as clientError:

            if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Error(
                f'Error: Failed to retrieve \'{model_name}\' - {clientError.response["Error"]["Code"]}')

        # Return the results
        return config, model

    @staticmethod
    def initialize_language_model(config, model):

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

        # Initialize the names
        get_lang_class = sys.modules[__name__].get_lang_class
        resource = sys.modules[__name__].resource
        ClientError = sys.modules[__name__].ClientError
        Config = sys.modules[__name__].Config

        # Initialize the Config from string
        config = Config().from_str(config)

        # Initialize the Language from the config
        language = get_lang_class(config['nlp']['lang']).from_config(config)
        language.from_bytes(model)

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

    def __init__(self, config, model, model_name, endpoint='', region='', current_file_size=0, file=None):

        # If we have a valid model name and bucket
        if config is not None and model is not None:

            # Initialize the client
            self.client = OpenSearchWorker.initialize_open_search_client(endpoint, region)

            # Initialize the model
            self.language   = OpenSearchWorker.initialize_language_model(config, model)
            self.model_name = model_name
            self.file       = file

            # Set the count
            self.count              = OpenSearchWorker.Count
            self.current_file_size  = current_file_size

            # Increment the count
            OpenSearchWorker.Count += 1

    def ingest_local(self, retain_keys, language_key):

        current_file_read = 0
        lines_read = 0
        terminate = False

        import os
        import psutil

        p = psutil.Process(os.getpid())
        p.cpu_affinity([self.count % 20])

        # Iterate while we have a language
        while self.language is not None:

            # Initialize the line
            line = None

            # Initialize the progress
            progress = 0

            # Attempt
            try:

                # Check if the file has finished
                if not current_file_read >= self.current_file_size:

                    # Retrieve the line
                    line = self.file.readline()

                    # Update the amount of read lines
                    lines_read += 1

                    # Update the amount read
                    current_file_read += len(line) + 1

                    # Calculate the progress
                    progress = (current_file_read / self.current_file_size) * 100

                # Otherwise
                else:

                    terminate = True

            # Finally
            except:

                print(f'Thread {self.count} - Error')

            # Break condition
            if terminate: break

            # Print out the progress
            OpenSearchWorker.Log.Info(f'File: {self.file} - Thread {self.count} - Lines Read: {lines_read}, {progress:.1f}%')

            # Initialize the entry
            entry = {key: value for key, value in json.loads(line).items() if key in retain_keys}

            # Brand it
            entry['dataset'] = self.model_name

            # Retrieve the categories for the text value
            categories = self.language(entry[language_key]).cats if language_key in entry else {}

            # Merge the results
            for key, value in categories.items():
                # Set the value
                entry[key] = value

            if 'datatype' in entry and 'createdAt' in entry:

                # Initialize the index name & createdAt
                index = entry['datatype']
                createdAt = entry['createdAt']

                # Delete the key
                del entry['datatype']
                del entry['createdAt']

                # Create the index if it does not exist
                if not self.client.indices.exists(index):
                    # Create it if necessary
                    self.client.indices.create(index, body={
                        'mappings': {
                            'properties': {
                                'username': {'type': 'text', 'analyzer': 'standard'},
                                'creator': {'type': 'text', 'analyzer': 'standard'},
                                'parent': {'type': 'text', 'analyzer': 'standard'},
                                'createdAtformatted': {'type': 'text', 'analyzer': 'standard'},
                                'verified': {'type': 'text', 'analyzer': 'standard'},
                                'impressions': {'type': 'text', 'analyzer': 'standard'},
                                'reposts': {'type': 'text', 'analyzer': 'standard'},
                                'state': {'type': 'text', 'analyzer': 'standard'},
                                'followers': {'type': 'text', 'analyzer': 'standard'},
                                'following': {'type': 'text', 'analyzer': 'standard'},
                                'depth': {'type': 'text', 'analyzer': 'standard'},
                                'comments': {'type': 'text', 'analyzer': 'standard'},
                                'body': {'type': 'text', 'analyzer': 'english'},
                                'bodywithurls': {'type': 'text', 'analyzer': 'english'},
                                'hashtags': {'type': 'text', 'analyzer': 'english'},
                                'POSITIVE': {'type': 'text', 'analyzer': 'standard'},
                                'NEGATIVE': {'type': 'text', 'analyzer': 'standard'},
                            }
                        }
                    })

                # TODO: Shove into open search here
                self.client.index(index, id=f'{entry["creator"]}:{createdAt}', body=entry)

        else:

            if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Info(f'Skipping entry')

    def bulk_local(self, retain_keys, language_key):

        current_file_read = 0
        lines_read = 0
        terminate = False

        import time
        import signal
        import os
        import psutil
        import json

        p = psutil.Process(os.getpid())
        p.cpu_affinity([self.count % 20])

        start_time = time.time()

        actions     = []
        bulk        = 1000
        lines_read  = 0

        mask = signal.pthread_sigmask(signal.SIG_BLOCK, {})
        signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT})

        while self.language is not None and True:

            progress   = 0

            # Iterate while we have a language
            for count in range(bulk):

                # Initialize the line
                line = None

                # Attempt
                try:

                    # Check if the file has finished
                    if not current_file_read >= self.current_file_size:

                        # Retrieve the line
                        line = self.file.readline()

                        # Update the amount of read lines
                        lines_read += 1

                        # Update the amount read
                        current_file_read += len(line) + 1

                        # Calculate the progress
                        progress = (current_file_read / self.current_file_size) * 100

                    # Otherwise
                    else:

                        terminate = True

                # Finally
                except:

                    print(f'Thread {self.count} - Error')

                # Break condition
                if line is None or terminate: break

                # Initialize the entry
                entry = {key: value for key, value in json.loads(line).items() if key in retain_keys}

                # Brand it
                entry['dataset'] = self.model_name

                # Retrieve the categories for the text value
                categories = self.language(entry[language_key]).cats if language_key in entry else {}

                # Merge the results
                for key, value in categories.items():

                    # Set the value
                    entry[key] = value

                if 'datatype' in entry and 'createdAt' in entry:

                    # Initialize the index name & createdAt
                    index       = entry['datatype']
                    createdAt   = entry['createdAt']

                    # Delete the key
                    del entry['datatype']

                    action  = json.dumps({'index': {'_index': index, "_id": f'{entry["creator"]}:{createdAt}'}}) + '\n'
                    action += json.dumps(entry) + '\n'

                    # Add to actions
                    actions.append(action)

            rate = lines_read / (time.time() - start_time)

            # Print out the progress
            OpenSearchWorker.Log.Info(f'Thread {self.count} - Lines Read: {lines_read}, {progress:.1f}% - {rate:.1f} lines/second')

            # Create the index if it does not exist
            if not self.client.indices.exists(index):

                # Create it if necessary
                self.client.indices.create(index, body={
                    'mappings': {
                        'properties': {
                            'username': {'type': 'text', 'analyzer': 'standard'},
                            'creator': {'type': 'text', 'analyzer': 'standard'},
                            'parent': {'type': 'text', 'analyzer': 'standard'},
                            'createdAtformatted': {'type': 'text', 'analyzer': 'standard'},
                            'verified': {'type': 'text', 'analyzer': 'standard'},
                            'impressions': {'type': 'text', 'analyzer': 'standard'},
                            'reposts': {'type': 'text', 'analyzer': 'standard'},
                            'state': {'type': 'text', 'analyzer': 'standard'},
                            'followers': {'type': 'text', 'analyzer': 'standard'},
                            'following': {'type': 'text', 'analyzer': 'standard'},
                            'depth': {'type': 'text', 'analyzer': 'standard'},
                            'comments': {'type': 'text', 'analyzer': 'standard'},
                            'body': {'type': 'text', 'analyzer': 'english'},
                            'bodywithurls': {'type': 'text', 'analyzer': 'english'},
                            'hashtags': {'type': 'text', 'analyzer': 'english'},
                            'POSITIVE': {'type': 'text', 'analyzer': 'standard'},
                            'NEGATIVE': {'type': 'text', 'analyzer': 'standard'},
                        }
                    }
                })

            attempt = True

            while attempt:

                try:

                    # Bulk upload
                    self.client.bulk(actions, index=index)

                    # Update the flag
                    attempt = False

                except:

                    if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Info(f'Retrying index')

        else:

            if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Info(f'Skipping entry')

        signal.pthread_sigmask(signal.SIG_SETMASK, mask)

    def ingest(self, retain_keys, language_key):

        current_file_read = 0
        lines_read = 0
        terminate = False

        #import os
        #import psutil

        #p = psutil.Process(os.getpid())
        #p.cpu_affinity([self.count % 20])

        # Iterate while we have a language
        while self.language is not None:

            # Initialize the line
            line = None

            # Initialize the progress
            progress = 0

            # Attempt
            try:

                # Check if the file has finished
                if not current_file_read >= self.current_file_size:

                    # Retrieve the line
                    line = OpenSearchWorker.read_line(self.file)

                    # Update the amount of read lines
                    lines_read += 1

                    # Update the amount read
                    current_file_read += len(line) + 1

                    # Calculate the progress
                    progress = (current_file_read / self.current_file_size) * 100

                # Otherwise
                else:

                    terminate = True

            # Finally
            except:

                print(f'Thread {self.count} - Error')

            # Break condition
            if terminate: break

            # Print out the progress
            OpenSearchWorker.Log.Info(f'Thread {self.count} - Lines Read: {lines_read}, {progress:.1f}%')

            # Initialize the entry
            entry = {key: value for key, value in json.loads(line).items() if key in retain_keys}

            # Brand it
            entry['dataset'] = self.model_name

            # Retrieve the categories for the text value
            categories = self.language(entry[language_key]).cats if language_key in entry else {}

            # Merge the results
            for key, value in categories.items():

                # Set the value
                entry[key] = value

            if 'datatype' in entry and 'createdAt' in entry:

                # Initialize the index name & createdAt
                index = entry['datatype']
                createdAt = entry['createdAt']

                # Delete the key
                del entry['datatype']
                del entry['createdAt']

                # Create the index if it does not exist
                if not self.client.indices.exists(index):

                    # Create it if necessary
                    self.client.indices.create(index, body={
                        'mappings': {
                            'properties': {
                                'username': {'type': 'text', 'analyzer': 'standard'},
                                'creator': {'type': 'text', 'analyzer': 'standard'},
                                'parent': {'type': 'text', 'analyzer': 'standard'},
                                'createdAtformatted': {'type': 'text', 'analyzer': 'standard'},
                                'verified': {'type': 'text', 'analyzer': 'standard'},
                                'impressions': {'type': 'text', 'analyzer': 'standard'},
                                'reposts': {'type': 'text', 'analyzer': 'standard'},
                                'state': {'type': 'text', 'analyzer': 'standard'},
                                'followers': {'type': 'text', 'analyzer': 'standard'},
                                'following': {'type': 'text', 'analyzer': 'standard'},
                                'depth': {'type': 'text', 'analyzer': 'standard'},
                                'comments': {'type': 'text', 'analyzer': 'standard'},
                                'body': {'type': 'text', 'analyzer': 'english'},
                                'bodywithurls': {'type': 'text', 'analyzer': 'english'},
                                'hashtags': {'type': 'text', 'analyzer': 'english'},
                                'POSITIVE': {'type': 'text', 'analyzer': 'standard'},
                                'NEGATIVE': {'type': 'text', 'analyzer': 'standard'},
                            }
                        }
                    })

                # TODO: Shove into open search here
                self.client.index(index, id=f'{entry["creator"]}:{createdAt}', body=entry)

        else:

            if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Info(f'Skipping entry')

def initialize_workers(arguments, config, model, n_threads=1, current_file_size=0, file=None):

    # Log
    if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Info(f'Initializing workers: {n_threads}')

    workers = [
        OpenSearchWorker(config, model, arguments['model_name'], 'alpha.lowerbound.dev', 'us-east-1', current_file_size,
                         file) for index in range(n_threads)]

    language_key = 'body'

    # Initialize the threads
    threads = []

    # Iterate through the workers
    for worker in workers:

        # Initialize & append the thread
        threads.append(threading.Thread(target=worker.bulk_local, args=(retain, language_key)))

    # Log
    if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Info(f'Workers Initialized')

    # Return the set of threads
    return threads

def ingest_s3_files(arguments, n_threads):

    # Download the language model
    config, model = OpenSearchWorker.download_language_model(arguments['modelsbucket'], arguments['model_name'])

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

    # Report to the user
    Log.Info(f'Binding imported construct names')

    # Bind the names
    resource = sys.modules[__name__].resource

    # Initialize the datasets bucket
    datasets_bucket_name    = arguments['datasetsbucket']
    datasets_bucket         = resource('s3').Bucket(datasets_bucket_name)

    # Initialize the objects
    objects = datasets_bucket.objects.filter(Delimiter='/', Prefix=arguments['dataset'])
    objects = [{'key': object.key, 'size': object.size} for object in objects if object.size > 0]

    pool    = []
    chunks  = 20
    count   = 0

    # Iterate through the object
    for object in objects:

        # Update the values
        current_file_size   = object['size']
        current_file        = resource('s3').Object(datasets_bucket_name, object['key']).get()['Body']

        # Initialize the threads
        threads = initialize_workers(arguments, config, model, n_threads, current_file_size, current_file)

        # Iterate through the threads
        for thread in threads:

            # Start
            thread.start()

            # Append
            pool.append(thread)

        # Increment the count
        count += 1

        # If we have the maximum amount of files open
        if count == chunks:

            # Wait
            [thread.join() for thread in pool]

            # Reset the file chunk & pool
            pool = []

            # Reset the count
            count = 0

    if count > 0:

        [thread.join() for thread in pool]

def ingest_local_files(arguments, n_threads, path):

    # Download the language model
    config, model = OpenSearchWorker.download_language_model(arguments['modelsbucket'], arguments['model_name'])

    # Import
    import os
    import mmap

    # Retrieve each file
    files       = [os.path.join(path, file) for file in os.listdir(path) if os.path.isfile(os.path.join(path, file))]
    pool        = []
    chunks      = 1
    count       = 0
    _read_file  = None

    # Iterate through the files
    for file in files:

        # Print out the current file
        if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Info(f'{file}')

        # Open the file
        with open(file, "r+b") as input:

            # Map the file onto memory
            _read_file = mmap.mmap(input.fileno(), 0)

            if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Info(f'File: {file} - Size: {_read_file.size()}')

        # Initialize the threads
        threads = initialize_workers(arguments, config, model, n_threads, _read_file.size(), _read_file)

        # Iterate through the threadscd
        for thread in threads:

            # Start
            thread.start()

            # Append
            pool.append(thread)

        # Increment the count
        count += 1

        # If we have the maximum amount of files open
        if count == chunks:

            # Wait
            [thread.join() for thread in pool]

            # Reset the file chunk & pool
            pool = []

            # Reset the count
            count = 0

    if count > 0:

        [thread.join() for thread in pool]

if __name__ == "__main__":

    # Initialize the log
    OpenSearchWorker.Log = log = Log()

    # Consume the arguments
    args = Arguments(sys.argv, REQUIRED_ARGUMENTS)

    number = int(args['set'])

    ingest_s3_files(args, int(args['threads']))
    #ingest_local_files(args, int(args['threads']), f'/media/cuenca/data/parler_/parler_data/data{number}')
