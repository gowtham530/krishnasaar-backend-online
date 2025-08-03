from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
import logging
import requests

# Optional translation
try:
    from argostranslate import package, translate
    translation_enabled = True
except ImportError:
    translation_enabled = False

from dotenv import load_dotenv
load_dotenv()

# Load Together API key
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY") or "tgp_v1_2pRyRXB_U7Dcow3nzf4ghmdZu8zGyZrhxF7SaQxxh3U"
TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"
TOGETHER_MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.2"

# App setup
app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

# Translation helper
def translate_text(text, from_lang, to_lang):
    if not translation_enabled or not text.strip() or from_lang == to_lang:
        return text
    try:
        installed_languages = translate.get_installed_languages()
        src_lang = next((l for l in installed_languages if l.code == from_lang), None)
        tgt_lang = next((l for l in installed_languages if l.code == to_lang), None)
        if src_lang and tgt_lang:
            translation = src_lang.get_translation(tgt_lang)
            return translation.translate(text)
    except Exception as e:
        logging.error(f"Translation error: {e}")
    return text

# Together API model call
def get_model_response(user_input):
    try:
        headers = {
            "Authorization": f"Bearer {TOGETHER_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": TOGETHER_MODEL_NAME,
            "messages": [
                {"role": "system", "content": "You are Lord Krishna from the Mahabharata, giving wise, spiritual, and compassionate answers."},
                {"role": "user", "content": user_input}
            ],
            "temperature": 0.7
        }

        response = requests.post(TOGETHER_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

        return result['choices'][0]['message']['content'].strip()

    except Exception as e:
        logging.error(f"Together API error: {e}")
        return None

@app.route('/chat', methods=['POST'])
def home():
    return "✅ KrishnaSaar backend is running!"
def chat():
    data = request.get_json()
    user_input = data.get("message", "")
    lang = data.get("language", "en")

    logging.info(f"User input: {user_input} | Language: {lang}")

    # Step 1: Translate input to English if needed
    input_english = translate_text(user_input, lang, "en")
    logging.info(f"Translated to English: {input_english}")

    # Step 2: Get model response from Together
    model_response = get_model_response(input_english)
    logging.info(f"Model response (EN): {model_response}")

    if not model_response:
        return jsonify({
            "audio_url": "",
            "english_reference": "Sorry, the model didn’t return a proper response.",
            "text_response": "Translation failed"
        })

    # Step 3: Translate back to target language
    final_response = translate_text(model_response, "en", lang)
    logging.info(f"Translated response to '{lang}': {final_response}")

    # Step 4: Optional audio (placeholder only)
    audio_filename = f"{uuid.uuid4().hex}.mp3"
    audio_path = os.path.join("static/audio", audio_filename)
    # [You can add TTS save here]

    return jsonify({
        "audio_url": f"/static/audio/{audio_filename}",
        "english_reference": model_response,
        "text_response": final_response
    })

if __name__ == '__main__':
    os.makedirs("static/audio", exist_ok=True)
    app.run(debug=True)

