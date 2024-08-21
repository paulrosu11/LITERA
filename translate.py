from openai import OpenAI
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Initialize the OpenAI client with your API key
clientGPT = OpenAI(api_key="Insert your API key here")

# Function to read prompts from files
def read_prompt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

# Reading the prompts
filter_prompt = read_prompt('FinalFilterPrompt.txt')
revision_prompt = read_prompt('RevisionPrompt.txt')
fine_tuned_system_prompt = read_prompt('FineTunedSystemPrompt.txt')
non_literal_prompt = read_prompt('NonLiteralPrompt.txt')

def generate_translation(text):
    """
    This function generates an initial translation using a fine-tuned GPT model
    and subsequently refines it using a GPT-4 revision model.
    """
    # Initial translation using the fine-tuned model
    initial_response = clientGPT.chat.completions.create(
        model="Insert your fine-tuned model ID here",  # Replace with your fine-tuned model ID
        messages=[{
            "role": "system",
            "content": fine_tuned_system_prompt
        }, {
            "role": "user",
            "content": text
        }],
        temperature=0.7,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    translated_text = initial_response.choices[0].message.content

    # Revision of the initial translation
    revised_response = clientGPT.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "system",
            "content": revision_prompt
        }, {
            "role": "user",
            "content": f"Return a corrected translation or the same if it is accurate:\nLatin text: {text}\nTranslation:\n{translated_text}"
        }],
        temperature=0.7,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    return revised_response.choices[0].message.content

def generate_non_literal_translation(text):
    """
    This function generates a non-literal translation that emphasizes readability and naturalness in English,
    while maintaining the core meaning of the original Latin text.
    """
    response = clientGPT.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "system",
            "content": non_literal_prompt
        }, {
            "role": "user",
            "content": text
        }],
        temperature=0.7,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    non_literal_translation = response.choices[0].message.content

    return non_literal_translation

def perform_latin_translation_workflow(text):
    """
    This function orchestrates the translation workflow, generating multiple candidate translations,
    selecting the best one, and refining it to produce a final output.
    """
    translations = []
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(generate_translation, text) for _ in range(5)]
        for future in as_completed(futures):
            translations.append(future.result())

    # Prepare the comparison prompt
    comparison_prompt = f"Given these five translations, select the best one based on this Latin provided text: \n{text}\n1. {translations[0]}\n2. {translations[1]}\n3. {translations[2]}\n4. {translations[3]}\n5. {translations[4]}"

    # Make the comparison call to gpt-4o
    best_choice_response = clientGPT.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "system",
            "content": filter_prompt
        }, {
            "role": "user",
            "content": comparison_prompt
        }],
        temperature=0.7,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    # Revise the final output using the same revision model
    final_revised_response = clientGPT.chat.completions.create(
        model="gpt-4o",
        messages=[{
            "role": "system",
            "content": revision_prompt
        }, {
            "role": "user",
            "content": f"Return a corrected translation or the same if it is accurate: \nLatin text: {text}\nTranslation:\n{best_choice_response.choices[0].message.content}"
        }],
        temperature=0.7,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    return final_revised_response.choices[0].message.content
