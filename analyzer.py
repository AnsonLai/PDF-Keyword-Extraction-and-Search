import fitz
# SECRETS lists IBM Watson Natural Language api and url, and a link to a sample text file
from SECRETS import apikey, url, service_url

import json
from ibm_watson import NaturalLanguageUnderstandingV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson.natural_language_understanding_v1 import Features, KeywordsOptions

# PREPARE PLAIN TEXT FILES
doc = fitz.open('sample.pdf')
plain_text = ''

for page in doc:
  page_plain_text = page.getTextPage().extractText().replace("-\n", "").replace("\n", "")
  plain_text += page_plain_text

text_file = open("sample.txt", "w", encoding="utf-8")
n = text_file.write(plain_text)
text_file.close()

# SPLIT INTO 50,000 CHUNKS (required for IBM Watson)
i = 0
while plain_text != '':
  split_plain_text = ''
  if len(plain_text) > 50000:
    split_plain_text = plain_text[0:50000]
    plain_text = plain_text[50000:]
  else:
    split_plain_text = plain_text[0:]
    plain_text = ''
  text_file = open("sample_split" + str(i) + ".txt", "w", encoding="utf-8")
  n = text_file.write(split_plain_text)
  text_file.close()
  i += 1

# KEYWORD EXTRACTION
authenticator = IAMAuthenticator(apikey)
natural_language_understanding = NaturalLanguageUnderstandingV1(
    version='2020-08-01',
    authenticator=authenticator
)
natural_language_understanding.set_service_url(service_url)

for j in range(i):
  text = open("sample_split" + str(j) + ".txt", "r", encoding="utf-8").read()
  response = natural_language_understanding.analyze(text = text, features=Features(keywords=KeywordsOptions(limit=4500))).get_result()

  ibm_output = json.dumps(response, indent=2)
  json_file = open("ibm_output_" + str(j) + ".json", "w", encoding="utf-8")
  n = json_file.write(ibm_output)
  json_file.close()

# PARSE JSON FILES FOR KEYWORDS
keywords = []

for k in range(i):
  json_file = open("ibm_output_" + str(k) + ".json", "r", encoding="utf-8").read()
  json_output = json.loads(json_file)
  for keyword in json_output['keywords']:
    text = keyword['text'].replace('\u2019', "'")
    relevance = keyword['relevance']
    count = keyword['count']
    if count > 1:
      keywords.append(text)
    elif relevance > 0.40:
      keywords.append(text)

keywords = sorted(list(set(keywords)), key=str.lower)

# SEARCH
keyword_locations ={}
doc = fitz.open('sample.pdf')

for page in doc:
  page_rect = page.MediaBox
  # TODO: May manually offset to match printed page numbers
  page_num = page.number

  for keyword in keywords:
    locations = []
    rect_list = page.searchFor(keyword)
    for rect in rect_list:
      location = {}
      x_coord = ((rect.x1 - rect.x0)/2)/page_rect.x1
      y_coord = ((rect.y1 - rect.y0)/2)/page_rect.y1
      location['page'] = page_num
      location['x-coord'] = x_coord
      location['y-coord'] = y_coord
      locations.append(location)
    if len(rect_list) > 0:
      if keyword in keyword_locations:
        for loc in locations:
          keyword_locations[keyword].append(loc)
      else:
        keyword_locations[keyword] = locations

sample_output = json.dumps(keyword_locations, indent=2)
json_file = open("sample_output.json", "w", encoding="utf-8")
n = json_file.write(sample_output)







# UNUSED EXTRACTION METHODS

# from summa.summarizer import summarize
# from summa import keywords
# print(keywords.keywords(plain_text, split=True))

# from gensim.summarization import keywords
# from gensim.summarization.summarizer import summarize
# from rake_nltk import Rake
# # GENSIM
# print("********** GENSIM SUMMARIZE *************")
# summary = summarize(page_plain_text, ratio = 0.70)
# print(summary)
# print("********** GENSIM KEYWORDS *************")
# print(keywords(plain_text, split=True))

# # RAKE
# print("********** RAKE FROM PLAIN TEXT *************")
# rake = Rake()
# rake.extract_keywords_from_text(plain_text)
# print(rake.get_ranked_phrases())
# print("********** RAKE FROM GENSIM SUMMARIZE *************")
# rake = Rake()
# rake.extract_keywords_from_text(summary)
# print(rake.get_ranked_phrases())