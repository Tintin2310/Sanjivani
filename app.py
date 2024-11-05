import os
from flask import Flask, render_template, request, redirect, url_for, session
import google.generativeai as genai

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Configure Generative AI API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Create the model
generation_config = {
    "temperature": 1.2,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Updated system instruction
system_instruction = (
    "You are a supportive and understanding mental health guide, here to chat like a close friend. Your goal is to help users feel comfortable sharing what is on their mind regarding challenges like anxiety, stress, insecurity, insomnia, or other personal struggles. Rather than offering solutions right away, focus on genuinely listening and connecting with them.\n\n"
    "Use a friendly, caring tone and keep responses short and simple, just as a close friend would. Start by asking gentle, open-ended questions that show you’re interested in getting to know them better. Avoid giving advice immediately; instead, encourage them to share their thoughts and feelings freely, showing empathy and understanding with casual phrases like I hear you or Tell me more if you feel like it.\n\n"
    "Let them lead the conversation, and check in naturally to make sure they feel comfortable. When appropriate, offer gentle reminders about self-care in a friendly way, but always focus on understanding them first. Keep responses natural, relaxed, and free of any symbols, like a chat with a good friend who is truly there for them."
)

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    system_instruction=system_instruction,
)

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/dashboard', methods=['POST', 'GET'])
def dashboard():
    if request.method == 'POST':
        username = request.form['username']
        session['username'] = username
        return redirect(url_for('dashboard'))
    return render_template('dashboard.html')

@app.route('/category/<category_name>', methods=['GET', 'POST'])
def category(category_name):
    # Ensure the user is logged in
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']

    # Initialize chat history storage for each user
    if 'chat_histories' not in session:
        session['chat_histories'] = {}

    # Initialize chat history for the logged-in user if it doesn't exist
    if username not in session['chat_histories']:
        session['chat_histories'][username] = {}

    # Initialize the specific category's chat history for the user if it doesn't exist
    if category_name not in session['chat_histories'][username]:
        session['chat_histories'][username][category_name] = []

    if category_name in ['Depression', 'Anxiety', 'Addiction', 'Anger']:
        if request.method == 'POST':
            user_input = request.form['message']

            # Retrieve chat history for the current category
            chat_history = session['chat_histories'][username][category_name]

            # Prepare the chat history for the model
            model_input = "\n".join([f"{msg['sender'].capitalize()}: {msg['text']}" for msg in chat_history])
            model_input += f"\nUser: {user_input}"

            # Initialize and send message to the model
            chat_session = model.start_chat(history=[])
            response = chat_session.send_message(model_input)
            bot_response = response.text

            # Append user and bot messages to the specific category's chat history for the logged-in user
            chat_history.append({'sender': 'user', 'text': user_input})
            chat_history.append({'sender': 'bot', 'text': bot_response})

            # Save chat history back to session
            session.modified = True

            return render_template('chatbox.html', category=category_name, chat_history=chat_history)

        # Display the chat page with current chat history for the category
        return render_template('chatbox.html', category=category_name, chat_history=session['chat_histories'][username][category_name])
    
    elif category_name == 'Insomnia':
        return render_template('insomnia.html')

@app.route('/logout')
def logout():
    session.clear()  # Clear the session
    return redirect(url_for('login'))  # Redirect to the login page

if __name__ == '__main__':
    app.run(debug=True)
