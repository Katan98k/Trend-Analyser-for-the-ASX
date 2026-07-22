"""
---------------------------------------------------------
Trend Analyzer for the ASX
Groq API Client Implementation
---------------------------------------------------------
"""

import requests

from config import Config


class GroqClient:

    DEFAULT_MODELS = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768"
    ]

    def __init__(self):
        self.api_key = getattr(Config, "GROQ_API_KEY", "") or getattr(Config, "GROK_API_KEY", "")
        self.base_url = getattr(Config, "GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
        self.timeout = getattr(Config, "TIMEOUT", 15)
        self.model = getattr(Config, "GROQ_MODEL", "") or getattr(Config, "GROK_MODEL", "")

    def _build_payload(self, model, system_prompt, user_prompt):
        return {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 800
        }

    def send_request(self, system_prompt, user_prompt):
        """
        Sends a POST request to the Groq completions endpoint.
        """
        if not self.api_key:
            return "Groq API key is not configured. The analysis can still be saved locally, but AI-generated summaries are unavailable until the key is added."

        models_to_try = []
        if self.model:
            models_to_try.append(self.model)

        for fallback in self.DEFAULT_MODELS:
            if fallback not in models_to_try:
                models_to_try.append(fallback)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        last_error_text = None
        response = None

        for model_name in models_to_try:
            payload = self._build_payload(model_name, system_prompt, user_prompt)
            try:
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
            except requests.exceptions.HTTPError as e:
                error_text = ""
                status = None
                if response is not None:
                    status = getattr(response, "status_code", None)
                    try:
                        error_data = response.json()
                        error_text = (
                            error_data.get("error") or
                            error_data.get("message") or
                            error_data.get("detail") or
                            response.text
                        )
                    except ValueError:
                        error_text = response.text

                normalized = (error_text or "").lower()
                print(f"[GroqClient HTTPError] model={model_name} {e} - {error_text}")

                if "incorrect api key" in normalized or "invalid api key" in normalized or "unauthorized" in normalized:
                    return (
                        "Groq API key appears to be invalid or unauthorized. "
                        "Please verify your GROQ_API_KEY in .env and that the key has access to the requested model."
                    )

                if status == 400 and ("model not found" in normalized or "model not supported" in normalized):
                    last_error_text = error_text
                    continue

                last_error_text = error_text
                continue
            except requests.exceptions.RequestException as e:
                print(f"[GroqClient Error] model={model_name} Failed API communication: {e}")
                last_error_text = str(e)
                continue

        fallback_message = (
            "Groq AI could not produce a response. Please check the following:\n"
            "1) Ensure your GROQ_API_KEY is valid and has the right permissions.\n"
            "2) Verify GROQ_MODEL in .env is set to a supported model name.\n"
            "3) Confirm network connectivity to the Groq API endpoint."
        )
        if last_error_text:
            fallback_message += f"\nLast error: {last_error_text}"
        return fallback_message

    def test_connection(self):
        """Run a short diagnostic request against Groq to verify connectivity."""
        result = self.send_request(
            "You are a diagnostic assistant. Reply with the word 'online'.",
            "Ping"
        )
        if isinstance(result, str):
            normalized = result.lower()
            if any(err in normalized for err in [
                "invalid api key",
                "incorrect api key",
                "unauthorized",
                "could not produce a response",
                "groq api key appears to be invalid",
                "model not found",
                "model not supported",
                "error occurred"
            ]):
                return False, result
        return True, result

    def summarise_records(self, records):
        """
        Takes database records (historical stock trend data) and
        formats them into a clean summary.
        """
        if not records:
            return "No historical analysis records found to summarize."

        formatted_history = ""
        for i, r in enumerate(records, 1):
            formatted_history += (
                f"Record #{i} (Time: {r[1]}):\n"
                f"- Keywords Analyzed: {r[2]}\n"
                f"- Market Sentiment: {r[3]}/100\n"
                f"- Market Risk: {r[4]}/100\n"
                f"- AI Confidence (Sureness): {r[5]}/100\n"
                f"- Articles Analyzed: {r[6]}\n"
                f"-----------------------------------------\n"
            )

        system_prompt = (
            "You are an expert ASX Stock Market Analyst. Your goal is to look at "
            "the trend history of sentiment, risk, and confidence metrics over past runs "
            "and provide an actionable summary."
        )

        user_prompt = (
            "Here is the historical record of recent sentiment analyses on the ASX:\n\n"
            f"{formatted_history}\n"
            "Please analyze these trends and write a concise, bulleted report covering:\n"
            "1. Notable shifts or consistency in market sentiment vs risk.\n"
            "2. Critical warnings or positive indicators for the current outlook.\n"
            "3. Recommendations based on the analyzed timeframe."
        )

        return self.send_request(system_prompt, user_prompt)

    def ask_database(self, user_query, database_context):
        """
        Lets the user converse with their database trends.
        """
        system_prompt = (
            "You are Katan, a friendly and professional specialist in ASX market analysis. "
            "Be clear, composed, and helpful; use approachable language while retaining analytical precision. "
            "Do not use slang, hype, or make financial recommendations unless the user particularly asks for them. Even still do warn them that you cannot give them real financial advice, that is something they must decide for themself."
            "Use the provided context database statistics to answer questions about historical stock sentiment, "
            "risk ratios, or trend activity. "
            "When you make a claim based on stored data, cite the supporting record in the format "
            "[TICKER]."
        )

        user_prompt = (
            f"Database Context Summary:\n{database_context}\n\n"
            f"User Question: {user_query}"
        )

        return self.send_request(system_prompt, user_prompt)
      
