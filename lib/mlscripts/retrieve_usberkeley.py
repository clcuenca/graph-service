import datasets
import os
import json

## Note: Undefined behavior. This won't properly output json documents unless the name of the dict
## is changed between runs.
class BerkelyRetriever:

	dataset = {
		'spancat': {
			'labels': [],
			'data': []
		},
		'textcat': {
			'labels': [],
			'data': []
		}
	}

	spancat_labels = ["sentiment",
			   "respect",
			   "insult",
			   "humiliate",
			   "status",
			   "dehumanize",
			   "violence",
			   "genocide",
			   "attack_defend",
			   "hatespeech",
			   "hate_speech_score",]

	@staticmethod
	def retrieve(data: dict) -> dict:

		# Retrieve the text
		text = data['text'] if 'text' in data else ''
		_id	 = data['comment_id'] if 'comment_id' in data else ''

		# Remove the text
		del data['text']
		del data['comment_id']

		spancat_result = {}
		textcat_result = {}

		# Append the dataset; huggingface datasets class will use LazyRow & LazyColumn
		# to improve performance. However, this will not allow the dict to serialize to json
		# properly since it requires all key-value pairs to be accessed at least once (loads data upon reference)
		# An iteration is necessary to serialize the entire dataset.
		for key, value in data.items():

			if key in BerkelyRetriever.spancat_labels:

				spancat_result[key] = value

				if key not in BerkelyRetriever.dataset['spancat']['labels']:

					BerkelyRetriever.dataset['spancat']['labels'].append(key)

			else:

				textcat_result[key] = value

				if key not in BerkelyRetriever.dataset['textcat']['labels']:

					BerkelyRetriever.dataset['textcat']['labels'].append(key)

		# Append the results
		BerkelyRetriever.dataset['spancat']['data'].append((text, spancat_result))
		BerkelyRetriever.dataset['textcat']['data'].append((text, textcat_result))

		# Return the result
		return data

	def __call__(self, data: dict) -> dict:

		# Retrieve the text
		text = data['text'] if 'text' in data else ''
		_id	 = data['comment_id'] if 'comment_id' in data else ''

		# Remove the text
		del data['text']
		del data['comment_id']

		result = {}

		# Append the dataset; huggingface datasets class will use LazyRow & LazyColumn
		# to improve performance. However, this will not allow the dict to serialize to json
		# properly since it requires all key-value pairs to be accessed at least once (loads data upon reference)
		# An iteration is necessary to serialize the entire dataset.
		for key, value in data.items():

			result[key] = value

		# Set the row
		BerkelyRetriever.dataset[_id] = {'text': text, 'cats': result}

		# Return the result
		return data

def retrieve_usberkeley():

	if not os.path.isfile('data/usberkeley.json'):

		# Retrieve the dataset
		dataset = datasets.load_dataset('ucberkeley-dlab/measuring-hate-speech', 'binary')['train']

		# Remove the specified columns
		dataset = dataset.remove_columns([
			'annotator_id',
			'platform',
			'annotator_severity',
			'std_err',
			'annotator_infitms',
			'annotator_outfitms',
			'hypothesis',
			'annotator_gender',
			'annotator_trans',
			'annotator_educ',
			'annotator_income',
			'annotator_ideology',
			'annotator_gender_men',
			'annotator_gender_women',
			'annotator_gender_non_binary',
			'annotator_gender_prefer_not_to_say',
			'annotator_gender_self_describe',
			'annotator_transgender',
			'annotator_cisgender',
			'annotator_transgender_prefer_not_to_say',
			'annotator_education_some_high_school',
			'annotator_education_high_school_grad',
			'annotator_education_some_college',
			'annotator_education_college_grad_aa',
			'annotator_education_college_grad_ba',
			'annotator_education_professional_degree',
			'annotator_education_masters',
			'annotator_education_phd',
			'annotator_income_<10k',
			'annotator_income_10k-50k',
			'annotator_income_50k-100k',
			'annotator_income_100k-200k',
			'annotator_income_>200k',
			'annotator_ideology_extremeley_conservative',
			'annotator_ideology_conservative',
			'annotator_ideology_slightly_conservative',
			'annotator_ideology_neutral',
			'annotator_ideology_slightly_liberal',
			'annotator_ideology_liberal',
			'annotator_ideology_extremeley_liberal',
			'annotator_ideology_no_opinion',
			'annotator_race_asian',
			'annotator_race_black',
			'annotator_race_latinx',
			'annotator_race_middle_eastern',
			'annotator_race_native_american',
			'annotator_race_pacific_islander',
			'annotator_race_white',
			'annotator_race_other',
			'annotator_age',
			'annotator_religion_atheist',
			'annotator_religion_buddhist',
			'annotator_religion_christian',
			'annotator_religion_hindu',
			'annotator_religion_jewish',
			'annotator_religion_mormon',
			'annotator_religion_muslim',
			'annotator_religion_nothing',
			'annotator_religion_other',
			'annotator_sexuality_bisexual',
			'annotator_sexuality_gay',
			'annotator_sexuality_straight',
			'annotator_sexuality_other',
			'infitms',
			'outfitms'])

		dataset.map(BerkelyRetriever.retrieve)

		with open('data/usberkeley.json', 'w') as output:

			output.write(json.dumps(BerkelyRetriever.dataset, indent=4))

	else:

		with open('data/usberkeley.json', 'r') as input:

			BerkelyRetriever.dataset = json.loads(input.read())

	return BerkelyRetriever.dataset















<<<<<<< HEAD

=======
>>>>>>> 6c4e96d (Update training script)
