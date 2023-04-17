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
    def Warn(message: str):
        """
        Outputs the specified message with a warning level.
        :param message: The message string to output
        """
        # Output the message with a timestamp
        print(f'{Log.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | Warn | {message}')

    @staticmethod
    def Info(message: str):
        """
        Outputs the specified message with an info level.
        :param message: The message string to output
        """
        # Output the message with a timestamp
        print(f'{Log.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | Info | {message}')

    @staticmethod
    def Error(message: str):
        """
        Outputs the specified message with an error level; terminates the execution
        :param message: The message string to output
        """
        # Output the message with a timestamp
        print(f'{Log.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | Info | {message}')

        # Exit
        exit(1)

    ## ------------
    ## Constructors

    def __init__(self):
        pass
