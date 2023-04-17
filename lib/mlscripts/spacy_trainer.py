"""
SpaCy text classifier trainer class. Handles training a SpaCy text classifier.
@author Kirsten Tan
@author Carlos L. Cuenca
"""

## -------
## Imports

from mltrainer import MLTrainer

class SpacyTextCatTrainer (MLTrainer):
    """
    Spacy Text Categorizer trainer class. Trains a Spacy TextCategorizer model & provides methods to retrieve the model
    & config.
    :author: Kirsten Tan
    :author: Carlos L. Cuenca
    """

    ## -------------
    ## Static Fields

    Log = None

    ## --------------
    ## Static Methods

    @staticmethod
    def prepare_pipe(language, name: str, configuration: dict, labels: list):
        """
        Prepares & adds the Spacy Pipe with the specified name, configuration, & labels.
        :param language: The nlp instance to create the pipe with
        :param name: The name of the pipe
        :param configuration: The configuration that corresponds with the pipe
        :param labels: The labels to assign to the pipe
        :return: Newly created pipe
        """

        # Initialize the pipe
        pipe = None

        # If we have a valid NLP instance
        if language is not None:

            # Report to the user
            if SpacyTextCatTrainer.Log is not None: SpacyTextCatTrainer.Log.Info(f'Creating pipe: {name}')

            # Create the pipe
            pipe = language.add_pipe(name, config=configuration)

            # Report to the user
            if SpacyTextCatTrainer.Log is not None: SpacyTextCatTrainer.Log.Info(f'Adding labels: {labels}')

            # Add the labels
            for label in labels:

                # Add the label
                pipe.add_label(label)

            # Report to the user
            if SpacyTextCatTrainer.Log is not None: SpacyTextCatTrainer.Log.Info(f'Adding pipe to language')

        # Report to the user
        if SpacyTextCatTrainer.Log is not None: SpacyTextCatTrainer.Log.Info(f'Pipe prepared.')

        # Return the result
        return pipe

    @staticmethod
    def evaluate(tokenizer, trained, texts: list, categories: list, omit: list) -> dict:

        # Initialize a tuple containing enumerated, tokenized text values
        documents = enumerate(trained.pipe((tokenizer(text) for text in texts)))

        # Initialize the metrics
        true_positive   = 0.0
        true_negative   = 0.0
        false_positive  = 1e-8
        false_negative  = 1e-8

        # Iterate through each of the index-document pairs
        for index, document in documents:

            # Retrieve the gold
            category = categories[index]['cats']

            # Iterate through the label-score pairs
            for label, score in document.cats.items():

                # If the label is not contained in gold or if it's NEGATIVE, continue
                if label not in category or label in omit:
                    continue

                # Increment the true positive score
                if score >= 0.5 and category[label] >= 0.5:
                    true_positive += 1.0

                # Increment the false positive score
                elif score >= 0.5 > category[label]:
                    false_positive += 1.0

                # Increment the true negative score
                elif score < 0.5 and category[label] < 0.5:
                    true_negative += 1

                # Increment the false negative score
                elif score < 0.5 <= category[label]:
                    false_negative += 1

        # Calculate the precision & recall
        precision   = true_positive / (true_positive + false_positive)
        recall      = true_positive / (true_positive + false_negative)

        # Initialize the f score, precision, & recall
        f_score = 0.0 if (precision + recall == 0) else 2 * (precision * recall) / (precision + recall)

        # Return the result
        return {
            'true_positive' : true_positive,
            'true_negative' : true_negative,
            'false_positive': false_positive,
            'false_negative': false_negative,
            'f_score'       : f_score,
            'precision'     : precision,
            'recall'        : recall
        }

    ## -----------
    ## Constructor

    def __init__(self, model, pipe_name, labels, dataset, columns: dict, separator=',',
                 evaluation_omit=[], split=0.8, epochs=10):
        """
        Initializes & trains the Spacy Textcat pipe
        :param model: The name of the spacy language model
        :param pipe_name: The name of the pipe
        :param labels: The training labels
        :param dataset: The dataset to train/evaluate
        :param pipe_configuration: The pipe configuration
        :param columns: The columns to extract into the training data
        :param separator: The sequence separating the data
        :param split: The ratio representing the data split
        :param epochs: The amount of training cycles
        """
        # Retrieved the formatted training & evaluation datasets
        super().__init__(dataset, columns, separator, split)

        from import_modules import import_modules

        # Import the required modules
        import_modules(SpacyTextCatTrainer, 0,
                       spacy={'package_name': 'spacy',
                              'blank': {},
                              'load': {},
                              'Language': {},
                              'tokenizer': {},
                              'training': {
                                  'Example': {}
                              },
                              'util': {
                                  'minibatch': {},
                                  'compounding': {}
                              }},
                       thinc={'package_name': 'thinc',
                              'api': {
                                  'Adam': {}
                              }})

        # Report to the user
        if SpacyTextCatTrainer.Log is not None: SpacyTextCatTrainer.Log.Info(f'Loading spacy model: {model}')

        # Initialize the names
        blank       = SpacyTextCatTrainer.blank
        load        = SpacyTextCatTrainer.load
        compounding = SpacyTextCatTrainer.compounding
        minibatch   = SpacyTextCatTrainer.minibatch
        Adam        = SpacyTextCatTrainer.Adam
        Example     = SpacyTextCatTrainer.Example

        # Initialize the Language
        nlp = None

        try:

            # Attempt to Load the spaCy Model
            nlp = blank(load(model).lang)

        # Except
        except OSError as error:

            # Report to the user
            SpacyTextCatTrainer.Log.Warn(f'Model \'{model}\' not found. Attempting to retrieve.')

            from sys import executable
            from subprocess import run

            # Attempt to install the module
            run([executable, '-m', 'spacy', 'download', model])

            # Attempt to load the spaCy model
            nlp = blank(load(model).lang)

        # Report to the user
        if SpacyTextCatTrainer.Log is not None: SpacyTextCatTrainer.Log.Info(f'Preparing pipe: {pipe_name}')

        # Create the pipe using the default single-label config
        text_cat = SpacyTextCatTrainer.prepare_pipe(nlp, pipe_name, {}, labels)

        # Retrieve all the pipes that are not the text classifier
        pipe_names = [name for name in nlp.pipe_names if name != pipe_name]

        # Report to the user
        if SpacyTextCatTrainer.Log is not None: SpacyTextCatTrainer.Log.Info(f'Pipes: {nlp.pipe_names}')

        # Disable all the pipes except the classifier
        with nlp.disable_pipes(*pipe_names):

            # Create the optimizer with the default sgd
            optimizer = nlp.initialize(sgd=Adam())

            # Report to the user
            if SpacyTextCatTrainer.Log is not None: SpacyTextCatTrainer.Log.Info(f'Training')

            # Performing training
            for epoch in range(epochs):

                # Initialize the losses
                losses = {}

                # Retrieve the batches
                batches = minibatch(self.training_dataset, size=compounding(4., 32., 1.001))

                # Iterate through each batch
                for batch in batches:

                    # Iterate through the text-annotations pairs
                    for text, annotations in batch:

                        # Initialize the example
                        example = Example.from_dict(nlp.make_doc(text), annotations)

                        # Update the model with the example
                        nlp.update([example], drop=0.2, sgd=optimizer, losses=losses)

                # With the optimizer averages
                with text_cat.model.use_params(optimizer.averages):

                    # Calculate & retrieve the metrics
                    self._metrics = SpacyTextCatTrainer.evaluate(nlp.tokenizer, text_cat, self.evaluation_text,
                                                                self.evaluation_categories, evaluation_omit)

        # Initialize the language, configuration & bytes
        self._language          = nlp
        self._configuration     = nlp.config
        self._bytes             = nlp.to_bytes()

    def metrics(self):

        return self._metrics

    def configuration(self):

        return self._configuration

    def bytes(self):

        return self._bytes
