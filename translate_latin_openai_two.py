from openai import OpenAI
import os

from concurrent.futures import ThreadPoolExecutor, as_completed

clientGPT = OpenAI(api_key= "Insert your api key here")


# Function to read prompts from files
def read_prompt(file_path):
  with open(file_path, 'r', encoding='utf-8') as file:
    return file.read()


# Reading the prompts¸
filterPrompt = read_prompt('Translator/FinalFilterPrompt.txt')
RevisionPrompt = read_prompt('Translator/GPT4Prompt.txt')
FineTunedPrompt = read_prompt('Translator/FineTunedSystemPrompt.txt')
nonLiteralPrompt = read_prompt('Translator/NonLiteralPrompt.txt')


def translate_and_revise(text):
  # Initial translation
  initialResponse = clientGPT.chat.completions.create(
       model = "ft:gpt-4o-2024-08-06:paul::9yTsIwYG",
      #model="ft:gpt-3.5-turbo-0125:paul::9g1kEkb7",
      messages=[{
          "role": "system",
          "content": FineTunedPrompt
      }, {
          "role": "user",
          "content": text
      }],
      temperature=0.68,
      max_tokens=2000,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0)

  translated_text = initialResponse.choices[0].message.content

  # Revision
  revisedResponse = clientGPT.chat.completions.create(
      model="gpt-4o",
      messages=[{
          "role": "system",
          "content": RevisionPrompt
      }, {
          "role":
          "user",
          "content":
          f"Return a corrected translation or the same if it is accurate:\nLatin text: {text}\nTranslation:\n{translated_text}"
      }])

  return revisedResponse.choices[0].message.content


def non_literal_translation(text):
  # Initial translation
  response = clientGPT.chat.completions.create(model="gpt-4o",
                                               messages=[{
                                                   "role":
                                                   "system",
                                                   "content":
                                                   nonLiteralPrompt
                                               }, {
                                                   "role": "user",
                                                   "content": text
                                               }],
                                               temperature=0.68,
                                               max_tokens=2000,
                                               top_p=1,
                                               frequency_penalty=0,
                                               presence_penalty=0)

  non_literal_translation = response.choices[0].message.content

  return non_literal_translation


def translate_latin_openai_two(text):
  translations = []
  with ThreadPoolExecutor() as executor:
    futures = [executor.submit(translate_and_revise, text) for _ in range(5)]
    for future in as_completed(futures):
      translations.append(future.result())

  # Prepare the comparison prompt
  comparisonPrompt = f"Given these five translations, select the best one based on this Latin provided text: \n {text} \n1. {translations[0]}\n2. {translations[1]}\n3. {translations[2]}\n4. {translations[3]}\n5. {translations[4]}"

  # Make the comparison call to gpt-4o
  bestChoiceResponse = clientGPT.chat.completions.create(
      model="gpt-4o",
      messages=[{
          "role": "system",
          "content": filterPrompt
      }, {
          "role": "user",
          "content": comparisonPrompt
      }])

  # Revise the final output using the same revision model
  finalRevisedResponse = clientGPT.chat.completions.create(
      model="gpt-4o",
      messages=[{
          "role": "system",
          "content": RevisionPrompt
      }, {
          "role":
          "user",
          "content":
          f"Return a corrected translation or the same if it is accurate: \n Latin text: {text} \n translation: \n {bestChoiceResponse.choices[0].message.content}"
      }])

  return finalRevisedResponse.choices[0].message.content
