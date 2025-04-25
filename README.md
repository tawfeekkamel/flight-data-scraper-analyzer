# Flight Data Scraper and Analyzer

This application scrapes flight data from Kayak.ae, stores it in MongoDB, and provides a Streamlit interface for analysis and visualization.

## Features

* Scrapes flight price, airline, duration, and stop information.
* Allows users to select origin and destination airports and departure dates.
* Stores scraped data in a MongoDB database.
* Provides data cleaning and transformation (currency conversion, duration to minutes, etc.).
* Visualizes data using bar charts and scatter plots (e.g., price vs. destination, price vs. airline).
* Displays a correlation matrix of price, stops, and duration.

## Prerequisites

* Python 3.7+
* MongoDB installed and running
* Chrome browser installed

## Installation

1.  Clone the repository:
    ```bash
    git clone <[repository_url](https://github.com/tawfeekkamel/flight-data-scraper-analyzer/)>
    cd flight-data-scraper-analyzer
    ```
2.  Create a virtual environment (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Linux/macOS
    venv\Scripts\activate  # On Windows
    ```
3.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  Ensure MongoDB is running on the default port (27017) or update the connection details in `app.py`.
2.  Run the Streamlit application:
    ```bash
    streamlit run app.py
    ```
3.  Open your browser to the displayed URL (usually `http://localhost:8501`).

## MongoDB Setup

* The application assumes MongoDB is running on `localhost:27017`.
* You may need to adjust the connection string in `app.py` if your MongoDB instance is configured differently.
* The database name used is `flights`, and the collection name is `last_scraped`.

## Notes

* Web scraping can be fragile.  Kayak's website structure may change, requiring updates to the CSS selectors in `app.py`.
* Be mindful of Kayak's terms of service and scraping policies.  Don't overload their servers.
* Consider adding error handling and logging for production use.
* The currency conversion rate (0.27) is hardcoded in `app.py`. You might want to make this configurable or fetch it dynamically.

