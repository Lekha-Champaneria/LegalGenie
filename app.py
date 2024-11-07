import os
from flask import Flask, render_template, request
import requests
import json
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from docx import Document

app = Flask(__name__)

chat_history = []
uploaded_file_text = ""
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(filepath):
    if filepath.endswith('.pdf'):
        reader = PdfReader(filepath)
        return "".join([page.extract_text() for page in reader.pages])
    elif filepath.endswith('.docx'):
        doc = Document(filepath)
        return "\n".join([para.text for para in doc.paragraphs])
    elif filepath.endswith('.txt'):
        with open(filepath, 'r') as file:
            return file.read()
    return ""

@app.route('/', methods=['GET', 'POST'])
def index():
    global chat_history, uploaded_file_text
    model_response = ""

    if request.method == 'POST':
        # Clear chat history if 'Clear Chat' is clicked
        if 'clear_chat' in request.form:
            chat_history = []
            uploaded_file_text = ""
            model_response = "Chat cleared."
            return render_template('index.html', answer=model_response, chat_history=chat_history)

        # Handle file upload, if any
        if 'uploaded_file' in request.files and request.files['uploaded_file'].filename != '':
            file = request.files['uploaded_file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join('uploads', filename)
                file.save(filepath)
                uploaded_file_text = extract_text_from_file(filepath)
                chat_history.append(f"File '{filename}' uploaded and processed.")
            else:
                chat_history.append("Invalid file type. Please upload a PDF, DOCX, or TXT file.")

        # Process user input text
        user_input = request.form['user_input']
        chat_history.append(f"You: {user_input}")

        # Create full prompt, append file content if available
        full_prompt = "\n".join(chat_history) + (f"\n\nFile content:\n{uploaded_file_text}" if uploaded_file_text else "")
        full_prompt += """
            Rules for Legal Genie (RAG Agent):
            1. You are only authorized to answer questions strictly related to the legality of terms and conditions documents.
            2. If no relevant file content is available, respond only with: "Please upload a terms and conditions document for analysis."
            3. Answer in a concise, factual manner and avoid engaging in any conversation or questions unrelated to terms and conditions.
            4. Ignore any questions or files not concerning terms and conditions. Do not provide any information or conversation unrelated to legality.
            5. Your responses should be focused and only provide specific legal insights or clarifications based on the uploaded document.
            6. Do not deviate from the topic. If uncertain, respond with: "I can only assist with terms and conditions-related queries."
            7. Keep your respons very very very short and to the point.
            """


        try:
            # Send request to LLaMA model
            response = requests.post("http://localhost:11434/api/generate", json={"model": "llama3.2", "prompt": full_prompt})
            for line in response.content.splitlines():
                model_response += json.loads(line.decode('utf-8')).get("response", "")
            chat_history.append(f"LLaMA: {model_response}")
        except Exception as e:
            chat_history.append(f"LLaMA: Error - {str(e)}")

        return render_template('index.html', answer=model_response, chat_history=chat_history)

    return render_template('index.html', answer="", chat_history=chat_history)

if __name__ == '__main__':
    app.run(debug=True)
