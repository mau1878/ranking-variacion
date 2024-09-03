import streamlit as st
import yfinance as yf
import pandas as pd

# Function to calculate the percentage variation between two values
def calculate_percentage_change(new_value, old_value):
    return ((new_value - old_value) / old_value) * 100

# Streamlit app
st.title("Stock Historical Data Table")

# Input for stock ticker and date range
ticker = st.text_input("Enter Stock Ticker (e.g., AAPL, MSFT, TSLA):", value="AAPL").upper()

# Set the minimum date to January 1, 1980
start_date = st.date_input("Start Date", value=pd.to_datetime("2023-01-01"), min_value=pd.to_datetime("1980-01-01"))
end_date = st.date_input("End Date", value=pd.to_datetime("2023-12-31"))

if st.button("Fetch Data"):
    # Fetch data from yfinance
    stock_data = yf.download(ticker, start=start_date, end=end_date)

    if not stock_data.empty:
        # Calculate Percentage Variation from the previous trading day
        stock_data['Percentage Variation'] = stock_data['Close'].pct_change() * 100
        
        # Calculate the distance between maximum and minimum values that day (in percentage)
        stock_data['Max-Min Distance (%)'] = ((stock_data['High'] - stock_data['Low']) / stock_data['Low']) * 100
        
        # Calculate the distance between open and closing values that day (in percentage)
        stock_data['Open-Close Distance (%)'] = ((stock_data['Close'] - stock_data['Open']) / stock_data['Open']) * 100
        
        # Prepare data for display
        display_data = stock_data[['Close', 'Percentage Variation', 'Max-Min Distance (%)', 'Open-Close Distance (%)']]
        
        # Display the data in a Streamlit data table
        st.dataframe(display_data)
    else:
        st.error("No data available for the selected date range.")
