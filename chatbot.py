import argparse
import pyttsx3
import speech_recognition as sr
import os
from dotenv import load_dotenv, find_dotenv
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from flask import Flask, request, jsonify
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load environment variables
_ = load_dotenv(find_dotenv())

# Load defaults and arguments
defaults = {
    "model": "gpt2",  # Choose a local-compatible model like gpt2 or facebook/opt-1.3b
    "temperature": 0.1,
    "voice": "com.apple.eloquence.en-US.Grandpa",
    "volume": 1.0,
    "rate": 200,
    "session_id": "abc123",
    "ability": "Psychology",
}

parser = argparse.ArgumentParser()
parser.add_argument("--list_voices", action="store_true", help="List available voices")
parser.add_argument("--test_voice", action="store_true", help="Test the TTS engine")
parser.add_argument("--ptt", action="store_true", help="Use push-to-talk mode")
parser.add_argument("--ability", type=str, help="The assistant's ability", default=defaults["ability"])
parser.add_argument("--model", type=str, help="The Hugging Face model", default=defaults["model"])
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

# Load the model and tokenizer
print("Loading model and tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(args.model)
model = AutoModelForCausalLM.from_pretrained(args.model)

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

def generate_response(prompt):
    try:
        inputs = tokenizer(prompt, return_tensors="pt")
        outputs = model.generate(
            inputs.input_ids,
            attention_mask=inputs['attention_mask'],
            max_length=100,
            do_sample=True,
            temperature=temperature,
            pad_token_id=tokenizer.eos_token_id,
            repetition_penalty=1.2
        )
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response
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
    prompt = f"You are an assistant who provides accurate and direct answers. User says: '{question}'. Answer as clearly and concisely as possible."
    response = generate_response(prompt)
    
    # Speak the response
    speak(response)

    return jsonify({"answer": response})

if __name__ == "__main__":
    print("Starting server...")
    app.run(port=5000)
