## -------
## Classes

class MLTrainer:
    """
    Base Machine Learning training class. Defines helper methods to train machine learning models.
    :author: Carlos L. Cuenca
    """

    ## -------------
    ## Static Fields

    Log = None

    ## --------------
    ## Static Methods

    @staticmethod
    def tuple_from(data: dict, columns: dict, callback=None) -> tuple:
        """
        Creates a tuple from the specified collection dictionary's value if the key corresponding to the value
        exists in the specified columns dictionary. For each column, if a transformation callback exists, the value
        is set to the result of the transformation, otherwise the value is appended to the resultant tuple as-is.
        If the specified callback is not None, then the result is transformed to the result of that callback.
        :param data: The data to collect as a Tuple
        :param columns: The columns to aggregate to the resultant tuple
        :param callback: The final callback whose result is returned if defined.
        :return: Tuple containing the (potentially transformed) data corresponding to the specified columns.
        """

        # Initialize the result
        result = ()

        # Check if we have valid parameters
        if data is not None and columns is not None:

            # Iterate through each item
            for key, value in data.items():

                # If the key is specified in the columns
                if key in columns:

                    # Append the value (potentially transformed
                    result = result + ((columns[key](value) if columns[key] is not None else value),)

        # Return the result
        return callback(result) if callback is not None else result

    @staticmethod
    def prepare(data, columns: dict, separator: str, split: float) -> tuple:
        """
        Prepares the training & evaluation dataset from the specified data, columns, separator, & split ratio.
        Each key-value pair in the columns collection contains the column as a key & a transformation callback as a
        value. If the transformation callback for a specified column is None, the value is appended to the result as-is.
        :param data: The data to prepare
        :param columns: The columns to aggregate to the result, potentially transformed
        :param separator: The sequence that separates each column
        :param split: The ratio to split the data
        :return: A tuple containing the training & evaluation datasets as a list of tuples
        """

        # Initialize the functions
        read_csv = MLTrainer.pandas.read_csv
        shuffle  = MLTrainer.random.shuffle

        # Report to the user
        if MLTrainer.Log is not None: MLTrainer.Log.Info(f'Preparing data; separator: \'{separator}\' split: \'{split}\'')

        # Read the csv data
        dataset = read_csv(data, sep=separator)[columns.keys()].dropna()

        # Report to the user
        if MLTrainer.Log is not None: MLTrainer.Log.Info(f'Data extracted, forming tuples')

        # Extract the values as a list of tuples
        dataset = dataset.apply(lambda row: MLTrainer.tuple_from(row, columns), axis=1).tolist()

        # Report to the user
        if MLTrainer.Log is not None: MLTrainer.Log.Info(f'Shuffling data')

        # Shuffle the list
        shuffle(dataset)

        # Retrieve the amount of entries for the training set
        index = int(len(dataset) * split)

        # Report to the user
        if MLTrainer.Log is not None: MLTrainer.Log.Info(f'Data preparation finished')

        # Return a tuple containing the training & testing datasets
        return dataset[:index], dataset[index:]

    ## -----------
    ## Constructor

    def __init__(self, dataset, columns: dict, separator=',', split=0.8, **modules):
        """
        Initializes the MLTrainer to its' default state with the specified dataset, columns, separator & data split
        :param dataset: The dataset to prepare
        :param columns: The columns that specify which values to use
        :param separator: The sequence separating the columns
        :param split: The ratio that represents the training-evaluation data split
        """
        from import_modules import import_modules

        # Import the required modules
        import_modules(MLTrainer, 0,
                       random={'package_name': 'random2', 'as': 'random'},
                       pandas={'package_name': 'pandas', 'as': 'pandas'})

        # Retrieved the formatted training & evaluation datasets
        training_dataset, evaluation_dataset = MLTrainer.prepare(dataset, columns, separator, split)

        # Retrieve & initialize the evaluation categories
        self.evaluation_categories = [categories for text, categories in evaluation_dataset]
        self.evaluation_text = [text for text, categories in evaluation_dataset]

        # Initialize the training dataset
        self.training_dataset = training_dataset
