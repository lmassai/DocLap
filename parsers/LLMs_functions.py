import base64
import os
import re
from urllib.parse import urlparse

import fitz
import requests
from flask import request, jsonify
from openai import OpenAI


def rispondi_domanda():
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response, 200

    try:
        data = request.get_json()
        print('Received payload:', data)

        domanda = data.get('question', '')
        log_data = data.get('logData', '')

        auto_context = data.get('useAutomaticContext', False)

        if auto_context:
            contexts = classify_question(domanda)
        else:
            contexts = data.get('contexts', [])

        pdf_url = data.get('pdfUrl', '')
        pdf_local_path = get_local_pdf_path(pdf_url)

        if not os.path.exists(pdf_local_path):
            raise FileNotFoundError(f"File not found: {pdf_local_path}")

        extract_images_from_pdf(pdf_local_path)

        log_data_vector = [element.replace('\t', '').replace('\r\n', ' ') for element in log_data.split('end_section') if element != '']
        print('User: ' + domanda)
        print('Selected contexts: ', contexts)

        context_map = {
            'General info': [0],
            'Header data': [1],
            'Abstract': [2],
            'Figures': [3],
            'Tables': [4],
            'Formulas': [7],
            'Sections': [8],
            'Links': [9],
            'Notes': [10],
            'Acknowledgements': [11],
            'References': [12],
            'Phrase': [13]
        }

        pattern = r"\w+\scoordinates: \(page: \d+, x: \d+\.\d+, y: \d+\.\d+, w: \d+\.\d+, h: \d+\.\d+\)"
        max_total_chars = 2048
        max_chars_per_section = 1200

        selected_log_data = []
        for context in contexts:
            if context in context_map:
                indices = context_map[context]
                for index in indices:
                    if index < len(log_data_vector):
                        cleaned_section = re.sub(pattern, '', log_data_vector[index])
                        if len(cleaned_section) > max_chars_per_section:
                            selected_log_data.append(cleaned_section[:max_chars_per_section])
                        else:
                            selected_log_data.append(cleaned_section)

        log_data_combined = " ".join(selected_log_data).replace('\r\n', ' ').replace('  ', '')
        if len(log_data_combined) > max_total_chars:
            log_data_combined = log_data_combined[:max_total_chars]


        image_dir = os.path.join(os.getcwd(), "uploads", "to_process", "extracted_images_for_QA")
        relevant_images = extract_relevant_images(log_data_combined, image_dir)

        if not relevant_images:
            print("[WARN] No relevant image found for LLaVA.")

        encoded_images = []

        print("Immagini inviate a LLaVA:")
        for img_path in relevant_images:
            print(" -", os.path.basename(img_path))
            with open(img_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
                encoded_images.append(image_data)

        prompt = (
            "You are given a question about a research article. "
            "Consider the following context extracted from it:\n\n"
            f"{log_data_combined}\n\n"
            "Now answer this question:\n"
            f"{domanda}. (Please answer in one sentence only)"
        )

        payload = {
            "model": "llava",
            "prompt": prompt,
            "images": encoded_images,
            "temperature": 0,
            "stream": False
        }

        response = requests.post("http://localhost:11434/api/generate", json=payload)

        if response.status_code == 200:
            risposta = "<b>Answer: </b>" + response.json()["response"].strip()

            pagine = set()
            for img_path in relevant_images:
                match = re.search(r'page_(\d+)\.png', os.path.basename(img_path), re.IGNORECASE)
                if match:
                    pagine.add(int(match.group(1)))

            if pagine:
                pagine_str = ", ".join(str(p) for p in sorted(pagine))
                risposta += "<br><b>Information found at page(s)</b>: " + pagine_str + "<br><br><b>Context: </b>" + str(contexts)

            print('LLaVA: ' + risposta)
            return jsonify({'risposta': risposta})
        else:
            print("Error in request:", response.text)
            return jsonify({'answer': 'Error calling LLaVA'})

    except Exception as e:
        print(f"Errore: {e}")
        return jsonify({'risposta': 'I did not understand, sorry.'})

def extract_relevant_images(log_data_combined, images_folder):

    pagine = set(re.findall(r'page:\s*(\d+)', log_data_combined))
    immagini = []

    for num in pagine:
        filename = f"page_{num}.png"
        filepath = os.path.join(images_folder, filename)
        if os.path.exists(filepath):
            immagini.append(filepath)
        else:
            print(f"[WARN] Image not found: {filepath}")

    return immagini

def get_local_pdf_path(pdf_url):
    parsed = urlparse(pdf_url)
    relative_path = parsed.path.lstrip('/')
    local_path = os.path.join(os.getcwd(), relative_path)
    return local_path

def extract_images_from_pdf(pdf_path):
    output_dir = os.path.join("uploads", "to_process", "extracted_images_for_QA")
    os.makedirs(output_dir, exist_ok=True)

    doc = fitz.open(pdf_path)

    for page_number in range(len(doc)):
        page = doc.load_page(page_number)
        pix = page.get_pixmap(dpi=500)
        image_path = os.path.join(output_dir, f"page_{page_number + 1}.png")
        pix.save(image_path)

    doc.close()
    print(f"Immagini estratte in: {output_dir}")

def classify_question(question):

    client = OpenAI(
        base_url='http://localhost:11434/v1'
    )

    messages = [
        {'role': 'user',
         'content': 'You are given a phrase from a research article. Classify it using one of these structure labels (comma-separated):\n'
                    'General info, Header data, Abstract, Figures, Tables, Formulas, Sections, Links, Notes, Acknowledgements, References. \n'
                    'The label Header data includes the article title and author names.\n'
                    'Note: The correct class label will most likely appear in the phrase.\n'
                    'Output format (no extra text):\n'
                    '[your selected label]'
                    '\nNow classify this phrase: ' + question}
    ]

    response = client.chat.completions.create(
        model="gpt-oss:120b-cloud",
        messages=messages
    )
    print('MESSAGES: ' + str(messages))
    print('QUESTION: ' + question)
    print('CONTEXT: ' + str(response.choices[0].message.content))

    layout_classes = response.choices[0].message.content.split(', ')

    print('\nLLM classification: ' + str(layout_classes) + '\n')

    return layout_classes


def answer_question_given_that(domanda, log_data_combined):
    client = OpenAI(
        base_url='http://localhost:11434/v1'
    )

    messages = [
        {"role": "system",
         "content": "The questions will be about a scholarly article from which some data has been extracted in structured form and given as context."},
        {"role": "user", "content": "Given that: " + log_data_combined + ", " + domanda + ". Give only the essential answer. No explanation, no deduction info, no extra text, no comments. Just the briefest answer that answers the question"}
    ]

    print('Messages to LLM:')
    for message in messages:
        print(message)

    response = client.chat.completions.create(
        model="gpt-oss:120b-cloud",
        messages=messages
    )

    risposta = response.choices[0].message.content

    print(risposta)
    return jsonify({'risposta': risposta})
