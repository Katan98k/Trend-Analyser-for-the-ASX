"""
---------------------------------------------------------
Trend Analyzer for the ASX
News API Client Implementation
---------------------------------------------------------
"""

import requests
from config import Config
from api.cache import api_cache


class NewsAPIClient:

    def __init__(self):
        # Fallback to an empty string if config is not loaded properly
        self.api_key = getattr(Config, "NEWS_API_KEY", "")
        self.base_url = "https://newsapi.org/v2/everything"
        self.timeout = getattr(Config, "TIMEOUT", 10)


    # -----------------------------------------------------
    # ASX Company Mapping
    # -----------------------------------------------------

    ASX_COMPANIES = {

        "PGY": [
            "Pilot Energy",
            "Pilot Energy Limited",
            "ASX:PGY"
        ],

        "BHP": [
            "BHP Group",
            "BHP Billiton",
            "ASX:BHP",
            "BHP Ltd"
        ],

        "CBA": [
            "Commonwealth Bank",
            "Commonwealth Bank of Australia",
            "ASX:CBA"
        ],

        "WBC": [
            "Westpac",
            "Westpac Banking Corporation",
            "ASX:WBC"
        ]
    }


    # -----------------------------------------------------
    # Convert ticker into searchable keywords
    # -----------------------------------------------------

    def resolve_company(self, ticker, company_name=None):
        """
        Converts ASX ticker into strict search keywords.
        For tickers in the mapping, uses the known company names.
        For unknown tickers, falls back to ASX:TICKER notation plus
        the user-supplied company name when available.
        """

        ticker = ticker.upper().strip()

        if ticker in self.ASX_COMPANIES:

            return [
                f'"{keyword}"'
                for keyword in self.ASX_COMPANIES[ticker]
            ]

        # Unknown ticker — build a best-effort query
        keywords = [f'"ASX:{ticker}"']
        if company_name:
            keywords.append(f'"{company_name}"')

        return keywords



    # -----------------------------------------------------
    # Build NewsAPI Query
    # -----------------------------------------------------

    def build_query(self, keywords):
        """
        Builds strict NewsAPI search query.
        """

        if not keywords:
            return '"ASX"'


        cleaned_keywords = [
            kw.strip()
            for kw in keywords
            if kw.strip()
        ]


        return " OR ".join(cleaned_keywords)



    # -----------------------------------------------------
    # Filter irrelevant articles
    # -----------------------------------------------------

    def filter_relevant_articles(self, articles, ticker, company_name=None):
        """
        Removes unrelated articles returned by NewsAPI.
        """

        ticker = ticker.upper().strip()

        if ticker in self.ASX_COMPANIES:
            company_keywords = self.ASX_COMPANIES[ticker]
        else:
            # For unknown tickers, filter by ASX:TICKER notation
            # and the user-supplied company name when available.
            company_keywords = [f"ASX:{ticker}"]
            if company_name:
                company_keywords.append(company_name)


        filtered_articles = []


        for article in articles:

            title = article.get("title") or ""
            description = article.get("description") or ""
            content = article.get("content") or ""


            text = (
                title +
                " " +
                description +
                " " +
                content
            ).lower()


            for keyword in company_keywords:

                if keyword.lower() in text:

                    filtered_articles.append(article)
                    break


        return filtered_articles



    # -----------------------------------------------------
    # Retrieve News
    # -----------------------------------------------------

    def get_news(self, keywords, language="en", page_size=20, company_name=None):
        """
        Fetches news articles from News API.
        """


        if not self.api_key:

            print(
                "[NewsAPIClient Error] API Key is missing. "
                "Check your .env file."
            )

            return []


        original_ticker = None


        # Allow ticker input directly
        if isinstance(keywords, str):

            original_ticker = keywords.upper().strip()

            keywords = self.resolve_company(
                original_ticker,
                company_name
            )


        query = self.build_query(
            keywords
        )


        cache_key = (
            query.lower(),
            language,
            page_size,
            original_ticker
        )


        cached_articles = api_cache.get(
            cache_key
        )


        if cached_articles is not None:
            return cached_articles



        params = {

            "q": query,

            "language": language,

            "pageSize": page_size,

            "sortBy": "relevancy",

            "searchIn": "title,description,content",

            "apiKey": self.api_key

        }


        try:

            response = requests.get(
                self.base_url,
                params=params,
                timeout=self.timeout
            )


            response.raise_for_status()


            data = response.json()


            articles = data.get(
                "articles",
                []
            )


            # Remove unrelated global articles
            if original_ticker:

                articles = self.filter_relevant_articles(
                    articles,
                    original_ticker,
                    company_name
                )


            api_cache.set(
                cache_key,
                articles,
                Config.CACHE_TIMEOUT
            )


            return articles



        except requests.exceptions.RequestException as e:

            print(
                f"[NewsAPIClient Error] Failed to fetch news: {e}"
            )

            return []
