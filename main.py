import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import serpapi
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SEO Analyzation API", version="1.0.0")

# Pydantic model for /analyze endpoint
class AnalyzeRequest(BaseModel):
    topic: str
    keywords: List[str]

# Pydantic model for /serpapi endpoint
class SerpapiRequest(BaseModel):
    query: str

# Outer function to get Google autocomplete suggestions using SerpApi
def get_google_autocomplete_suggestions(topic: str, max_results: int = 10) -> List[str]:
    """Fetch Google autocomplete suggestions using SerpApi."""
    try:
        client = serpapi.Client(api_key="21895f39a905a49085b25837bebd79b950331c60d1f46e56c7dcf7d2270c933a")
        results = client.search({
            "q": topic,
            "engine": "google_autocomplete",
            "hl": "en",
            "gl": "us"
        })
        suggestions = [item["value"] for item in results.get("suggestions", [])][:max_results]
        logger.info(f"Autocomplete suggestions for topic '{topic}': {suggestions}")
        return suggestions if suggestions else ["No suggestions found"]
    except Exception as e:
        logger.error(f"Error fetching autocomplete suggestions: {str(e)}")
        return [f"Error: {str(e)}"]

# Outer function to calculate SEO score
def calculate_seo_score(topic: str, keywords: List[str]) -> int:
    """Calculate SEO score based on topic and keyword relevance in autocomplete suggestions."""
    try:
        suggestions = get_google_autocomplete_suggestions(topic)
        matched = 0
        for kw in keywords:
            if any(kw.lower() in s.lower() or s.lower() in kw.lower() for s in suggestions if s != "No suggestions found"):
                matched += 1
        score = int((matched / max(len(keywords), 1)) * 100)
        logger.info(f"SEO score for topic '{topic}': {score}")
        return score
    except Exception as e:
        logger.error(f"Error calculating SEO score: {str(e)}")
        return 0

# Outer function to calculate trending score
def calculate_trending_score(topic: str) -> int:
    """Calculate trending score based on topic word matches in autocomplete suggestions."""
    try:
        suggestions = get_google_autocomplete_suggestions(topic)
        words = topic.lower().split()
        count = 0
        for sug in suggestions:
            if sug != "No suggestions found" and any(word in sug.lower() for word in words):
                count += 1
        score = int((count / max(len(suggestions), 1)) * 100)
        logger.info(f"Trending score for topic '{topic}': {score}")
        return score
    except Exception as e:
        logger.error(f"Error calculating trending score: {str(e)}")
        return 0

# Outer function to get related keywords
def get_related_keywords(topic: str, input_keywords: List[str], max_results: int = 10) -> List[str]:
    """Fetch related keywords combining autocomplete suggestions and input keywords."""
    try:
        suggestions = get_google_autocomplete_suggestions(topic, max_results)
        combined = list(dict.fromkeys(suggestions + input_keywords))  # Unique, preserve order
        logger.info(f"Related keywords for topic '{topic}': {combined[:max_results]}")
        return combined[:max_results]
    except Exception as e:
        logger.error(f"Error fetching related keywords: {str(e)}")
        return input_keywords[:max_results]

# Outer function to suggest text improvements
def suggest_text_improvements(topic: str, keywords: List[str]) -> str:
    """Generate text improvement suggestions based on topic and keywords."""
    try:
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
        suggestion_text = "Suggestions: " + "; ".join(suggestions)
        logger.info(f"Text improvement suggestions for topic '{topic}': {suggestion_text}")
        return suggestion_text
    except Exception as e:
        logger.error(f"Error generating text improvements: {str(e)}")
        return "Unable to generate suggestions due to an error."



# /serpapi endpoint
@app.post("/serpapi")
async def serpapi_endpoint(data: SerpapiRequest):
    """Fetch Google search organic results for a given query using SerpApi."""
    try:
        client = serpapi.Client(api_key="21895f39a905a49085b25837bebd79b950331c60d1f46e56c7dcf7d2270c933a")
        results = client.search({
            "q": data.query,
            "engine": "google",
            "location": "Austin, Texas",
            "hl": "en",
            "gl": "us"
        })
        organic_results = results.get("organic_results", [])
        logger.info(f"Google search results for query '{data.query}': {len(organic_results)} results")
        return {"query": data.query, "organic_results": organic_results}
    except Exception as e:
        logger.error(f"Error in /serpapi endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

# /analyze endpoint
@app.post("/analyze")
async def analyze(data: AnalyzeRequest):
    """Analyze SEO and trending data for a given topic and keywords."""
    try:
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
    except Exception as e:
        logger.error(f"Error in /analyze endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint to check API status."""
    return {"message": "SEO Analyzation API is running!"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8440))
    uvicorn.run(app, host="0.0.0.0", port=port)
