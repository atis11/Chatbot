import argparse
import pyttsx3
import speech_recognition as sr
import os
from dotenv import load_dotenv, find_dotenv
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load environment variables from .env
load_dotenv(find_dotenv())  # This loads variables from .env file into the environment

# Retrieve the API key from the environment variables
api_key = os.getenv("HUGGING_FACE_API_KEY")
print("Using API Key:", api_key)  # This will print the API key in the console for verification

# Check if API key is loaded (for debugging only; remove this in production)
if not api_key:
    print("Error: Hugging Face API key not found. Ensure it's in the .env file.")
else:
    print("API Key loaded successfully.")

# Hugging Face API setup
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"
headers = {"Authorization": f"Bearer {api_key}"}  # Use API key from .env file

# Other code and defaults
defaults = {
    "temperature": 0.5,
    "voice": "com.apple.eloquence.en-US.Grandpa",
    "volume": 1.0,
    "rate": 200,
    "session_id": "abc123",
}

parser = argparse.ArgumentParser()
parser.add_argument("--list_voices", action="store_true", help="List available voices")
parser.add_argument("--test_voice", action="store_true", help="Test the TTS engine")
parser.add_argument("--ptt", action="store_true", help="Use push-to-talk mode")
parser.add_argument("--temperature", type=float, help="Temperature for creativity", default=defaults["temperature"])
parser.add_argument("--voice", type=str, help="Voice for TTS", default=defaults["voice"])
parser.add_argument("--volume", type=float, help="Volume for TTS", default=defaults["volume"])
parser.add_argument("--rate", type=int, help="TTS speech rate", default=defaults["rate"])
parser.add_argument("--session_id", type=str, help="Chat session ID", default=defaults["session_id"])

args = parser.parse_args()

temperature = min(max(args.temperature, 0.0), 1.0)
interface_voice = args.voice
volume = min(max(args.volume, 0.0), 1.0)
rate = min(max(args.rate, 20), 500)
session_id = args.session_id

if args.list_voices:
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    for voice in voices:
        print(voice.id)
    exit()

if args.test_voice:
    engine = pyttsx3.init()
    engine.setProperty('voice', interface_voice)
    engine.setProperty('volume', volume)
    engine.setProperty('rate', rate)
    engine.say("Hello, I am Jarvis. How can I help you today?")
    engine.runAndWait()
    exit()

# Speech recognition setup
r = sr.Recognizer()

# Define the speak function to initialize engine each time to avoid loop issues
def speak(text):
    print("Jarvis: " + text)
    engine = pyttsx3.init()  # Initialize a new instance each time
    engine.setProperty('voice', interface_voice)
    engine.setProperty('volume', volume)
    engine.setProperty('rate', rate)
    engine.say(text)
    try:
        engine.runAndWait()
    except RuntimeError:
        pass  # Ignore if the loop is already running
    finally:
        engine.stop()  # Ensure resources are released

def listen():
    with sr.Microphone() as source:
        print("Listening... (you can type instead if preferred)")
        audio = r.listen(source, phrase_time_limit=5)
    try:
        text = r.recognize_google(audio)
        return text
    except Exception as e:
        print("Error: " + str(e))
        return None

def generate_response(question):
    # Prepare the payload for the API request
    payload = {
        "inputs": question,
        "parameters": {
            "temperature": temperature,
            "max_length": 50,
            "top_p": 0.95,
            "do_sample": True
        }
    }

    try:
        # Send a request to the Hugging Face API
        response = requests.post(API_URL, headers=headers, json=payload)
        
        # Check for HTTP errors
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code}")
            print("Response content:", response.content)
            return "I'm sorry, there was an error with the model request."

        response_data = response.json()

        # Check if 'generated_text' is in the response data
        if isinstance(response_data, list) and 'generated_text' in response_data[0]:
            answer = response_data[0]['generated_text']
        else:
            print("Unexpected response format:", response_data)
            answer = "I'm sorry, I couldn't process the response from the model."

        return answer
    except Exception as e:
        print(f"Error generating response: {e}")
        return "I'm sorry, I couldn't process that request."

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    question = data.get("question")
    if not question:
        return jsonify({"error": "No question provided"}), 400

    print("User: " + question)
    response = generate_response(question)
    
    # Speak the response
    speak(response)

    return jsonify({"answer": response})

if __name__ == "__main__":
    print("Starting server...")
    app.run(port=5000)
