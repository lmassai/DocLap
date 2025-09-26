import os
import nltk
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import parsers.LLMs_functions

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
conversation_history = []

UPLOAD_FOLDER = 'uploads'
TO_PROCESS_FOLDER = os.path.join(UPLOAD_FOLDER, 'to_process')

if not os.path.exists(TO_PROCESS_FOLDER):
    os.makedirs(TO_PROCESS_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

nltk.download('punkt')
nltk.download('stopwords')

@app.route('/delete_groundtruth_errors_bb', methods=['POST'])
def delete_bb():
    data = request.json['line'].strip()
    file_path = 'uploads/to_process/groundtruth_errors_bb.txt'

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        deleted = False
        with open(file_path, 'w', encoding='utf-8') as f:
            for line in lines:
                if not deleted and line.strip() == data:
                    deleted = True
                    continue
                f.write(line)

        return jsonify({ 'message': 'Success deleting row' })

    except Exception as e:
        return jsonify({ 'error': str(e) }), 500

@app.route('/save_groundtruth_errors_bb', methods=['POST', 'OPTIONS'])
def save_groundtruth_errors_bb():
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response, 200

    try:
        data = request.get_json()
        line = data.get('line', '') + '\n'

        file_path = os.path.join(TO_PROCESS_FOLDER, 'groundtruth_errors_bb.txt')

        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(line)

        response = jsonify({'message': 'Coordinates saved'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        print(f"Errore nel salvataggio: {e}")
        response = jsonify({'error': 'Error saving coordinates'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500

@app.route('/uploads/to_process/<path:filename>')
def uploaded_to_process_file(filename):
    return send_from_directory(TO_PROCESS_FOLDER, filename)


@app.route('/upload_pair', methods=['POST'])
def upload_pair():
    if 'pdf_file' not in request.files or 'txt_file' not in request.files:
        return jsonify({'error': 'Missing files'}), 400

    pdf_file = request.files['pdf_file']
    txt_file = request.files['txt_file']

    if pdf_file.filename == '' or txt_file.filename == '':
        return jsonify({'error': 'No selected files'}), 400

    try:
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file.filename)
        txt_path = os.path.join(app.config['UPLOAD_FOLDER'], txt_file.filename)

        pdf_file.save(pdf_path)
        txt_file.save(txt_path)

        return jsonify({
            'pdf_url': f'/uploads/{pdf_file.filename}',
            'txt_url': f'/uploads/{txt_file.filename}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate_bounding_boxes', methods=['POST'])
def generate_bounding_boxes():
    try:
        data = request.get_json()
        pdf_filename = data['filename']
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)

        command = f'python parsers/grobid_pdf_with_bb_generator.py "{pdf_path}"'
        os.system(command)

        return jsonify({'message': 'Bounding boxes generated successfully', 'pdf': pdf_filename})
    except Exception as e:
        print(f"Errore: {e}")
        return jsonify({'error': 'Failed to generate bounding boxes'}), 500

@app.route('/find_violations', methods=['POST'])
def find_violations():
    try:
        data = request.get_json()
        pdf_filename = data['filename']
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)

        command = f'python parsers/violations_finder.py "{pdf_path}"'
        os.system(command)

        return jsonify({'message': 'Violations analyzed successfully', 'pdf': pdf_filename})
    except Exception as e:
        print(f"Errore: {e}")
        return jsonify({'error': 'Failed to analyze violations'}), 500

@app.route('/generate_key-value_pairs_from_tex', methods=['POST'])
def generate_pdf_from_tex():
    try:
        data = request.get_json()
        tex_filename = data['filename']
        tex_path = os.path.join(app.config['UPLOAD_FOLDER'], tex_filename)
        print('TEX PATH: ' + tex_path)
        print('TEX FILENAME: ' + tex_filename)

        command = f'python parsers/latex_key_value_pairs_generator.py "{tex_path}"'
        os.system(command)

        return jsonify({'message': 'Key-value pairs from LaTeX generated successfully', 'tex': tex_filename})
    except Exception as e:
        print(f"Errore: {e}")
        return jsonify({'error': 'Failed to extract key-value pairs from LaTeX'}), 500

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        return jsonify({'url': f'/uploads/{file.filename}'})

@app.route('/upload_tex', methods=['POST'])
def upload_tex():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        return jsonify({'url': f'/uploads/{file.filename}'})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/answer_question', methods=['POST', 'OPTIONS'])
def answer_question():
    return parsers.LLMs_functions.answer_question()

if __name__ == '__main__':
    app.run(debug=True)
