# Criterion 8 Module Tester

`test_criterion8_modules.py` contains the repeatable white-box tests used for
T28-T34 in the Criterion 8 testing report.

The tester imports the real `SentimentAnalyzer`, `RiskAnalyzer`,
`SurenessAnalyzer`, `TrustworthinessAnalyzer`, and analysis fallback function
from the application. It supplies controlled NewsAPI-shaped articles so the
results do not change according to live news or external API availability.

## Run the tester

From the `Trend Analyser for the ASX` project folder, run:

```powershell
$env:PYTHONPATH = (Get-Location).Path
python ".\Alpha testing\test_criterion8_modules.py"
```

If the virtual environment is not already active, run:

```powershell
$env:PYTHONPATH = (Get-Location).Path
.\.venv\Scripts\python.exe ".\Alpha testing\test_criterion8_modules.py"
```

The tester prints every Criterion 8 test ID and behaviour. A failed assertion is
reported as `FAIL`; the command also returns a non-zero exit code so the tester
can later be used in automated Git checks.

## Test mapping

| Test ID | Module behaviour checked |
|---|---|
| T28 | Groq failure activates the local analysis-summary fallback |
| T29 | Positive financial language produces strongly positive sentiment |
| T30 | Severe negative language produces negative sentiment and high risk |
| T31 | Neutral and empty article text returns safe bounded defaults |
| T32 | A recognised Reuters source receives a high trust score |
| T33 | An unknown source receives a lower trust score |
| T34 | Five supporting articles produce more sureness than one article |
