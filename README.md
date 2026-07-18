# Trend Analyzer for the ASX

## Overview

Trend Analyzer for the ASX is a Flask-based web application developed to assist users in analysing Australian Securities Exchange (ASX) companies using news sentiment, financial risk analysis, statistical calculations, historical records, graphical trend visualisation, and AI-generated insights.

The application retrieves current news articles related to a selected ASX company, performs automated sentiment and risk analysis, calculates a Prediction Sureness Score, stores results in an SQLite database, generates historical trend graphs, and allows users to query previous analyses using the Grok AI API.

This project was developed using a modular architecture to improve readability, maintainability, scalability, and ease of future development.

---

## Features

* Search and analyse ASX-listed companies
* Retrieve live financial news using NewsAPI
* Automated sentiment analysis using TextBlob
* Financial risk assessment using keyword analysis
* Prediction Sureness Score calculation
* Historical analysis storage using SQLite
* CRUD functionality for saved analyses
* Historical trend graph generation using Matplotlib
* AI-powered summaries and database queries using the Grok API
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
* Claude Api ---> Changed to Grok API (xAI) ---> Changed most recently to Groq (Not Xapi) API (I'm broke twin, I can't afford paying for an API)

### Libraries

* TextBlob
* Matplotlib
* Requests
* Pandas
* python-dotenv

### Frontend

* HTML5
* CSS3
* Bootstrap 5
* JavaScript
* Jinja2 Templates

---

## Planned Project Structure

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

## Installation

1. Clone or download the project.
2. Install the required Python packages:

```
pip install -r requirements.txt
```

3. Create a `.env` file in the project directory containing:

```
SECRET_KEY=your_secret_key

NEWS_API_KEY=your_newsapi_key

GROK_API_KEY=your_grok_api_key
```

4. Download the TextBlob language data:

```
python -m textblob.download_corpora
```

5. Run the application:

```
python app.py
```

6. Open your browser and navigate to:

```
http://127.0.0.1:5000
```

---

## How It Works

1. The user enters an ASX ticker.
2. The application retrieves recent news articles.
3. Sentiment analysis and risk analysis are performed.
4. A Prediction Sureness Score is calculated.
5. Results are saved to the SQLite database.
6. Historical statistics and trend graphs are generated.
7. Users can review previous analyses or ask AI questions based on stored data.

---

## Disclaimer

This application is an educational software project developed for VCE Software Development. It is designed to demonstrate software engineering concepts including APIs, databases, modular programming, data analysis, graphical visualisation, and AI integration.

The application does **not** provide financial advice. Users should conduct their own research before making any investment decisions.

---

## Author

**Karan Attavar** 

Year 12 VCE Software Development



2026
