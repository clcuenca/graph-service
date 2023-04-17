## -------
## Imports

import re


## -----
## Class

class Arguments:
    """
    Class that contains command-line arguments in a neat format.
    @author Carlos L. Cuenca
    """

    ## --------------
    ## Static Methods

    @staticmethod
    def parse_from(arguments: list) -> dict:
        """
        Reads in the arguments from the list and groups the contents into key-value pairs
        :param arguments: The string arguments to parse
        :return: dictionary containing the arguments
        """

        # Initialize the result
        result = {}
        index = 0

        # Iterate through the range of arguments
        while index < len(arguments):

            # If we have an argument
            if arguments[index] is not None and arguments[index].startswith('-'):

                # Initialize the key, argument & increment the index
                key = re.sub(r'-+', '', arguments[index])
                index += 1

                # Check if the key is in the collection
                if key not in result:
                    # Initialize the argument to None
                    result[key] = None

                # Sub-iterate
                while index < len(arguments) and not arguments[index].startswith('-'):

                    # Check if we have a key
                    if result[key] is None:

                        # Initialize the argument
                        result[key] = arguments[index]

                    # Otherwise
                    else:

                        # If the value is not already a list
                        if not isinstance(result[key], list):
                            # Reset the value
                            result[key] = [result[key]]

                        # Append the current argument
                        result[key].append(arguments[index])

                    # Increment the index
                    index += 1

            # Otherwise
            else:

                # Increment the index
                index += 1

        # Finally, return the result
        return result

    ## ---------
    ## Overloads

    def __init__(self, arguments):
        """
        Initializes the Arguments instance to its' default state.
        :param arguments: The arguments list to parse
        """

        # Initialize the collection
        self.dictionary = Arguments.parse_from(arguments)
        self.count = len(self.dictionary)

    def __dict__(self):
        """
        Returns the dict representation of the Arguments instance
        :return: dict containing the arguments as key-value pairs
        """

        return self.dictionary

    def __getitem__(self, item):
        """
        Returns the value corresponding with the specified item
        :param item: The key corresponding to the value to retrieve
        :return: The value corresponding with the key
        """

        return self.dictionary[item]
