"""
title: Link Fetch Tool
author: davidcrumpton
description: >
 Fetches a HTTP link using GET
version: 1.3.1
license: MIT
"""

import json
import re
import time
import random
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Tools:
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    ]

    def _fetch(self, url: str) -> dict:
        """
        Internal method to fetch URL content and follow redirects.
        Returns a dictionary with final URL, HTTP status code, and content.
        """
        max_retries = 3
        current_url = url

        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(
                    current_url, headers={"User-Agent": random.choice(self.USER_AGENTS)}
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    # Check if the response is a redirect (3xx)
                    if 300 <= response.getcode() < 400 and response.getheader(
                        "Location"
                    ):
                        final_url = response.geturl()
                        logger.info(f"Redirect detected: {current_url} -> {final_url}")
                        current_url = final_url
                        continue  # Retry with the new URL

                    content = response.read().decode("utf-8", errors="ignore")
                    return {
                        "status": "success",
                        "original_url": url,
                        "final_url": current_url,
                        "http_status_code": response.getcode(),
                        "content": content,
                    }
            except urllib.error.URLError as e:
                if (
                    attempt == max_retries - 1
                    or not hasattr(e, "reason")
                    or isinstance(e.reason, str)
                ):
                    raise Exception(f"Failed to fetch {current_url}: {e.reason}")
                time.sleep(1 * (attempt + 1))
            except Exception as e:
                logger.error(f"Unexpected error fetching {current_url}: {str(e)}")
                raise
        return {"status": "error", "message": f"Max retries exceeded for {url}"}

    def _strip_html(self, html: str) -> str:
        """Strips HTML tags and returns clean text."""
        try:
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            return re.sub(r"\s+", " ", text).strip()
        except Exception as e:
            logger.error(f"HTML stripping failed: {e}")
            return html

    def fetch(self, url: str, strip_html: bool = True) -> dict:
        """
        Fetches URL content with optional HTML stripping.
        Automatically follows redirects (e.g., 302) and returns final URL.
        Returns structured metadata and content.
        """
        if not url or not urllib.parse.urlparse(url).netloc:
            return {"error": "Invalid URL"}

        try:
            start_time = time.time()
            fetch_result = self._fetch(url)
            content = fetch_result["content"]
            plain_text = self._strip_html(content) if strip_html else content
            fetch_time = round(time.time() - start_time, 2)

            return {
                "status": "success",
                "original_url": url,
                "final_url": fetch_result["final_url"],
                "http_status_code": fetch_result["http_status_code"],
                "content_type": "text" if strip_html else "html",
                "content_length": len(plain_text),
                "fetch_time_seconds": fetch_time,
                "content": plain_text,
            }
        except Exception as e:
            logger.error(f"Fetch failed for {url}: {str(e)}")
            return {"status": "error", "message": str(e)}
