from flask import Flask, request, jsonify
from pipeline.language_detector import detect_language
from pipeline.opinion_filter import is_opinion
from pipeline.political_checker import flag_political
from pipeline.translator import translate_to_english

app = Flask(__name__)
app.json.sort_keys = False

def build_response(base_response, debug_enabled, opinion_result, political_result):
    """
    Keeps normal API responses clean, but allows detailed matching info when
    Postman sends: { "text": "...", "debug": true }
    """
    if debug_enabled:
        base_response["debug"] = {
            "opinion_analysis": opinion_result,
            "political_analysis": political_result
        }

    return base_response

@app.route('/verify', methods=['POST'])
def verify():
    data = request.get_json()

    if not data or 'text' not in data:
        return jsonify({ "error": "No text provided" }), 400

    text = data['text'].strip()
    debug_enabled = bool(data.get("debug", False))

    if not text:
        return jsonify({ "error": "Text cannot be empty" }), 400

    # Step 1: Detect language
    language = detect_language(text)

    # Step 2: Translate if needed
    translated = translate_to_english(text, language)

    # Step 3: Detect obvious opinions before spending search/API resources
    opinion_result = is_opinion(text)

    # Step 4: Add political sensitivity flag. This is an overlay, not a verdict.
    political_result = flag_political(text)
    politically_sensitive = political_result["politically_sensitive"]
    flags = ["politically_sensitive"] if politically_sensitive else []

    if opinion_result["is_opinion"]:
        response = build_response({
            "verdict": "Opinion Detected",
            "message": "This appears to be an opinion, so IRIS did not perform fact-checking.",
            "original_text": text,
            "translated_text": translated,
            "detected_language": language,
            "politically_sensitive": politically_sensitive,
            "flags": flags
        }, debug_enabled, opinion_result, political_result)

        return jsonify(response)

    response = build_response({
        "verdict": "Preprocessing Complete",
        "message": "The text is ready for search and article extraction.",
        "original_text": text,
        "translated_text": translated,
        "detected_language": language,
        "politically_sensitive": politically_sensitive,
        "flags": flags
    }, debug_enabled, opinion_result, political_result)

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
