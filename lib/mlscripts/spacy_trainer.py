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
    def evaluate(tokenizer, trained, texts: list, feature_set: list) -> dict:

        # Initialize a tuple containing enumerated, tokenized text values
        documents = enumerate(trained.pipe((tokenizer(text) for text in texts)))

        # Initialize the metrics
        true_positive   = 0.0
        true_negative   = 0.0
        false_positive  = 1e-8
        false_negative  = 1e-8

        # Iterate through each of the index-document pairs
        for index, document in documents:

            # Initialize a handle to the features
<<<<<<< HEAD
            labels = feature_set[index]
=======
            labels = feature_set[index]['cats']
>>>>>>> 6c4e96d (Update training script)

            # Iterate through the label-score pairs
            for feature, score in document.cats.items():

                # Increment the true positive score
                if score >= 0.5 and labels[feature] >= 0.5:
                    true_positive += 1.0

                # Increment the false positive score
                elif score >= 0.5 > labels[feature]:
                    false_positive += 1.0

                # Increment the true negative score
                elif score < 0.5 and labels[feature] < 0.5:
                    true_negative += 1

                # Increment the false negative score
                elif score < 0.5 <= labels[feature]:
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

    @staticmethod
    def train_pipe(language, pipe_name, pipe, epochs, training_dataset, evaluation_text, evaluation_features):
<<<<<<< HEAD
=======

        from import_modules import import_modules

        # Import the required modules
        import_modules(SpacyTextCatTrainer, 0,
                       spacy={'package_name': 'spacy',
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
                              }},
                       time={'package_name': 'time',
                             'time': {}})

        # Initialize the names
        compounding = SpacyTextCatTrainer.compounding
        minibatch   = SpacyTextCatTrainer.minibatch
        time        = SpacyTextCatTrainer.time
        Adam        = SpacyTextCatTrainer.Adam
        Example     = SpacyTextCatTrainer.Example

        # Retrieve all the pipes that are not the text classifier
        pipe_names = [name for name in language.pipe_names if name != pipe_name]

        # Report to the user
        if SpacyTextCatTrainer.Log is not None: SpacyTextCatTrainer.Log.Info(f'Pipes: {language.pipe_names}')

        # Initialize the choices
        choices = []

        # Disable all the pipes except the classifier
        with language.disable_pipes(*pipe_names):

            # Create the optimizer with the default sgd
            optimizer = language.initialize(sgd=Adam())

            # Report to the user
            if SpacyTextCatTrainer.Log is not None: SpacyTextCatTrainer.Log.Info(f'Training {pipe_name}; epochs {epochs}')

            # Intialize the start time
            start_time = time()

            # Performing training
            for epoch in range(epochs):

                # Initialize the losses
                losses = {}

                # Retrieve the batches
                batches = minibatch(training_dataset, size=compounding(4., 32., 1.001))

                # Initialize the batch count
                batch_count = 0

                # Iterate through each batch
                for batch in batches:

                    # Increment the batch count
                    batch_count += 1

                    # Report
                    if SpacyTextCatTrainer.Log is not None:

                        SpacyTextCatTrainer.Log.Info(f'Training: Epoch {epoch} Batch {batch_count}')

                    # Iterate through the text-annotations pairs
                    for text, features in batch:

                        # Initialize the example
                        example = Example.from_dict(language.make_doc(text), {'cats': features})

                        # Update the model with the example
                        language.update([example], drop=0.2, sgd=optimizer, losses=losses)

                # Initialize the metrics
                training_time = time() - start_time

                # With the optimizer averages
                with pipe.model.use_params(optimizer.averages):

                    # Calculate & retrieve the metrics
                    metrics = SpacyTextCatTrainer.evaluate(language.tokenizer, pipe, evaluation_text,
                                                           evaluation_features, [])

                # Insert the training time (seconds)
                metrics['training_time'] = training_time

                # Report
                if SpacyTextCatTrainer.Log is not None: SpacyTextCatTrainer.Log.Info(f'Trained {pipe_name} - {str(metrics)}')

                # Append to the choices
                choices.append((language.to_bytes(), language.config, metrics))

        # Return the result
        return metrics

    ## -----------
    ## Constructor

    def __init__(self, spacy_model, dataset, split=0.8, epochs=10):
        """
        Initializes & trains the Spacy Textcat pipe
        :param spacy_model: The name of the spacy language model
        :param textcat_multilabel: The name of the pipe
        :param dataset: The dataset to train/evaluate
        :param split: The ratio representing the data split
        :param epochs: The amount of training cycles
        """
        # Retrieved the formatted training & evaluation datasets
        super().__init__(dataset, split)
>>>>>>> 6c4e96d (Update training script)

        from import_modules import import_modules

        # Import the required modules
        import_modules(SpacyTextCatTrainer, 0,
                       spacy={'package_name': 'spacy',
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
                              }},
                       time={'package_name': 'time',
                             'time': {}})

        # Initialize the names
        compounding = SpacyTextCatTrainer.compounding
        minibatch   = SpacyTextCatTrainer.minibatch
        time        = SpacyTextCatTrainer.time
        Adam        = SpacyTextCatTrainer.Adam
        Example     = SpacyTextCatTrainer.Example

        # Retrieve all the pipes that are not the text classifier
        pipe_names = [name for name in language.pipe_names if name != pipe_name]

        # Report to the user
        if SpacyTextCatTrainer.Log is not None: SpacyTextCatTrainer.Log.Info(f'Pipes: {language.pipe_names}')

        # Initialize the choices
        choices = []

        # Disable all the pipes except the classifier
        with language.disable_pipes(*pipe_names):

            # Create the optimizer with the default sgd
            optimizer = language.initialize(sgd=Adam())

            # Report to the user
            if SpacyTextCatTrainer.Log is not None: SpacyTextCatTrainer.Log.Info(f'Training {pipe_name}; epochs {epochs}')

            # Intialize the start time
            start_time = time()

            # Performing training
            for epoch in range(epochs):

                # Initialize the losses
                losses = {}

                # Retrieve the batches
                batches = minibatch(training_dataset, size=compounding(4., 64., 1.001))

                # Initialize the batch count
                batch_count = 0

                # Iterate through each batch
                for batch in batches:

                    # Increment the batch count
                    batch_count += 1

                    # Report
                    if SpacyTextCatTrainer.Log is not None:

                        SpacyTextCatTrainer.Log.Info(f'Training: Epoch {epoch} Batch {batch_count}')

                    # Iterate through the text-annotations pairs
                    for text, features in batch:

                        # Initialize the example
                        example = Example.from_dict(language.make_doc(text), {'cats': features})

                        # Update the model with the example
                        language.update([example], drop=0.2, sgd=optimizer, losses=losses)

                # Initialize the metrics
                training_time = time() - start_time

                # With the optimizer averages
                with pipe.model.use_params(optimizer.averages):

                    # Calculate & retrieve the metrics
                    metrics = SpacyTextCatTrainer.evaluate(language.tokenizer, pipe,
                                                           evaluation_text, evaluation_features)

                # Insert the training time (seconds)
                metrics['training_time'] = training_time

                # Report
                if SpacyTextCatTrainer.Log is not None: SpacyTextCatTrainer.Log.Info(f'Trained {pipe_name} - {str(metrics)}')

                # Append to the choices
                choices.append((language.to_bytes(), language.config, metrics))

        # Return the result
        return metrics

    ## -----------
    ## Constructor

    def __init__(self, spacy_model, dataset, split=0.8, epochs=8):
        """
        Initializes & trains the Spacy Textcat pipe
        :param spacy_model: The name of the spacy language model
        :param textcat_multilabel: The name of the pipe
        :param dataset: The dataset to train/evaluate
        :param split: The ratio representing the data split
        :param epochs: The amount of training cycles
        """
        # Retrieved the formatted training & evaluation datasets
        super().__init__(dataset, split)

        from import_modules import import_modules

        # Import the required modules
        import_modules(SpacyTextCatTrainer, 0,
                       spacy={'package_name': 'spacy',
                              'prefer_gpu': {},
                              'require_gpu': {},
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
                              }},
                       time={'package_name': 'time',
                             'time': {}})

        spancat_dataset = dataset['spancat'] if 'spancat' in dataset else {}
        textcat_dataset = dataset['textcat'] if 'textcat' in dataset else {}

        spancat_labels = spancat_dataset['labels']
        textcat_labels = textcat_dataset['labels']

        spancat_data = spancat_dataset['data']
        textcat_data = textcat_dataset['data']
<<<<<<< HEAD

        SpacyTextCatTrainer.prefer_gpu()
=======
>>>>>>> 6c4e96d (Update training script)

        # Report to the user
        if SpacyTextCatTrainer.Log is not None: SpacyTextCatTrainer.Log.Info(f'Loading spacy model: {spacy_model}')

        # Initialize the names
        blank = SpacyTextCatTrainer.blank
        load  = SpacyTextCatTrainer.load

        try:

            # Attempt to Load the spaCy Model
            nlp = blank(load(spacy_model).lang)

        # Except
        except OSError as error:

            # Report to the user
            SpacyTextCatTrainer.Log.Warn(f'Model \'{spacy_model}\' not found. Attempting to retrieve.')

            from sys import executable
            from subprocess import run

            # Attempt to install the module
            run([executable, '-m', 'spacy', 'download', spacy_model])

            # Attempt to load the spaCy model
            nlp = blank(load(spacy_model).lang)

        # Report to the user
        if SpacyTextCatTrainer.Log is not None: SpacyTextCatTrainer.Log.Info(f'Preparing pipes')

        # Create the pipe using the default single-label config
        spancat = SpacyTextCatTrainer.prepare_pipe(nlp, 'spancat', {}, spancat_labels)
        textcat = SpacyTextCatTrainer.prepare_pipe(nlp, 'textcat_multilabel', {}, textcat_labels)

        # Prep the data
        spancat_training, spancat_evaluation = MLTrainer.prepare(spancat_data, split)
        textcat_training, textcat_evaluation = MLTrainer.prepare(textcat_data, split)

        # Split the evalutation & featuresets for spancat
        spancat_evaluation_text     = [text for text, features in spancat_evaluation]
        spancat_evaluation_features = [features for text, features in spancat_evaluation]

        # Split the evalutation & featuresets for textcat
        textcat_evaluation_text     = [text for text, features in textcat_evaluation]
        textcat_evaluation_features = [features for text, features in textcat_evaluation]

        # Train the spancat pipe
<<<<<<< HEAD
        self.spancat_metrics = SpacyTextCatTrainer.train_pipe(nlp, 'spancat', spancat, epochs, spancat_training,
                                       spancat_evaluation_text, spancat_evaluation_features)

        # Train the textcat pipe
        self.textcat_metrics = SpacyTextCatTrainer.train_pipe(nlp, 'textcat_multilabel', textcat, epochs, textcat_training,
=======
        SpacyTextCatTrainer.train_pipe(nlp, 'spancat', spancat, epochs, spancat_training,
                                       spancat_evaluation_text, spancat_evaluation_features)

        # Train the textcat pipe
        SpacyTextCatTrainer.train_pipe(nlp, 'textcat_multilabel', textcat, epochs, textcat_training,
>>>>>>> 6c4e96d (Update training script)
                                       textcat_evaluation_text, textcat_evaluation_features)

        # Initialize the language, configuration & bytes
        self._language          = nlp
        self._configuration     = nlp.config
        self._bytes             = nlp.to_bytes()

    def configuration(self):

        return self._configuration

    def bytes(self):

        return self._bytes
