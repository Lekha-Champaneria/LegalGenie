from flask import Flask, render_template, request
import requests
import json

app = Flask(__name__)

# Store the conversation history
chat_history = []

@app.route('/', methods=['GET', 'POST'])
def index():
    global chat_history

    model_response = ""  # Initialize model_response

    if request.method == 'POST':
        if 'clear_chat' in request.form:  # Check if the clear chat button was pressed
            chat_history = []  # Clear chat history
            model_response = "Chat cleared."
            return render_template('index.html', answer=model_response, chat_history=chat_history)

        user_input = request.form['user_input']
        chat_history.append(f"You: {user_input}")

        # Prepare the prompt with history
        full_prompt = "\n".join(chat_history)
        try:
            response = requests.post("http://localhost:11434/api/generate", json={"model": "llama3.2", "prompt": full_prompt})

            # Process each line of the response separately
            response_lines = response.content.splitlines()

            for line in response_lines:
                # Parse each line as a JSON object
                response_data = json.loads(line.decode('utf-8'))
                model_response_part = response_data.get("response", "")

                if model_response_part:
                    model_response += model_response_part

            # Append the model's response to the chat history
            chat_history.append(f"LLaMA: {model_response}")
        
        except json.decoder.JSONDecodeError as e:
            model_response = f"Error decoding response: {str(e)}"
            chat_history.append(f"LLaMA: {model_response}")
        
        except requests.exceptions.RequestException as e:
            model_response = f"Error reaching the model: {str(e)}"
            chat_history.append(f"LLaMA: {model_response}")

        return render_template('index.html', answer=model_response, chat_history=chat_history)

    return render_template('index.html', answer="", chat_history=chat_history)

if __name__ == '__main__':
    app.run(debug=True)
