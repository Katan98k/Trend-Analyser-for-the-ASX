"""Transparent source-based trustworthiness scoring for news articles."""

from urllib.parse import urlparse


class TrustworthinessAnalyzer:
    """Estimate source reliability using a documented, tiered source list."""

    # Tier 1 - Official financial bodies and premium wire services (90-95)
    # Tier 2 - Quality Australian business and national media (80-89)
    # Tier 3 - General quality media and recognised finance platforms (70-79)
    # Tier 4 - Analyst blogs and aggregators with editorial standards (60-69)
    # Unrecognised sources start at 55 and earn quality bonuses below.

    SOURCE_SCORES = {
        # --- Tier 1 ---
        "asx": 95,
        "reuters": 93,
        "bloomberg": 92,
        "associated press": 90,
        "ap news": 90,

        # --- Tier 2 ---
        "australian financial review": 88,
        "afr": 88,
        "financial times": 88,
        "ft": 88,
        "wall street journal": 87,
        "wsj": 87,
        "abc news": 87,
        "abc": 85,
        "morningstar": 85,
        "the australian": 84,
        "the conversation": 83,
        "the age": 82,
        "sydney morning herald": 82,
        "smh": 82,

        # --- Tier 3 ---
        "crikey": 79,
        "guardian": 78,
        "cnbc": 78,
        "nine": 76,
        "marketwatch": 76,
        "news.com.au": 75,
        "yahoo finance": 74,
        "investing.com": 74,
        "seven": 72,

        # --- Tier 4 ---
        "simply wall st": 70,
        "motley fool": 68,
        "seeking alpha": 64,
    }

    # Known high-quality financial domains (matched against the article URL).
    DOMAIN_SCORES = {
        "asx.com.au": 95,
        "reuters.com": 93,
        "bloomberg.com": 92,
        "apnews.com": 90,
        "afr.com": 88,
        "ft.com": 88,
        "wsj.com": 87,
        "abc.net.au": 86,
        "morningstar.com.au": 85,
        "theaustralian.com.au": 84,
        "theconversation.com": 83,
        "theage.com.au": 82,
        "smh.com.au": 82,
        "crikey.com.au": 79,
        "theguardian.com": 78,
        "cnbc.com": 78,
        "9finance.com.au": 76,
        "marketwatch.com": 76,
        "news.com.au": 75,
        "finance.yahoo.com": 74,
        "au.finance.yahoo.com": 74,
        "investing.com": 74,
        "simplywallst.com": 70,
        "fool.com.au": 68,
        "seekingalpha.com": 64,
    }

    def calculate(self, article):
        source_name = (article.get("source") or {}).get("name", "").lower()
        url = article.get("url") or ""
        domain = urlparse(url).netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]

        # Start from the base unknown-source floor
        score = 55

        # 1. Match against the source name list (checked first)
        matched = False
        for source, source_score in self.SOURCE_SCORES.items():
            if source in source_name:
                score = source_score
                matched = True
                break

        if not matched:
            # 2. Fall back to domain matching if source name didn't match
            for dom, dom_score in self.DOMAIN_SCORES.items():
                if dom in domain:
                    score = dom_score
                    break

        # 3. Article quality bonuses (max +7 total)

        # Served over HTTPS - basic authenticity signal
        if url.startswith("https://"):
            score += 3

        # Both headline and description present - article is more complete
        if article.get("title") and article.get("description"):
            score += 2

        # Longer descriptions suggest a substantive article rather than a stub
        description = article.get("description") or ""
        if len(description) > 200:
            score += 2

        return min(score, 100)
