import argparse
import pyttsx3
import speech_recognition as sr
import os
from dotenv import load_dotenv, find_dotenv
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Load environment variables
_ = load_dotenv(find_dotenv())

# Load defaults and arguments
defaults = {
    "model": "gpt2",  # Choose a local-compatible model like gpt2 or facebook/opt-1.3b
    "temperature": 0.3,
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

# Text-to-speech engine setup
engine = pyttsx3.init()
engine.setProperty('voice', interface_voice)
engine.setProperty('volume', volume)
engine.setProperty('rate', rate)

if args.list_voices:
    voices = engine.getProperty('voices')
    for voice in voices:
        print(voice.id)
    exit()

if args.test_voice:
    engine.say("Hello, I am Jarvis. How can I help you today?")
    engine.runAndWait()
    exit()

# Speech recognition setup
r = sr.Recognizer()

def speak(text):
    print("Jarvis: " + text)
    engine.say(text)
    engine.runAndWait()

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
        # Tokenize input and set attention mask
        inputs = tokenizer(prompt, return_tensors="pt")
        attention_mask = inputs['attention_mask']
        
        # Generate response with temperature, attention mask, and pad_token_id
        outputs = model.generate(
            inputs.input_ids,
            attention_mask=attention_mask,
            max_length=100,
            do_sample=True,
            temperature=temperature,
            pad_token_id=tokenizer.eos_token_id,  # Set pad token to end-of-sequence token
            repetition_penalty=1.2  # Penalizes repeated text, adjust between 1.1 to 1.5 as needed
        )


        # Decode and return the generated text
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response
    except Exception as e:
        print(f"Error generating response: {e}")
        return "I'm sorry, I couldn't process that request."


speak("Hello, I am Jarvis. How can I help you today?")

# Main loop with flexible input
while True:
    user_input = input("Type your question, or press Enter to speak: ").strip()
    
    if not user_input:
        user_input = listen()
    
    if user_input:
        print("You: " + user_input)
        if user_input.lower() == "thank you for your help":
            exit()
        prompt = f"You are an assistant who provides accurate and direct answers. User says: '{user_input}'. Answer as clearly and concisely as possible."


        
        # Generate response and handle output
        response = generate_response(user_input)
        
        # Print and speak response
        speak(response)
    else:
        speak("I'm sorry, I didn't understand that.")
