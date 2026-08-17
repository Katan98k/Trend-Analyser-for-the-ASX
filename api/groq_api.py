"""
---------------------------------------------------------
Trend Analyzer for the ASX
Groq API Client

Builds authenticated LLM requests, selects supported fallback
models, and returns clear diagnostic messages on API failure.

Author: Karan Attavar
---------------------------------------------------------
"""

import requests

from config import Config


class GroqClient:
    """Communicate with Groq's OpenAI-compatible chat completion endpoint."""

    DEFAULT_MODELS = [
        "openai/gpt-oss-20b",
        "qwen/qwen3.6-27b",
        "openai/gpt-oss-120b"
    ]

    def __init__(self):
        """Load API credentials, endpoint, timeout, and preferred model."""
        self.api_key = getattr(Config, "GROQ_API_KEY", "") or getattr(Config, "GROK_API_KEY", "")
        self.base_url = getattr(Config, "GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
        self.timeout = getattr(Config, "TIMEOUT", 15)
        self.model = getattr(Config, "GROQ_MODEL", "") or getattr(Config, "GROK_MODEL", "")

    def _build_payload(self, model, system_prompt, user_prompt):
        """Build the JSON body expected by the Groq chat endpoint."""
        return {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 800
        }

    @staticmethod
    def _response_error_text(response):
        """Return a readable error message from either Groq error shape."""
        fallback_text = str(getattr(response, "text", "") or "")

        try:
            error_data = response.json()
        except ValueError:
            return fallback_text

        if not isinstance(error_data, dict):
            return fallback_text

        error = error_data.get("error")
        if isinstance(error, dict):
            error = (
                error.get("message")
                or error.get("detail")
                or error.get("code")
            )

        return str(
            error
            or error_data.get("message")
            or error_data.get("detail")
            or fallback_text
        )

    @staticmethod
    def _is_model_unavailable(error_text):
        """Return whether Groq rejected a model that can be replaced."""
        normalized = (error_text or "").lower()
        return any(signal in normalized for signal in [
            "model not found",
            "model not supported",
            "model does not exist",
            "has been decommissioned",
            "no longer supported"
        ])

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
                content = data["choices"][0]["message"]["content"]
                if not isinstance(content, str) or not content.strip():
                    raise ValueError("Groq returned an empty completion")
                return content.strip()
            except requests.exceptions.HTTPError as e:
                status = None
                if response is not None:
                    status = getattr(response, "status_code", None)
                    error_text = self._response_error_text(response)
                else:
                    error_text = str(e)

                normalized = (error_text or "").lower()
                print(f"[GroqClient HTTPError] model={model_name} {e} - {error_text}")

                if "incorrect api key" in normalized or "invalid api key" in normalized or "unauthorized" in normalized:
                    return (
                        "Groq API key appears to be invalid or unauthorized. "
                        "Please verify your GROQ_API_KEY in .env and that the key has access to the requested model."
                    )

                if status == 400 and self._is_model_unavailable(normalized):
                    last_error_text = error_text
                    continue

                last_error_text = error_text
                continue
            except (KeyError, IndexError, TypeError, ValueError) as e:
                # A successful HTTP status can still contain an unexpected
                # body. Treat it like an unavailable model rather than
                # allowing the analysis route to fail with a 500 error.
                last_error_text = f"Unexpected Groq response: {e}"
                print(f"[GroqClient Response Error] model={model_name} {last_error_text}")
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

    def _diagnostic_result(self, success, state, title, message, action, fallback_available=True):
        """Return a consistent, user-facing diagnostic response for Settings."""
        return {
            "success": success,
            "state": state,
            "title": title,
            "message": message,
            "action": action,
            "fallback_available": fallback_available
        }

    def test_connection(self):
        """Run a short diagnostic request against Groq to verify connectivity."""
        if not self.api_key:
            return self._diagnostic_result(
                False,
                "missing_key",
                "Groq API key is missing",
                "Katan can still use the local fallback, but Groq-generated answers are unavailable until an API key is added.",
                "Add GROQ_API_KEY to the .env file, then restart the app and test again."
            )

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

        last_error = ""
        for model_name in models_to_try:
            payload = self._build_payload(
                model_name,
                "You are a diagnostic assistant. Reply with the word 'online'.",
                "Ping"
            )
            try:
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                answer = data["choices"][0]["message"]["content"].strip()
                if not answer:
                    raise ValueError("Groq returned an empty completion")
                return self._diagnostic_result(
                    True,
                    "online",
                    "Groq connection online",
                    f"Groq responded successfully. Response: {answer}",
                    "No action required.",
                    fallback_available=True
                )
            except requests.exceptions.Timeout as e:
                last_error = str(e)
                return self._diagnostic_result(
                    False,
                    "timeout",
                    "Groq connection timed out",
                    "The app reached Groq but did not receive a response before the timeout.",
                    "Check your internet connection and try again. Katan can still use the local fallback while Groq is unavailable."
                )
            except requests.exceptions.ConnectionError as e:
                last_error = str(e)
                return self._diagnostic_result(
                    False,
                    "network_error",
                    "Groq network connection failed",
                    "The app could not reach the Groq API endpoint.",
                    "Check internet access, school/home network blocking, and the Groq endpoint setting. Katan can still use the local fallback."
                )
            except requests.exceptions.HTTPError:
                error_text = self._response_error_text(response)

                normalized = (error_text or "").lower()
                last_error = error_text
                print(f"[Groq Diagnostic HTTPError] model={model_name} {response.status_code} - {error_text}")

                if response.status_code in (401, 403) or any(
                    signal in normalized for signal in ["incorrect api key", "invalid api key", "unauthorized"]
                ):
                    return self._diagnostic_result(
                        False,
                        "auth_error",
                        "Groq authentication failed",
                        "The configured Groq API key was rejected.",
                        "Check GROQ_API_KEY in .env and make sure the key is active. Katan can still use the local fallback."
                    )

                if self._is_model_unavailable(normalized):
                    continue

                return self._diagnostic_result(
                    False,
                    "api_error",
                    "Groq returned an API error",
                    error_text or "Groq rejected the diagnostic request.",
                    "Check the Groq endpoint, model, account status and API limits. Katan can still use the local fallback."
                )
            except (KeyError, ValueError) as e:
                last_error = str(e)
                return self._diagnostic_result(
                    False,
                    "bad_response",
                    "Groq returned an unexpected response",
                    "The API replied, but the app could not read the expected response format.",
                    "Try again later or check whether the Groq API response format has changed."
                )
            except requests.exceptions.RequestException as e:
                last_error = str(e)
                print(f"[Groq Diagnostic Error] model={model_name} Failed API communication: {e}")

        return self._diagnostic_result(
            False,
            "model_error",
            "No supported Groq model responded",
            f"The app tried the configured/fallback models but none completed successfully. Last error: {last_error}",
            "Update GROQ_MODEL in .env to a currently supported Groq chat model. Katan can still use the local fallback."
        )

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
