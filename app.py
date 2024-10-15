from flask import Flask, render_template, request
import os
import PyPDF2  # Library for PDF handling
import requests  # For querying the Llama model
from transformers import AutoTokenizer  # Import the tokenizer

app = Flask(__name__)

# Create a directory for uploads if it doesn't exist
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load the tokenizer
tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")  # Change this to the tokenizer you need

# Function to extract text from a PDF file
def extract_text_from_pdf(file_path):
    text = ""
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""  # Handle cases where text might not be extracted
    return text

# Function to tokenize text
def tokenize_text(text):
    tokens = tokenizer.encode(text, add_special_tokens=True)  # Tokenize the text
    return tokens[:2048]  # Truncate to the first 512 tokens

# Function to query the Llama model
def query_llama_model(tokenized_content, question):
    url = 'http://localhost:11434/api/generate'  # Ensure this is the correct endpoint
    payload = {
        'model': 'llama3.2:3b',  # Specify the model you want to use
        'context': tokenized_content,  # Send the tokenized content (array of integers)
        'question': question
    }
    response = requests.post(url, json=payload)

    # Print the raw response for debugging
    print("Response Status Code:", response.status_code)
    print("Response Content:", response.text)  # Print full response content for debugging

    if response.status_code == 200:
        try:
            return response.json().get('answer', 'No answer returned.')
        except ValueError:
            return 'Error: Could not decode JSON response. Response content: ' + response.text
    else:
        return f'Error querying the model: {response.status_code}'

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
                # Tokenize the extracted text
                tokenized_content = tokenize_text(file_content)
            else:
                answer += "Unsupported file format.<br>"
                return render_template('index.html', answer=answer)

            # Query the LLaMA model with the tokenized content and question
            model_answer = query_llama_model(tokenized_content, question)
            answer += f"Model response: {model_answer}"

    return render_template('index.html', answer=answer)

if __name__ == '__main__':
    app.run(debug=True)