import argparse
import pyttsx3
import speech_recognition as sr
import os
from dotenv import load_dotenv, find_dotenv
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from flask import Flask, request, jsonify, render_template
import wave
from pydub import AudioSegment
import io

# Initialize Flask app
app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')


# Load environment variables
_ = load_dotenv(find_dotenv())

# Set up default parameters and arguments
defaults = {
    "model": "gpt2",
    "temperature": 0.3,
    "voice": "com.apple.eloquence.en-US.Grandpa",
    "volume": 1.0,
    "rate": 200,
}

parser = argparse.ArgumentParser()
parser.add_argument("--model", type=str, default=defaults["model"])
parser.add_argument("--temperature", type=float, default=defaults["temperature"])
parser.add_argument("--voice", type=str, default=defaults["voice"])
parser.add_argument("--volume", type=float, default=defaults["volume"])
parser.add_argument("--rate", type=int, default=defaults["rate"])

args = parser.parse_args()

# Initialize model and tokenizer
tokenizer = AutoTokenizer.from_pretrained(args.model)
model = AutoModelForCausalLM.from_pretrained(args.model)

# Text-to-speech engine setup
engine = pyttsx3.init()
engine.setProperty('voice', args.voice)
engine.setProperty('volume', min(max(args.volume, 0.0), 1.0))
engine.setProperty('rate', min(max(args.rate, 20), 500))

# Speech recognition setup
recognizer = sr.Recognizer()

def generate_response(prompt):
    try:
        inputs = tokenizer(prompt, return_tensors="pt")
        outputs = model.generate(
            inputs.input_ids,
            max_length=100,
            do_sample=True,
            temperature=args.temperature,
            pad_token_id=tokenizer.eos_token_id,
            repetition_penalty=1.2
        )
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response
    except Exception as e:
        print(f"Error generating response: {e}")
        return "I'm sorry, I couldn't process that request."

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get("text", "")
    response = generate_response(user_input)
    return jsonify({"response": response})

@app.route('/audio', methods=['POST'])
def audio():
    print("Audio route accessed")
    audio_file = request.files.get('audio')
    if not audio_file:
        return jsonify({"response": "No audio file provided."}), 400

    # Check file type
    if audio_file.mimetype not in ['audio/wav', 'audio/x-wav']:
        return jsonify({"response": "Unsupported audio format. Please use WAV."}), 400

    print("Processing audio file with MIME type:", audio_file.mimetype)

    try:
        # Convert audio to WAV format
        audio = AudioSegment.from_file(io.BytesIO(audio_file.read()), format="webm")
        wav_data = io.BytesIO()
        audio.export(wav_data, format="wav")
        wav_data.seek(0)  # Rewind to the start of the file

        # Now use this `wav_data` with sr.AudioFile for speech recognition
        with sr.AudioFile(wav_data) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data)
                response = generate_response(text)
                return jsonify({"response": response})
            except sr.UnknownValueError:
                return jsonify({"response": "Sorry, I couldn't understand the audio."})
            except sr.RequestError:
                return jsonify({"response": "Speech recognition service error."})
    except Exception as e:
        print("Error processing audio file:", e)
        return jsonify({"response": "An error occurred while processing the audio file."}), 500
# @app.route('/audio', methods=['POST'])
# def audio():
#     audio_file = request.files['audio']
#     # Check file type
#     if audio_file.mimetype not in ['audio/wav', 'audio/x-wav']:
#         return jsonify({"response": "Unsupported audio format. Please use WAV."}), 400
#     audio = sr.AudioFile(BytesIO(audio_file.read()))

#     with audio as source:
#         audio_data = recognizer.record(source)
#         try:
#             text = recognizer.recognize_google(audio_data)
#             response = generate_response(text)
#             return jsonify({"response": response})
#         except sr.UnknownValueError:
#             return jsonify({"response": "Sorry, I couldn't understand the audio."})
#         except sr.RequestError:
#             return jsonify({"response": "Speech recognition service error."})

if __name__ == '__main__':
    app.run(debug=True)
