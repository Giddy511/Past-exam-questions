# flask_server.py
from flask import Flask, request, jsonify
from googletrans import Translator

app = Flask(__name__)
translator = Translator()

app.route('/')
def Translator_site():
    return render_template('')
@app.route('/api/translate', methods=['POST'])
def translate_text():
    data = request.get_json()
    text = data.get('text')
    src_lang = data.get('src_lang')
    dest_lang = data.get('dest_lang')

    if not text or not src_lang or not dest_lang:
        return jsonify({"error": "Missing 'text', 'src_lang', or 'dest_lang'"}), 400

    try:
        translation = translator.translate(text, src=src_lang, dest=dest_lang)
        return jsonify({
            "original_text": text,
            "translated_text": translation.text,
            "source_language": translation.src,
            "destination_language": translation.dest
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
