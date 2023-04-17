## -------
## Imports

import boto3
import re
import json
import os

from html.parser import HTMLParser

FILENAME = ''

REMOVE_KEYS = [
    'duplicated',
    'id',
    'content',
    'onclick',
    'name',
    'rel',
    'property',
    'http-equiv',
    'type',
    'separator',
    'login-more',
    'footer--container',
    'show-comments--wrapper',
    'hide-comments--wrapper',
    'impressions--icon--wrapper',
    'close_side_navigationparler_logo'
]

OMIT = [
    'ms--menu-item',
    'version-text',
    'separator',
    'mc-image--modal--close',
    'gradient-btn bold',
    'mf--fn--item',
    'w--100 gutter--15 container--mainmain-footercopyright',
    'mc-video--wrapper',
    'show-comments--wrappershow-comments-',
    'hide-comments--wrapperhide-comments-',
    'show-replies--wrappershow-replies-',
    'hide-replies--wrapperhide-replies-'
]

## -------
## Classes

class Log:
    """
    A class representing a logger that reports (structured) events.
    """

    ## -------
    ## Imports

    from datetime import datetime

    ## --------------
    ## Static Methods

    @staticmethod
    def warn(message: str):
        """
        Outputs the specified message with a warning level.
        :param message: The message string to output
        """
        # Output the message with a timestamp
        print(f'{Log.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | {FILENAME} | Warn | {message}')

    @staticmethod
    def info(message: str):
        """
        Outputs the specified message with an info level.
        :param message: The message string to output
        """
        # Output the message with a timestamp
        print(f'{Log.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | {FILENAME} | Info | {message}')

    ## ------------
    ## Constructors

    def __init__(self):
        pass

class HTMLToDictionaryParser(HTMLParser):
    """
    A Simple HTML parser that reads an html markup file and produces a semantically
    equivalent dict, preserving the html's structure, attributes, and data.
    Attributes
    ----------
    root : dict
        The .html file's root container
    """

    ## --------------
    ## Static Methods

    @staticmethod
    def set_or_duplicate(target: dict, key, value) -> None:
        """
        Sets the key-value pair to the specified dictionary if the key-value pair does not exist;
        otherwise this will create a list with the current & new values and update the entry.
        This method will insert a 'duplicated' key into the target dictionary if it doesn't already
        exist.
        :param target: The dictionary to aggregate the key-value pair
        :param key: The key corresponding to the value
        :param value: The value corresponding with the key
        """

        # Initialize a duplicated list if the target does not contain a 'duplicated' key
        if 'duplicated' not in target: target['duplicated'] = []

        # If the target does not contain the key
        if key not in target:

            # Set the key-value pair as-is
            target[key] = value

        # Otherwise, we have a duplicate
        else:

            # If we haven't encountered a duplicate
            if key not in target['duplicated']:

                # Update the value as a list
                target[key] = [target[key], value]

                # Update the duplicated flag
                target['duplicated'].append(key)

            # Otherwise, we must have a list
            else:

                # Simply append
                target[key].append(value)

    @staticmethod
    def list_to_string(data) -> str:

        if not isinstance(data, list): return data

        result = ''

        if data is not None:

            for index in range(len(data)):

                result += data[index]

                if index > len(data) - 1:

                    result += ' '

        return result

    @staticmethod
    def merge(target: dict, source: dict) -> None:
        """
        Merges the key-value pairs from the source dictionary to the target dictionary.
        :param target: The dictionary to aggregate key-value pairs from the source
        :param source: The dictionary containing the key-value pairs to aggregate
        """

        # Report the event
        Log.info(f'merging source into target')

        if source is not None:

            # Iterate through the attributes and append the key-value pairs into the target dictionary
            for key, value in source.items():

                # Aggregate the key-value pair into the target
                HTMLToDictionaryParser.set_or_duplicate(target, key, value)

                # Report the aggregation
                Log.info(f'aggregated {key}:{value} into target')

    ## ------------
    ## Constructors

    def __init__(self, filename: str):
        """
        Default constructor. Initializes the HTMLToDictionaryParser to its' default state.
        :param filename: The string value corresponding to the html file to process
        """
        super().__init__()

        # Initialize the members
        self.attributes_index   = {}
        self.keys_index         = {}
        self.root               = {'filename': filename}
        self.parent             = self.root
        self.current            = self.root
        self.current_key        = 'root'
        self.stack              = []

        # Open the file
        with open(filename, 'r') as input_file:

            # And feed it into our parser
            self.feed(input_file.read())

    ## -------
    ## Methods

    def handle_starttag(self, tag: str, attributes: list[tuple[str, str]]) -> None:
        """
        Invoked when the HTMLToDictionaryParser has encountered an html opening tag.
        Depending on the length of the attributes parameter, this method will either:
            1) Create a child dictionary within the current dictionary with the class attribute
            value as the key
            or
            2) Do nothing if the attributes parameter is empty; this will cause any future data
            to be appended to the current dictionary
        :param tag: The string value corresponding to the html tag
        :param attributes: The html tag's specified attributes
        """
        # Log the event
        Log.info(f'start tag: \"{tag}\" attributes: {str(attributes)}')

        # Check if the tag contained a set of attributes & the attributes included a class
        if len(attributes) > 0:

            # Convert the list into a dictionary
            attributes = {key: value for key, value in attributes}

            # If the attributes dictionary contains a key 'class'
            if 'class' in attributes and attributes['class'] != '':

                # Push the current key and entry onto the stack
                self.stack.append((self.current_key, self.current))

                # Initialize the child & key
                self.current_key = HTMLToDictionaryParser.list_to_string(attributes['class'])
                self.current = {}

                # Remove the 'class' key-value pair
                del attributes['class']

                # Insert into the keys index
                HTMLToDictionaryParser.set_or_duplicate(self.keys_index, self.current_key, True)

                # Report the event
                Log.info(f'{self.stack[-1][0]} aggregated child {self.current_key}')

            # Merge the attributes into the current dictionary & index the keys
            HTMLToDictionaryParser.merge(self.current, attributes)

            # Report the event
            Log.info(f'merged attributes into {self.current_key}')

    def handle_data(self, data: str) -> None:
        """
        Invoked when the HTMLToDictionaryParser has encountered data.
        The specified data will be appended to the current dictionary.
        :param data: The string value corresponding to the data
        """
        # If we have valid data:
        if data is not None:

            # Scrub the data
            data = re.sub(r'[\t\f\r\n ]+', ' ', data)

            # Check if the data is a single space
            if data != '' and data != ' ':

                # Report the event
                Log.info(f'received data: {data}')

                # Set the data
                HTMLToDictionaryParser.set_or_duplicate(self.current, 'data', data)

    def handle_endtag(self, tag: str) -> None:
        """
        Invoked when the HTMLToDictionaryParser has encountered an html closing tag.
        This will update the current dictionary to the current dictionary's parent, and
        the parent to the current dictionary's grandparent.
        :param tag: The string value corresponding to the html tag
        """

        if len(self.stack) > 0:

            # Initialize a handle to the current child
            child_id    = self.current_key
            child       = self.current

            # Update the current key and the current entry
            self.current_key, self.current = self.stack.pop()

            # If we even received anything
            if len(child) > 0:

                # Set the child's key-value pair onto the parent
                HTMLToDictionaryParser.set_or_duplicate(self.current, child_id, child)

                # Iterate through the key-value pairs of the child
                for key, value in child.items():

                    # If the value is not a dictionary or list (we already indexed the children)
                    if not isinstance(value, dict) and not isinstance(value, list):

                        # Merge it into the index
                        HTMLToDictionaryParser.set_or_duplicate(self.attributes_index, key, value)

                        # Report the event
                        Log.info(f'aggregated {key}:{value} into index')

            # Report the event
            Log.info(f'Closing {child_id}')

    def index(self) -> dict:
        """
        Returns the resultant attributes index composed of the keys the parser encountered.
        :return: dictionary containing the keys the parser encountered while processing the specified file
        """
        return self.attributes_index

    def dictionary(self) -> dict:
        """
        Returns the resultant dictionary corresponding to the html document the parser processed
        :return: dictionary corresponding to the html document the parser processed.
        """
        return self.root

    def keys(self) -> dict:
        """
        Returns the resultant keys index corresponding to the html document the parser processed
        :return: dictionary corresponding to the keys the parser encountered.
        """
        return self.keys_index

def handler(event, context): 

    table_name  = event['table_name']
    input_name  = event['input_bucket']
    output_name = event['output_bucket']

    input_bucket = boto3.resource('s3').Bucket(input_name)
    output_bucket = boto3.resource('s3').Bucket(output_name)
    table = boto3.resource('dynamodb').Table(table_name)

    for obj in input_bucket.objects():
        with open(obj.key, 'wb') as data:
            input_bucket.download_fileobj(obj.key, data)
            # table.put_item(Item=ParlerParser(data).result)
            output_bucket.upload_file(obj.key, obj.key)
        
        input_bucket.delete_objects(Delete={"Objects": [{"Key": obj.key}]})

    return {}

def snake_case(value):

    # Attempt to convert the value into a string
    value = str(value) if not isinstance(value, str) else value

    # Return the result of consolidating spaces of the lowercase string
    return re.sub(r'[\t\f\r\n ]+', '_', value.lower())

def traverse(data, callback):

    Log.warn(f'Traversing: {data}')

    # If the data is a list
    if isinstance(data, list):

        # Create a new list with the result of this method
        data = [traverse(child, callback) for child in data]

    # Otherwise, if the data is a dictionary
    elif isinstance(data, dict):

        # Set each key's value to the result of this method
        data = {key: traverse(child, callback) for key, child in data.items()}

    # Return the result of the callback, if any
    return callback(data) if callback is not None else data

def starts_with(key, other):

    return key.startswith(other) if key is not None else False

class MergeValueAsKeyCallback:
    """
    Defines a callback that converts a value to a key, and assigns an existing, sibling
    value as it's value
    """

    ## -----------
    ## Constructor

    def __init__(self, value_to_key=None, key=None, transform=None, callback=None):

        self.value_to_key   = value_to_key
        self.key            = key
        self.transform      = transform
        self.callback       = callback

    ## ---------
    ## Overloads

    def __call__(self, value):

        # If the value is a list
        if isinstance(value, list):

            # Set the result to the modified list
            value = [self(child) for child in value]

        # Otherwise, if the value is a dictionary & if we have a valid set of keys
        elif isinstance(value, dict) and self.value_to_key is not None and self.key is not None:

            # If the keys exist in the dictionary
            if self.value_to_key in value and self.key in value:

                Log.info(f'Converting {self.value_to_key} to key with value {value[self.key]}')

                # Retrieve the value to be set as a key, and the corresponding value
                new_key     = value[self.value_to_key]
                existing    = value[self.key]

                # If the value to be turned into a key is not empty
                if not RemoveEmptyCallback.is_empty(new_key):

                    # Remove the existing key-value pairs
                    del value[self.value_to_key]
                    del value[self.key]

                    # If we have a transformation function, transform the key
                    if self.transform is not None: new_key = self.transform(new_key)

                    # Set the new key-value pair
                    HTMLToDictionaryParser.set_or_duplicate(value, new_key, existing)

            # Reset the value
            value = {key: self(child) for key, child in value.items()}

        # Return the result
        return self.callback(value) if self.callback is not None else value

class MergeLeavesCallback:
    """
    Defines a callback that merges the leaves of a piece of data onto the parent.
    """

    ## --------------
    ## Static Methods

    @staticmethod
    def flatten(result, value):

        Log.warn(f'Flattening {value}')

        # If the value is a dictionary
        if isinstance(value, dict):

            Log.warn(f'Value is dictionary')

            # Iterate through the key-value pairs
            for child_key, child in value.items():

                # Update the child
                child = MergeLeavesCallback.flatten(result, child)

                # If the child is not empty
                if not RemoveEmptyCallback.is_empty(child):

                    # Set the child
                    HTMLToDictionaryParser.set_or_duplicate(result, child_key, child)

            # Clear the value
            value.clear()

        # Otherwise, if the value is a list
        elif isinstance(value, list):

            Log.warn(f'Value is list')

            # Recur on the children
            value = [MergeLeavesCallback.flatten(result, child) for child in value]

            # Filter out the empty results
            value = [child for child in value if not RemoveEmptyCallback.is_empty(child)]

        Log.warn(f'Result: {value}')

        # Finally, return the result
        return value

    ## -----------
    ## Constructor

    def __init__(self, key=None, callback=None, condition=None):

        self.key        = key
        self.callback   = callback
        self.condition  = condition

    ## --------
    ## Overload

    def __call__(self, value):

        # If the value is a dictionary & it contains the specified key
        if isinstance(value, dict):

            # If we have a condition
            if self.condition is not None:

                found_keys = [key for key in value.keys() if self.condition(key, self.key)]

                for key in found_keys:

                    # Initialize the result
                    result = {}

                    # Flatten the value into the result
                    MergeLeavesCallback.flatten(result, value[key])

                    # Delete the key-value pair
                    del value[key]

                    # Set the key-value pair
                    HTMLToDictionaryParser.set_or_duplicate(value, key, result)

        # Return the value
        return self.callback(value) if self.callback is not None else value

class RemoveKeyCallback:
    """
    Defines a callback that recursively removes the specified key from a given value
    """

    ## ------------
    ## Constructors

    def __init__(self, key=None, callback=None):
        """
        Initializes the RemoveKeyCallback with the specified key and callback
        :param key: The key to potentially remove
        :param callback: The callback to invoke after key removal
        """
        self.key        = key
        self.callback   = callback

    ## ---------
    ## Overloads

    def __call__(self, value):
        """
        Removes any key-value pairs that correspond with the specified key.
        This method will keep track of the deleted values.
        :param value: The value to delete the key from
        :return: Potentially modified value
        """

        # If the value is a dictionary & we have a valid key
        if isinstance(value, dict) and self.key is not None:

            # If the value contains the key
            if self.key in value:

                # Report the event
                Log.info(f'Removing {self.key}: {value[self.key]}')

                # Remove it
                del value[self.key]

        # Return the result of the value passed through the callback, if any
        return self.callback(value) if self.callback is not None else value

class RemoveEmptyCallback:
    """
    Defines a callback that returns a filtered list; specifically checked against empty values.
    """

    ## --------------
    ## Static Methods

    @staticmethod
    def is_empty(value):
        """
        Returns a boolean flag indicating if the specified value is empty or if the value is a string, is blank
        :param value: The value to check
        :return: boolean flag indicating if the value is empty or blank
        """

        # Initialize the initial result
        result = (isinstance(value, list) or isinstance(value, dict)) and len(value) == 0

        # Return the choice between the initial or string condition
        return result or (isinstance(value, str) and (len(re.sub(r'[\t\f\r\n ]+', '', value)) == 0))

    ## ------------
    ## Constructors

    def __init__(self, callback=None):

        self.callback = callback

    ## ---------
    ## Overloads

    def __call__(self, value):
        """
        Invocation overload. Returns a list containing non-empty or non-blank elements (in the case of strings)
        if the specified value is a list. Otherwise, it returns the unchanged value.
        :param value: The value to filter
        :return: Modified value
        """

        # If the value is a list
        if isinstance(value, list):

            # Set the value to the filtered list
            value = [child for child in value if not RemoveEmptyCallback.is_empty(child)]

        # If the value is a dictionary
        elif isinstance(value, dict):

            # Set the value to a filtered dictionary
            value = {key: child for key, child in value.items() if not RemoveEmptyCallback.is_empty(child)}

        # Finally, return the value
        return self.callback(value) if self.callback is not None else value

class PullSingleUpCallback:
    """
    Defines a callback that returns a modified value with single children being pulled up to the level of
    the parent
    """

    ## ------------
    ## Constructors

    def __init__(self, callback=None):

        self.key        = None
        self.callback   = callback

    ## ---------
    ## Overloads

    def __call__(self, value):
        """
        Pulls any single member up to the level of the parent
        :param value: The value to check
        :return: Modified value or same
        """

        # If the value is a list
        if isinstance(value, list):

            # Set the value to the only element in the list
            value = value[0] if len(value) == 1 else [self(child) for child in value]

        # If the value is a dictionary
        elif isinstance(value, dict) and len(value) > 0:

            # If the value contains a single element
            if len(value) == 1:

                # Set the current key
                self.key = [key for key in value.keys()][0]

                if self.key == 'data':

                    # Report the event
                    Log.info(f'Pulling member {value[self.key]} up')

                    # Set the result
                    result = value[self.key]

                    # Delete the current entry
                    del value[self.key]

                    # Assign the result
                    value = result

            # Otherwise, we have some elements
            else:

                # Initialize the result
                new_value = {}
                remove_keys = []

                # Iterate through the key value pairs
                for key, child in value.items():

                    # Add to the remove keys
                    remove_keys.append(key)

                    # Recur to set the key
                    result = self(child)

                    # Initialize the new key
                    new_key = f'{key} {self.key}' if self.key is not None else key

                    # Report the event
                    Log.info(f'Writing {key}: {value[key]} to {new_key}: {result}')

                    # Initialize the key-value pair
                    HTMLToDictionaryParser.set_or_duplicate(new_value, new_key, result)

                    # Reset the key
                    self.key = None

                # Iterate through the remove keys and clear out the old value
                for key in remove_keys: del value[key]

                # Set the result
                value = new_value

        # Return the result
        return self.callback(value) if self.callback is not None else value

## ------------
## Script Start

mega_index  = {}
mega_keys   = {}

remove_duplicated   = RemoveKeyCallback('duplicated')
pull_single_members = PullSingleUpCallback()

for filename in os.listdir('sample'):

    FILENAME = filename

    # Start the parser
    parser = HTMLToDictionaryParser(f'sample/{filename}')

    # Remove the 'duplicated' keys
    dictionary = traverse(parser.dictionary(), remove_duplicated)

    # Remove the 'footer--container' key
    dictionary = traverse(dictionary, RemoveKeyCallback('footer--container'))

    # Remove the 'login-more' key
    dictionary = traverse(dictionary, RemoveKeyCallback('login-more'))

    # Remove the 'hide-comments--wrapper' key
    dictionary = traverse(dictionary, RemoveKeyCallback('hide-comments--wrapper'))

    # Remove the 'show-comments--wrapper' key
    dictionary = traverse(dictionary, RemoveKeyCallback('show-comments--wrapper'))

    # Remove the 'impressions-icon--wrapper' key
    dictionary = traverse(dictionary, RemoveKeyCallback('impressions--icon--wrapper'))

    # Remove the 'mc-video--link--icon' key
    dictionary = traverse(dictionary, RemoveKeyCallback('mc-video--link--icon'))

    # Remove the 'id' key
    dictionary = traverse(dictionary, RemoveKeyCallback('id'))

    # Remove the 'type' key
    dictionary = traverse(dictionary, RemoveKeyCallback('type'))

    # Remove the 'onclick' key
    dictionary = traverse(dictionary, RemoveKeyCallback('onclick'))

    # Merge the echo fields
    dictionary = traverse(dictionary, MergeLeavesCallback('eb--col', condition=starts_with))

    # Remove any duplicated
    dictionary = traverse(dictionary, remove_duplicated)

    # Merge the ca-item--count fields with the alt
    dictionary = traverse(dictionary, MergeValueAsKeyCallback('alt', 'ca--item--count', snake_case))

    # Merge the pa-item--count fields with the alt
    dictionary = traverse(dictionary, MergeValueAsKeyCallback('alt', 'pa--item--count', snake_case))

    # Merge the src fields with the alt
    dictionary = traverse(dictionary, MergeValueAsKeyCallback('alt', 'src', snake_case))

    # Remove any duplicated
    dictionary = traverse(dictionary, remove_duplicated)

    # Remove the separator key
    dictionary = traverse(dictionary, RemoveKeyCallback('separator'))

    # Merge the media container
    dictionary = traverse(dictionary, MergeLeavesCallback('media-container--wrapper', condition=starts_with))

    # Remove any duplicated
    dictionary = traverse(dictionary, remove_duplicated)

    # Pull single members up
    dictionary = traverse(dictionary, pull_single_members)

    # Remove any duplicated
    dictionary = traverse(dictionary, remove_duplicated)

    # Merge the card--header leaves
    dictionary = traverse(dictionary, MergeLeavesCallback('card--header', condition=starts_with))

    # Remove any duplicated
    dictionary = traverse(dictionary, remove_duplicated)

    # Merge the card--footer leaves
    dictionary = traverse(dictionary, MergeLeavesCallback('card--footer', condition=starts_with))

    # Remove any duplicated
    dictionary = traverse(dictionary, remove_duplicated)

    # Merge the echo by leaves
    #dictionary = traverse(dictionary, MergeLeavesCallback('echo-byline--wrapper', condition=starts_with))

    # Remove any duplicated
    #dictionary = traverse(dictionary, remove_duplicated)

    # Merge the comment--card--wrapper leaves
    #dictionary = traverse(dictionary, MergeLeavesCallback('comment--card--wrapper', condition=starts_with))

    # Remove any duplicated
    #dictionary = traverse(dictionary, remove_duplicated)

    # Merge the reblock leaves
    #dictionary = traverse(dictionary, MergeLeavesCallback('reblock', condition=starts_with))

    # Remove any duplicated
    #dictionary = traverse(dictionary, remove_duplicated)


    # Merge the index to the mega
    HTMLToDictionaryParser.merge(mega_index, parser.index())
    HTMLToDictionaryParser.merge(mega_keys, parser.keys())

    # Transform the filename
    filename = re.sub(r'\.html', '', filename)

    # Write index
    with open(f'output/{filename}-index.json', 'w') as output_file:

        output_file.write(json.dumps(parser.index(), indent=4))

    # Write keys index
    with open(f'output/{filename}-keys.json', 'w') as output_file:

        output_file.write(json.dumps(parser.keys(), indent=4))

    # Write result
    with open(f'output/{filename}.json', 'w') as output_file:

        output_file.write(json.dumps(dictionary, indent=4))

# Finally, write the mega index
with open(f'mega_index.json', 'w') as output_file:

    output_file.write(json.dumps(mega_index, indent=4))

# Finally, write the mega keys
with open(f'mega_keys.json', 'w') as output_file:

    output_file.write(json.dumps(mega_keys, indent=4))

