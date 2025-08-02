from flask import Flask, request, jsonify
from gtts import gTTS
import requests
import os
import uuid

app = Flask(__name__)

TOGETHER_API_KEY = "tgp_v1_2pRyRXB_U7Dcow3nzf4ghmdZu8zGyZrhxF7SaQxxh3U"
TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"
TRANSLATE_API_URL = "https://translate.argosopentech.com/translate"

# Temporary folder for audio
AUDIO_FOLDER = "static/audio"
os.makedirs(AUDIO_FOLDER, exist_ok=True)

def translate_text(text, source_lang, target_lang):
    try:
        payload = {
            "q": text,
            "source": source_lang,
            "target": target_lang,
            "format": "text"
        }
        response = requests.post(TRANSLATE_API_URL, json=payload)
        response.raise_for_status()
        return response.json()["translatedText"]
    except Exception as e:
        print("Translation Error:", e)
        return "Translation failed"

def get_deepseek_response(prompt):
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-ai/deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    try:
        res = requests.post(TOGETHER_API_URL, headers=headers, json=payload)
        res.raise_for_status()
        return res.json()['choices'][0]['message']['content']
    except Exception as e:
        print("DeepSeek Error:", e)
        return "Sorry, the model didn’t return a proper response."

def text_to_speech(text, lang="en"):
    try:
        filename = f"{uuid.uuid4().hex}.mp3"
        filepath = os.path.join(AUDIO_FOLDER, filename)
        tts = gTTS(text=text, lang=lang)
        tts.save(filepath)
        return f"/static/audio/{filename}"
    except Exception as e:
        print("TTS Error:", e)
        return None

@app.route("/ask", methods=["POST"])
def ask():
    try:
        data = request.get_json()
        user_input = data.get("user_input", "")
        source_lang = data.get("source_lang", "en")

        # Detect target direction
        if source_lang in ["te", "hi"]:
            input_in_english = translate_text(user_input, source_lang, "en")
        else:
            input_in_english = user_input

        # Get response from DeepSeek
        bot_response_en = get_deepseek_response(input_in_english)

        # Translate back to user language
        if source_lang in ["te", "hi"]:
            bot_response_local = translate_text(bot_response_en, "en", source_lang)
        else:
            bot_response_local = bot_response_en

        # Generate voice output
        audio_url = text_to_speech(bot_response_local, lang=source_lang if source_lang in ["te", "hi"] else "en")

        return jsonify({
            "text_response": bot_response_local,
            "english_reference": bot_response_en,
            "audio_url": audio_url
        })

    except Exception as e:
        print("Server Error:", e)
        return jsonify({"error": "Server error occurred"}), 500

@app.route("/")
def home():
    return "KrishnaSaar backend is running"

if __name__ == "__main__":
    app.run(debug=True)
