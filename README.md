# Trend Analyzer for the ASX
(Side note: Sift through the headings to find the progression, it will be labled "Progress")

## Overview

Trend Analyzer for the ASX is a Flask-based web application developed to assist users in analysing Australian Securities Exchange (ASX) companies using news sentiment, financial risk analysis, statistical calculations, historical records, graphical trend visualisation, and AI-generated insights.

The application retrieves current news articles related to a selected ASX company, lets the user choose which articles to analyse, performs automated sentiment and risk analysis, calculates a Prediction Sureness Score, stores results in an SQLite database, generates historical trend graphs, and allows users to query previous analyses using the Groq AI API.

This project was developed using a modular architecture to improve readability, maintainability, scalability, and ease of future development.

---

## Features

* Search and analyse ASX-listed companies
* Retrieve live financial news using NewsAPI
* Select which retrieved articles are included in an analysis
* Automated sentiment analysis using TextBlob
* Financial risk assessment using keyword analysis
* Article source trustworthiness scoring
* Prediction Sureness Score calculation
* Historical analysis storage using SQLite
* CRUD functionality for saved analyses
* Historical trend graph generation using Matplotlib
* AI-powered summaries and saved-data queries using the Groq API
* Saved Katan AI conversations with a local fallback when Groq is unavailable
* Responsive Flask web interface
* Input validation and error handling
* Modular project structure following software engineering principles

---

## Technologies Used

### Backend

* Python 3
* Flask
* SQLite

### APIs

* NewsAPI
* Claude Api ---> Changed to Grok API (xAI) ---> Changed most recently to Groq (not xAI) API (I'm broke twin, I can't afford paying for an API)  (╥_╥)
* Current AI provider: Groq. The default model is GPT-OSS 20B served through Groq.


### Libraries

* TextBlob
* Matplotlib
* Requests
* python-dotenv

### Frontend

* HTML5
* CSS3
* Bootstrap 5
* JavaScript
* Jinja2 Templates

---

## Project Structure

```
TrendAnalyzer/

├── api/
├── analysis/
├── database/
├── graphs/
├── routes/
├── static/
├── templates/
├── utils/

app.py
config.py
requirements.txt

---
```
## Installation

1. Clone or download the project.

2. Install the required Python packages:

```powershell
pip install -r requirements.txt
```

3. Create a `.env` file in the project directory containing:

```
SECRET_KEY=your_secret_key

NEWS_API_KEY=your_newsapi_key

GROQ_API_KEY=your_groq_api_key
```

4. Run the application:

```powershell
python app.py
```

5. Open your browser and navigate to:

```text
http://127.0.0.1:5000
```

(Or whatever local address Flask prints when you run step 4 in PowerShell/VS Code.)

---

## Trouble shooting

- I will be testing the running in all sorts of ways, if I find any faults I can't fix that may need the user to debug on their side, I will include it here. 

---

## Progress:
(Version 1.2 is the current beta-adjusted application. All files are possibly subject to change.But generally this is the final verison)
```

The application is completed, no more updates will be rolled out.

---

```
## How It Works
```
1. The user enters an ASX ticker.
2. The application retrieves recent news articles.
3. The user selects which retrieved articles to include.
4. Sentiment, risk, and article trustworthiness analysis are performed.
5. A Prediction Sureness Score is calculated.
6. Results and selected article evidence are saved to the SQLite database.
7. Historical statistics and article-date trend graphs are generated.
8. Users can review previous analyses or ask Katan AI questions based on stored data.
```

---

## Automated Criterion 8 Module Tests

The repeatable white-box tests for T28-T34 are stored in
`Alpha testing/test_criterion8_modules.py`. They call the application's real analysis
classes with controlled article inputs, keeping the results independent of
live NewsAPI and Groq data.

Run them from the project folder with:

```powershell
python -m unittest discover -s "Alpha testing" -p "test_criterion8_modules.py" -v
```

See `Alpha testing/README-For-A-Testing.md` for the purpose and expected behaviour of each test ID.

---

## Disclaimer

This application is an educational software project developed for VCE Software Development. It is designed to demonstrate software engineering concepts including APIs, databases, modular programming, data analysis, graphical visualisation, and AI integration.

The application does **not** provide financial advice. Users should conduct their own research before making any investment decisions.

---

## Author

**Karan Attavar** 

Year 12 VCE Software Development



2026
