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
        text = "".join([page.extract_text() for page in reader.pages])
        return text.strip()
    elif filepath.endswith('.docx'):
        doc = Document(filepath)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text.strip()
    elif filepath.endswith('.txt'):
        with open(filepath, 'r') as file:
            text = file.read()
            return text.strip()
    return ""

def is_terms_and_conditions(content):
    """Check if the uploaded file content is related to terms and conditions."""
    keywords = ["terms and conditions", "agreement", "terms of service", "privacy policy"]
    for keyword in keywords:
        if keyword.lower() in content.lower():
            return True
    return False

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

        # Handle file upload
        if 'uploaded_file' in request.files and request.files['uploaded_file'].filename != '':
            file = request.files['uploaded_file']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join('uploads', filename)
                file.save(filepath)
                uploaded_file_text = extract_text_from_file(filepath)

                if not uploaded_file_text:
                    uploaded_file_text = ""
                    chat_history.append(f"File '{filename}' is empty. THE FILE IS EMPTY.")
                elif not is_terms_and_conditions(uploaded_file_text):
                    uploaded_file_text = ""
                    chat_history.append(f"File '{filename}' does not appear to be a terms and conditions document.")
                else:
                    chat_history.append(f"File '{filename}' uploaded and processed.")
            else:
                chat_history.append("Invalid file type. Please upload a PDF, DOCX, or TXT file.")

        # Process user input text
        user_input = request.form['user_input'].strip()
        if not user_input:
            model_response = "No input provided. Please enter a query or upload a document."
        else:
            chat_history.append(f"You: {user_input}")

            if not uploaded_file_text:
                model_response = "No valid terms and conditions document uploaded. Please upload a relevant document."
            else:
                # Create full prompt with user input and file content
                full_prompt = f"User Query: {user_input}\n\nFile content:\n{uploaded_file_text}"
                full_prompt += """
                    Rules for Legal Genie (RAG Agent):
                    1. Answer only questions related to terms and conditions documents.
                    2. If no relevant content is available, respond: "The content provided is unrelated to terms and conditions."
                    3. If the file is empty, respond: "THE FILE IS EMPTY."
                    4. Provide concise, factual answers to legal questions about terms and conditions.
                    5. Ignore unrelated queries. If uncertain, respond: "I can only assist with terms and conditions-related queries."
                    STRICTLY NOTE TO: 
                    - Give vanilla html response only and KEEP YOUR RESPONSE VERY SHORT.
                """

                try:
                    # Send request to LLaMA model
                    response = requests.post("http://localhost:11434/api/generate", json={"model": "llama3.2", "prompt": full_prompt})
                    for line in response.content.splitlines():
                        model_response += json.loads(line.decode('utf-8')).get("response", "")
                except Exception as e:
                    model_response = "Error in processing the request. Please try again."

            # Append response to chat history
            chat_history.append(f"Genie: {model_response}")

        return render_template('index.html', answer=model_response, chat_history=chat_history)

    return render_template('index.html', answer="", chat_history=chat_history)

if __name__ == '__main__':
    app.run(debug=True)
