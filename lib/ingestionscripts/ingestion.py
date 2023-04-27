## -------
## Imports

import sys
import json
import time
import threading
import signal
import os
import re

from pathlib import Path
from datetime import datetime
from log import Log
from arguments import Arguments

REQUIRED_ARGUMENTS = ['datasetsbucket', 'dataset', 'modelsbucket', 'model_name', 'threads']  # , 'endpoint', 'region']
# TODO: Make this into a parameter
retain = ['body',
          'comments',
          'creator',
          'createdAtformatted',
          'datatype',
          'depth',
          'followers',
          'following',
          'hashtags',
          'id',
          'impressions',
          'parent',
          'posts',
          'reposts',
          'username',
          'upvotes']

class OpenSearchWorker:

    ## -------------
    ## Static Fields

    Log     = None
    Count   = 0
    Bucket  = None
    Key     = None

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
        AWS4Auth                = sys.modules[__name__].AWS4Auth
        OpenSearch              = sys.modules[__name__].OpenSearch
        RequestsHttpConnection  = sys.modules[__name__].RequestsHttpConnection
        Session                 = sys.modules[__name__].Session

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
                           'package_name': 'botocore'
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

    def __init__(self, config, model, model_name, retain_keys=[],
                 endpoint='', region='', file_size=0, file=None, method='s3', destination='opensearch'):

        # If we have a valid model name and bucket
        if config is not None and model is not None and file is not None:

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

            # Initialize the client
            self.client = OpenSearchWorker.initialize_open_search_client(endpoint, region)

            # Initialize the model
            self.language           = OpenSearchWorker.initialize_language_model(config, model)
            self.model_name         = model_name
            self.file               = file
            self.retain_keys        = retain_keys
            self.terminate          = False
            self.lines_read         = 0
            self.current_file_read  = 0
            self.progress           = 0
            self.local_count        = 0
            self.mask               = None
            self.start_time         = None
            self.action_count       = 1000
            self.actions            = []
            self.indices            = []
            self.current_file_size  = file_size
            self.count              = OpenSearchWorker.Count
            self.thread             = threading.Thread(target=self.ingest)
            self.bucket             = resource('s3').Bucket(OpenSearchWorker.Bucket)
            self.root_key           = OpenSearchWorker.Key

            # If the method of retrieval is s3
            if method == 's3':

                self.line_from_file = lambda worker: OpenSearchWorker.read_line(worker.file)

            # Otherwise
            else:

                self.line_from_file = lambda worker: worker.file.readline()

            # If the upload destination is s3
            if destination == 'opensearch':

                self.set_entry      = self.set_entry_from
                self.ingest_index   = self.attempt_index

            else:

                self.set_entry      = self.set_s3_entry_from
                self.ingest_index   = None

            # Increment the count
            OpenSearchWorker.Count += 1

    def bind_to_thread(self):

        import psutil

        # Set the affinity
        p = psutil.Process(os.getpid())
        p.cpu_affinity([self.count])

        # Prevent from being interrupted
        self.mask = signal.pthread_sigmask(signal.SIG_BLOCK, {})
        signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT})

    def unbind_from_thread(self):

        # Allow interruptions
        signal.pthread_sigmask(signal.SIG_SETMASK, self.mask)

    def update_metrics(self, line):

        # Update the amount of read lines
        self.lines_read += 1

        # Update the amount of bytes read
        self.current_file_read += len(line) + 1

        # Update the local count
        self.local_count += 1

        # Print out the progress
        if OpenSearchWorker.Log is not None and self.local_count >= self.action_count:

            # Calculate the progress
            self.progress = (self.current_file_read / self.current_file_size) * 100

            # Calculate the rate
            rate = self.lines_read / (time.time() - self.start_time)

            # Clear the local count
            self.local_count = 0

            # Report
            OpenSearchWorker.Log.Info(f'Thread {self.count} - Lines Read: {self.lines_read}, {self.progress:.1f}% - {rate:.1f} lines/second')

    def create_if_not_exists(self, index):

        # If the index does not exist
        if not self.client.indices.exists(index):

            # Create it
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

            # Log
            if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Info(f'Created index: {index}')

    def set_entry_from(self, line):

        # Initialize the entry
        entry = {key: value for key, value in json.loads(line).items() if key in self.retain_keys}

        # Brand it
        entry['dataset'] = self.model_name

        # Retrieve the categories for the text value
        categories = self.language(entry['body']).cats if 'body' in entry else {}

        # Merge the results
        for key, value in categories.items():

            # Set the value
            entry[key] = value

        if 'datatype' in entry and 'createdAtformatted' in entry:

            # Initialize the index name & createdAt
            index       = entry['datatype']
            createdAt   = entry['createdAtformatted']

            # Create the action
            action  = json.dumps({'index': {'_index': index, "_id": f'{entry["creator"]}:{createdAt}'}}) + '\n'
            action += json.dumps(entry) + '\n'

            # Append it
            self.actions.append(action)

            # If the index is not in the list of indices
            if index not in self.indices:

                # Check if we should create it
                self.create_if_not_exists(index)

                # Append it to the list
                self.indices.append(index)

    def set_s3_entry_from(self, line):

        # Initialize the entry
        entry = {key: value for key, value in json.loads(line).items() if key in self.retain_keys}

        # Brand it
        entry['dataset'] = self.model_name

        # Retrieve the categories for the text value
        categories = self.language(entry['body']).cats if 'body' in entry else {}

        # Merge the results
        for key, value in categories.items():

            # Set the value
            entry[key] = value

        if 'datatype' in entry and 'createdAtformatted' in entry:

            # Calculate the amount of seconds
            created = entry['createdAtformatted'].split(' ')
            created = created[0] + ' ' + created[1]

            date    = created.split(' ')[0].split('-')
            created = datetime.strptime(created, '%Y-%m-%j %H:%M:%S')

            # Compute the seconds
            seconds = (created - datetime(1970, 1, 1)).total_seconds()

            # Set them to the entry
            entry['seconds'] = seconds

            # Initialize the key
            key = f'/media/cuenca/data/parler_/processed/{date[0]}_{date[1]}_{date[2]}.json'

            # If the file does not exist
            if not Path(key).is_file():

                # Simply create it
                with open(key, 'w') as output:

                    # Write
                    output.write(json.dumps(entry))

            # Otherwise
            else:

                # Open in append mode
                with open(key, 'a') as output:

                    # Write
                    output.write(f'\n{json.dumps(entry)}')

            # Bind the entry
            #self.bucket.put_object(Key=f'{key}', Body=bytes(json.dumps(entry).encode('utf-8')))

    def attempt_index(self):

        terminate = False

        # Keep trying
        while not terminate:

            try:

                # Bulk upload
                self.client.bulk(self.actions)

                # Leave
                terminate = True

            except:

                if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Info(f'Retrying index')

        # Clear the actions
        self.actions = []

    def ingest(self):

        # Bind the thread
        self.bind_to_thread()

        # Mark the start time
        self.start_time = time.time()

        if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Info(f'Thread {self.count} - Starting ingestion')

        # While we haven't consumed the entire file
        while self.current_file_read < self.current_file_size:

            # Attempt
            try:

                # To read the line
                line = self.line_from_file(self)

                # Set the entry
                self.set_entry(line)

                # Update the metrics
                self.update_metrics(line)

                # Check if we reached the maximum amount of actions
                if len(self.actions) == self.action_count and self.ingest_index is not None:

                    # Attempt to index
                    self.ingest_index()

            except:

                # Log the error
                if OpenSearchWorker.Log is not None:

                    # Log the error
                    OpenSearchWorker.Log.Info(f'Thread {self.count} - Error; terminating')

                # Leave
                break

        # Unbind from the thread
        self.unbind_from_thread()

<<<<<<< HEAD
def ingest_s3_files(arguments, chunks):
=======
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

        import os
        import psutil

        p = psutil.Process(os.getpid())
        p.cpu_affinity([self.count % 20])

        actions = []
        bulk    = 1000

        while self.language is not None and True:

            # Iterate while we have a language
            for count in range(bulk):

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
                    index       = entry['datatype']

                    # Delete the key
                    del entry['datatype']

                    # Add to actions
                    actions.append({'index': entry})

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

                # Bulk upload
                self.client.bulk(actions, index=index)

        else:

            if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Info(f'Skipping entry')

    def ingest(self, retain_keys, language_key):

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
        threads.append(threading.Thread(target=worker.ingest, args=(retain, language_key)))

    # Log
    if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Info(f'Workers Initialized')

    # Return the set of threads
    return threads

def ingest_s3_files(arguments, n_threads):
>>>>>>> 6c4e96d (Update training script)

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
    datasets_bucket_name = arguments['datasetsbucket']
    datasets_bucket      = resource('s3').Bucket(datasets_bucket_name)
    dataset              = arguments["dataset"]

    # Initialize the objects
    objects = datasets_bucket.objects.all()
    objects = [{'key': file.key, 'size': file.size} for file in objects if file.key.startswith(dataset) and file.size > 0]
    pool    = []

    # Iterate through the object
    for current_file in objects:

        # Update the values
        current_file_size = current_file['size']
        current_file      = resource('s3').Object(datasets_bucket_name, current_file['key']).get()['Body']

        # Log
        if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Info(f'Initializing worker')

        # Initialize the worker; Retrieve from s3, upload to s3
        worker = OpenSearchWorker(config, model, arguments['model_name'], retain, 'alpha.lowerbound.dev', 'us-east-1',
                                  current_file_size, current_file, 's3', 's3')

        # Log
        if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Info(f'Worker Initialized')

        # Start the thread
        worker.thread.start()

        # Append the thread
        pool.append(worker.thread)

        # Check if we should wait
        if len(pool) == chunks:

            # Wait
            [thread.join() for thread in pool]

            # Reinit
            pool = []

            # Reset the count
            OpenSearchWorker.Count = 0

def ingest_local_files(arguments, chunks, path):

    # Download the language model
    config, model = OpenSearchWorker.download_language_model(arguments['modelsbucket'], arguments['model_name'])

    # Import
    import os
    import mmap

    # Retrieve each file
    files       = [os.path.join(path, file) for file in os.listdir(path) if os.path.isfile(os.path.join(path, file))]
    pool        = []
    _read_file  = None

    # Iterate through the files
    for file in files:

        # Print out the current file
        if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Info(f'{file}')

        # Open the file
        with open(file, "r+b") as input:

            # Map the file onto memory
            _read_file = mmap.mmap(input.fileno(), 0)

            # Log
            if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Info(f'File: {file} - Size: {_read_file.size()}')

        # Initialize the current file size
        current_file_size = _read_file.size()

        # Log
        if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Info(f'Initializing worker')

        # Initialize the worker; retrieve local, upload to s3
        worker = OpenSearchWorker(config, model, arguments['model_name'], retain, 'alpha.lowerbound.dev', 'us-east-1',
                                  current_file_size, _read_file, 'local', 's3')

        # Log
        if OpenSearchWorker.Log is not None: OpenSearchWorker.Log.Info(f'Worker Initialized')

        # Start the thread
        worker.thread.start()

        # Append the thread
        pool.append(worker.thread)

        # Check if we should wait
        if len(pool) == chunks:

            # Wait
            [thread.join() for thread in pool]

            # Reinit
            pool = []

if __name__ == "__main__":

    # Initialize the log
    OpenSearchWorker.Log = log = Log()

    # Consume the arguments
    args = Arguments(sys.argv, REQUIRED_ARGUMENTS)

    # Set the class-wide variables
    OpenSearchWorker.Bucket = args['datasetsbucket']
    OpenSearchWorker.Key    = args['dataset']

    # Ingest
    #ingest_s3_files(args, int(args['threads']))
    ingest_local_files(args, int(args['threads']), f'/media/cuenca/data/parler_/parler_data/data{int(args["set"])}')
