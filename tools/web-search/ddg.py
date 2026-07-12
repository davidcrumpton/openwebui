"""
title: DuckDuckGo Search Extractor
author: ChatGPT
description: >
  Search DuckDuckGo and return structured search results
  with title, URL, and snippet extraction.
  No API key required.
version: 2.0.0
license: MIT
"""

import json
import re
import urllib.request
import urllib.parse


class Tools:
    """
    DuckDuckGo search-result extractor.

    INSTRUCTIONS FOR THE LLM — READ CAREFULLY:

    PRIMARY METHOD:
    search(query, max_results=5)

    Use this for web searching.

    Returns structured search results:
    - title
    - url
    - snippet

    Use cases:
    - fresh information
    - browsing the web
    - finding sources
    - summarization workflows

    Behavior:
    - Queries DuckDuckGo HTML endpoint
    - Extracts only useful search results
    - Returns compact JSON
    - No API key required
    """

    USER_AGENT = (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0 Safari/537.36"
    )

    def _fetch(self, query: str) -> str:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"

        req = urllib.request.Request(url, headers={"User-Agent": self.USER_AGENT})

        with urllib.request.urlopen(req, timeout=20) as response:
            return response.read().decode("utf-8", errors="ignore")

    def _clean(self, text: str) -> str:
        text = re.sub(r"<.*?>", "", text, flags=re.S)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _extract_results(self, html: str, max_results: int):
        results = []

        pattern = re.compile(
            r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?'
            r'(?:<a[^>]*class="result__snippet"|<div[^>]*class="result__snippet")'
            r"[^>]*>(.*?)</",
            re.S,
        )

        matches = pattern.findall(html)

        for href, title, snippet in matches[:max_results]:
            title = self._clean(title)
            snippet = self._clean(snippet)

            # DuckDuckGo redirect cleanup
            parsed = urllib.parse.urlparse(href)
            qs = urllib.parse.parse_qs(parsed.query)

            if "uddg" in qs:
                url = urllib.parse.unquote(qs["uddg"][0])
            else:
                url = href

            results.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                }
            )

        return results

    def search(self, query: str, max_results: int = 5) -> str:
        """
        Search DuckDuckGo.

        Args:
            query: search query
            max_results: number of results (1-10)

        Returns:
            JSON search results
        """
        if not query:
            return json.dumps({"error": "query is required"}, indent=2)

        max_results = max(1, min(max_results, 10))

        try:
            html = self._fetch(query)
            results = self._extract_results(html, max_results)

            return json.dumps(
                {
                    "query": query,
                    "count": len(results),
                    "results": results,
                },
                indent=2,
            )

        except Exception as e:
            return json.dumps({"error": str(e)}, indent=2)


if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "NetBSD"
    print(Tools().search(query))
