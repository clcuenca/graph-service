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
    def prepare(dataset: dict, split: float) -> tuple:
        """
        Prepares the training & evaluation dataset from the specified data, & split ratio.
        :param dataset: The data to prepare
        :param split: The ratio to split the data
        :return: The training & evaluation datasets as a list of tuples
        """

        # Initialize the functions
        shuffle  = MLTrainer.random.shuffle

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

    def __init__(self, dataset, split=0.8):
        """
        Initializes the MLTrainer to its' default state with the specified dataset, columns, separator & data split
        :param dataset: The dataset to prepare
        :param split: The ratio that represents the training-evaluation data split
        """

        from import_modules import import_modules

        # Import the required modules
        import_modules(MLTrainer, 0,
                       random={'package_name': 'random2', 'as': 'random'},
                       pandas={'package_name': 'pandas', 'as': 'pandas'})

