import streamlit as st
import pandas as pd
import time
from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from pymongo import MongoClient
import re
import matplotlib.pyplot as plt 
import seaborn as sns 

def scrape_kayak_flights_css(origin, destination, depart_date):

    # Build URL
    base_url = "https://www.kayak.ae/flights"
    search_url = f"{base_url}/{origin}-{destination}/{depart_date}?sort=price_a"
    st.info(f"Navigating to: {search_url}")

    # Configure Chrome options
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36")

    driver = None
    scraped_data = []

    try:
        st.info("Initializing WebDriver...")
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        driver.implicitly_wait(5)
        st.success("WebDriver initialized.")
        driver.get(search_url)

        # Wait for results
        individual_results_selector_css = "div[class*='Fxw9-result-item-container']"  # Placeholder - update after inspection
        st.warning(f"Waiting for flight results using CSS selector: '{individual_results_selector_css}'...")
        wait = WebDriverWait(driver, 10)  # Increased wait time
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, individual_results_selector_css)))
        st.info("At least one result item appears to be present. Waiting for dynamic loading...")

        # Delay for dynamic content (you might need to adjust this)
        time.sleep(7)

        # Find result elements
        result_elements = driver.find_elements(By.CSS_SELECTOR, individual_results_selector_css)
        st.success(f"Found {len(result_elements)} potential flight results.")

        if not result_elements:
            st.error("No flight result elements found. Check the selector or page structure.")
            return []

        # Extract data
        count = 0
        for result in result_elements:
            count += 1
            st.warning(f"\n--- Processing Result {count} ---")
            try:
                # Price - Re-locate within the loop
                price_selector_css = "div[class*='e2GB-price-text']"
                try:
                    price_element = result.find_element(By.CSS_SELECTOR, price_selector_css)
                    price = price_element.text.strip()
                    st.success(f"  Price: {price}")
                except NoSuchElementException:
                    st.error(f"  - Warning: Price not found with selector: {price_selector_css}")
                    price = "N/A"

                # Airlines - Re-locate within the loop
                airline_selector_css = "div[class*='J0g6-operator-text']"
                try:
                    airline_element = result.find_element(By.CSS_SELECTOR, airline_selector_css)
                    airline_elements = airline_element.text.strip()
                    st.success(f"  Airlines: {airline_elements}")
                except NoSuchElementException:
                    st.error(f"  - Warning: Airlines not found with selector: {airline_selector_css}")
                    airlines = "N/A"

                # Stops - Re-locate within the loop
                stops_selector_css = "span[class*='JWEO-stops-text']"
                try:
                    stops_elements = result.find_elements(By.CSS_SELECTOR, stops_selector_css)
                    stops = ', '.join([el.text.strip() for el in stops_elements if el.text.strip()]) or "N/A"
                    st.success(f"  Stops: {stops}")
                except NoSuchElementException:
                    st.error(f"  - Warning: Stops not found with selector: {stops_selector_css}")
                    stops = "N/A"

                # Duration - Re-locate within the loop
                duration_selector_css = "div[class*='xdW8 xdW8-mod-full-airport']"
                try:
                    duration_element = result.find_element(By.CSS_SELECTOR, duration_selector_css)
                    duration = duration_element.text.strip()
                    st.success(f"  Duration: {duration}")
                except NoSuchElementException:
                    st.error(f"  - Warning: Duration not found with selector: {duration_selector_css}")
                    duration = "N/A"

                flight_info = {
                    "price": price,
                    "airlines": airline_elements,
                    "stops": stops,
                    "duration": duration,
                    "search_url": search_url
                }
                scraped_data.append(flight_info)
                st.success(f"  => Added: {airline_elements} - {price} - {stops} - {duration}")

            except NoSuchElementException as e:
                st.error(f"  - Warning: Issue processing result {count}. Skipping. Error: {e}")
                continue
            except Exception as e:
                st.error(f"  - Error processing result {count}: {e}")
                continue
    finally:
        if driver:
            st.info("Closing WebDriver.")
            driver.quit()
    return scraped_data
def write_df_to_mongoDB(  my_df,\
                          database_name = 'flights' ,\
                          collection_name = 'last_scraped',
                          server = 'localhost',\
                          mongodb_port = 27017,\
                          chunk_size = 100):

    client = MongoClient('localhost',int(mongodb_port))
    db = client[database_name]
    collection = db[collection_name]
    # To write
    #collection.delete_many({})  # Destroy the collection
    #aux_df=aux_df.drop_duplicates(subset=None, keep='last') # To avoid repetitions
    my_list = my_df.to_dict('records')
    l =  len(my_list)
    ran = range(l)
    steps=ran[chunk_size::chunk_size]
    steps.extend([l])

    # Inser chunks of the dataframe
    i = 0
    for j in steps:
        print (j)
        collection.insert_many(my_list[i:j]) # fill de collection
        i = j

    print('Done')
    return
def convert_to_minutes(duration):
    match = re.search(r'(\d+)h\s+(\d+)m', duration) # separating hours and minutes
    if match:
        hours = int(match.group(1)) if match.group(1) else 0 
        minutes = int(match.group(2)) if match.group(2) else 0
        duration_in_minutes = hours * 60 + minutes # covering to minutes
        return duration_in_minutes
    return None
def convert_to_usd(price):
    only_price = price[4:].replace(',', '')
    price_in_usd = int(only_price) * 0.27 #covering the currency
    return price_in_usd
def convert_to_int(stops):
    return 0 if stops == 'direct' else int(stops[0]) # if it direct it will return zero


st.set_page_config(page_title="Airport Scraper", page_icon="", layout="centered")
    
tab1, tab2, tab3 = st.tabs(["scraping bot", "mongodb exploration", "analysis"])
    
with tab1:
    st.title("✈️ Flight Scraper Tool")

    #Predefined Airport Options
    airport_options = ["CAI", "DXB", "DOH", "JED", "RUH", "DMM", "IST", "LHR", "CDG","HBE","HKG"]

    #User Input
    st.subheader("Choose origin Airports")
    origin_city = st.selectbox(
        "Select one Arrival Airports", 
        options=airport_options    
    )

    st.subheader("🛫 Choose destination Airports")
    destination_city = st.selectbox(
        "Select one  Initial Airports",
        options=airport_options,
        
    )

    initial_date = st.date_input("Initial Date")


    # ====== Scraping Section ======
    if st.button("🚀 Start Scraping"):
        with st.spinner("Starting the scraping process..."):
            scraped_data= scrape_kayak_flights_css(
                origin=origin_city,
                destination=destination_city,
                depart_date=initial_date.strftime("%Y-%m-%d"),
            )
            
            # Show results
            df = pd.DataFrame(scraped_data)
            st.subheader("Flights Found")
            st.dataframe(df)

            # Offer download
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("⬇Download Results as CSV", csv, "scraped_flights.csv", "text/csv")

            #offer load to mongodb
    if st.button("Load to MongoDB"):
        with st.spinner("Loading data to MongoDB..."):
            write_df_to_mongoDB(df)
        st.success("Data loaded to MongoDB successfully!")
        st.balloons()

with tab2:
    st.subheader("MongoDB Data")
    # Connect to MongoDB and fetch data
    client = MongoClient('localhost', 27017)
    db = client['flights']
    collection = db['last_scraped']
    num=st.slider("Select number of showed data", 10,1000)
    
    # Fetch data from MongoDB
    data = list(collection.find())
    if data:
        df_mongo = pd.DataFrame(data)
        st.dataframe(df_mongo.head(num))  # Display first 100 records
    else:
        st.warning("No data found in MongoDB.")

with tab3:
    st.subheader("Data Analysis")
    # datapreprocessing
    df_mongo['airlines'] = df_mongo['airlines'].astype(str)
    df_mongo['duration'] = df_mongo['duration'].apply(convert_to_minutes)        
    df_mongo['price'] = df_mongo['price'].apply(convert_to_usd)
    df_mongo['stops'] = df_mongo['stops'].apply(convert_to_int)
    st.dataframe(df_mongo.describe())
    
    st.subheader("data visualization")
    
    #first chart
    st.write("Top 10 Avarage Price per Destinations")
    top_destinations = df_mongo["destination"].value_counts().head(10).index
    top_avg_price_per_dest = df_mongo[df_mongo["destination"].isin(top_destinations)].groupby("destination")['price'].mean().sort_values(ascending = False)
    st.bar_chart(top_avg_price_per_dest)
    st.write("Some destinations (like MLA and PRG) have relatively lower average prices compared to others.\n " \
    "Prices vary significantly by location, likely due to distance or airline competition.")
    
    #second chart
    st.write("Top 10 Avarage Price per airline")
    top_destinations = df_mongo["airlines"].value_counts().head(10).index
    top_avg_price_per_dest_air = df_mongo[df_mongo["airlines"].isin(top_destinations)].groupby("airlines")['price'].mean().sort_values(ascending = False)
    st.bar_chart(top_avg_price_per_dest_air)
    st.write("Airlines like Delta and United Airlines show higher average ticket prices.\n" \
    " Budget carriers like Wizz Air and Air Arabia offer lower average prices.")

    #third chart

    correlation_matrix = df_mongo[["price", "stops", "duration"]].corr()
    fig, ax = plt.subplots(figsize=(6, 4))  # Create a Matplotlib figure and axes
    sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm", ax=ax) 
    ax.set_title("Correlation Matrix") 
    st.pyplot(fig, use_container_width = True ) 
    
    #fourth chart
    st.write("avrage price per stop")
    avg_price_per_stop = df_mongo[["stops", "price"]].groupby("stops")['price'].mean()
    st.bar_chart(avg_price_per_stop)
    st.write("increasing the number of stops will increase the price \n but that also indicates that the distination is further away")

    #fifth chart
    st.write("price vs duration")
    df_scater=df_mongo[["price","duration"]]
    st.scatter_chart(df_scater, x="price", y="duration")