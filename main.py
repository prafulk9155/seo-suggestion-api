import requests
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

class AnalyzeRequest(BaseModel):
    topic: str
    keywords: List[str]

def get_google_autocomplete_suggestions(query: str, max_results=10):
    url = "http://suggestqueries.google.com/complete/search"
    params = {'client': 'firefox', 'q': query}
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        suggestions = response.json()[1]
        return suggestions[:max_results]
    except Exception:
        return []

def calculate_seo_score(topic: str, keywords: List[str]) -> int:
    suggestions = get_google_autocomplete_suggestions(topic)
    matched = 0
    for kw in keywords:
        if any(kw.lower() in s.lower() or s.lower() in kw.lower() for s in suggestions):
            matched += 1
    score = int((matched / max(len(keywords), 1)) * 100)
    return score

def calculate_trending_score(topic: str) -> int:
    suggestions = get_google_autocomplete_suggestions(topic)
    words = topic.lower().split()
    count = 0
    for sug in suggestions:
        if any(word in sug.lower() for word in words):
            count += 1
    score = int((count / max(len(suggestions), 1)) * 100)
    return score

def get_related_keywords(topic: str, input_keywords: List[str], max_results=10) -> List[str]:
    suggestions = get_google_autocomplete_suggestions(topic, max_results=max_results)
    combined = list(dict.fromkeys(suggestions + input_keywords))  # unique, preserve order
    return combined[:max_results]

def suggest_text_improvements(topic: str, keywords: List[str]) -> str:
    suggestions = []
    topic_words = topic.lower().split()
    keywords_lower = [k.lower() for k in keywords]
    if not any(topic_words[0] in kw for kw in keywords_lower):
        suggestions.append(f"Add keywords including main topic word '{topic_words[0]}'")
    if any(len(k.split()) > 4 for k in keywords):
        suggestions.append("Avoid very long keywords; keep keywords concise (max 4 words)")
    if not keywords:
        suggestions.append("Add relevant keywords related to your topic")
    if not suggestions:
        return "Keywords and topic look good."
    return "Suggestions: " + "; ".join(suggestions)

@app.post("/analyze")
async def analyze(data: AnalyzeRequest):
    seo_score = calculate_seo_score(data.topic, data.keywords)
    trending_score = calculate_trending_score(data.topic)
    related_keywords = get_related_keywords(data.topic, data.keywords)
    improvement_text = suggest_text_improvements(data.topic, data.keywords)
    trending_texts = get_google_autocomplete_suggestions(data.topic, max_results=10)

    return {
        "seo_score": seo_score,
        "trending_score": trending_score,
        "related_keywords": related_keywords,
        "top_10_trending_texts": trending_texts,
        "suggestion_text": improvement_text
    }


@app.get("/")
async def root():
    return {"message": "Seo analyzation API works!"}
