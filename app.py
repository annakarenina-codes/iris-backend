from flask import Flask, request, jsonify
from pipeline.language_detector import detect_language
from pipeline.opinion_filter import is_opinion
from pipeline.political_checker import flag_political
from pipeline.search import search_and_extract
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

def summarize_sources(source_summary, articles):
    """Groups article links by source for Postman and the future UI."""
    grouped_sources = []

    for source in source_summary:
        source_articles = [
            {
                "title": article["title"],
                "url": article["url"],
                "status": article["status"],
                "word_count": article["word_count"],
                "error": article["error"],
            }
            for article in articles
            if article["source"] == source["source"]
        ]

        grouped_sources.append({
            "source": source["source"],
            "results_found": source["results_found"],
            "articles_checked": source["articles_checked"],
            "articles_extracted": source["articles_extracted"],
            "articles": source_articles,
        })

    return grouped_sources

def get_search_status(search_result):
    """Creates a short status for the user-facing API response."""
    statuses = []
    for search in search_result["search"]["searches"]:
        for report in search["source_reports"]:
            statuses.append(report["status"])

    if "missing_api_key" in statuses:
        return {
            "verdict": "Search Not Configured",
            "status": "missing_api_key",
            "message": "Brave Search is not configured yet. Add BRAVE_API_KEY to .env."
        }

    if statuses and all(status == "error" for status in statuses):
        return {
            "verdict": "Search Failed",
            "status": "error",
            "message": "IRIS could not reach the approved sources through Brave Search."
        }

    if search_result["total_search_results"] == 0:
        return {
            "verdict": "No Search Results",
            "status": "no_results",
            "message": "IRIS searched the approved sources but found no matching results."
        }

    return {
        "verdict": "Search Complete",
        "status": "ok",
        "message": "IRIS searched the approved sources and extracted readable article text where possible."
    }

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

    search_result = search_and_extract(
        primary_query=translated,
        backup_query=text if language in ["tagalog", "taglish"] else None
    )
    search_status = get_search_status(search_result)

    response = build_response({
        "verdict": search_status["verdict"],
        "message": search_status["message"],
        "original_text": text,
        "translated_text": translated,
        "detected_language": language,
        "politically_sensitive": politically_sensitive,
        "flags": flags,
        "search_status": search_status["status"],
        "searched_sources": "VERA Files + 6 approved Philippine news sources",
        "total_search_results": search_result["total_search_results"],
        "searched_articles": search_result["searched_articles"],
        "extracted_articles": search_result["extracted_articles"],
        "source_summary": search_result["source_summary"],
        "sources": summarize_sources(
            search_result["source_summary"],
            search_result["articles"]
        )
    }, debug_enabled, opinion_result, political_result)

    if debug_enabled:
        response["debug"]["search"] = search_result["search"]
        response["debug"]["articles_with_text"] = search_result["articles"]

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
