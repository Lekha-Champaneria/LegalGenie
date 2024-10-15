from flask import Flask, render_template, request
import os
import PyPDF2  # Library for PDF handling
import requests  # For querying the Llama model

app = Flask(__name__)

# Create a directory for uploads if it doesn't exist
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Function to extract text from a PDF file
def extract_text_from_pdf(file_path):
    text = ""
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text()
    return text

# Function to query the Llama model
def query_llama_model(file_content, question):
    url = 'http://your-ollama-model-endpoint'  # Replace with your model's URL
    payload = {
        'context': file_content,
        'question': question
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json().get('answer', 'No answer returned.')
    else:
        return 'Error querying the model.'

@app.route('/', methods=['GET', 'POST'])
def index():
    answer = ""
    if request.method == 'POST':
        question = request.form.get('question')
        file = request.files.get('file')
        
        if file:
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)
            answer += f"File '{file.filename}' uploaded successfully.<br>"
            
            # Extract text from the uploaded file
            if file.filename.endswith('.pdf'):
                file_content = extract_text_from_pdf(file_path)
            else:
                answer += "Unsupported file format.<br>"
                return render_template('index.html', answer=answer)

            # Query the Llama model with the extracted content and question
            model_answer = query_llama_model(file_content, question)
            answer += f"Model response: {model_answer}"

    return render_template('index.html', answer=answer)

if __name__ == '__main__':
    app.run(debug=True)
