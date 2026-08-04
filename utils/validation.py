"""
---------------------------------------------------------
Trend Analyzer for the ASX
Validation Utilities

Secures forms and parameters to prevent empty submissions,
invalid tickers, or injection attempts.

Author: Karan Attavar
---------------------------------------------------------
"""

import re


def validate_asx_ticker(ticker):
    """
    Validates ASX Stock Ticker formats.
    Standard ASX tickers are 3 alphabetical characters (e.g., BHP, CBA).
    Sometimes they include 4-character combinations for ETFs or options.
    """
    if not ticker:
        return False, "Ticker code cannot be blank."
        
    cleaned_ticker = ticker.strip().upper()
    
    # Check length constraints (generally 3 to 5 characters)
    if not (3 <= len(cleaned_ticker) <= 5):
        return False, "ASX Ticker must be between 3 and 5 characters long."
        
    # Standard alphanumeric check ensuring it doesn't contain malicious symbols
    if not re.match(r"^[A-Z0-9]+$", cleaned_ticker):
        return False, "Ticker can only contain alphanumeric characters."
        
    return True, cleaned_ticker


def validate_company_name(name):
    """
    Ensures company names do not contain system command codes or injection structures.
    """
    if not name:
        return False, "Company name cannot be blank."
        
    cleaned_name = name.strip()
    
    if len(cleaned_name) < 2:
        return False, "Company name is too short (minimum 2 characters)."
        
    if len(cleaned_name) > 100:
        return False, "Company name cannot exceed 100 characters."
        
    # Prevent common script injection tags
    if any(tag in cleaned_name.lower() for tag in ["<script>", "javascript:", "onload=", "onerror="]):
        return False, "Invalid characters detected in company name."
        
    return True, cleaned_name