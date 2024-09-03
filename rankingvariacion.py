import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Function to calculate the percentage variation between two values
def calculate_percentage_change(new_value, old_value):
    return ((new_value - old_value) / old_value) * 100

# Streamlit app
st.title("Tabla Histórica de Datos de Acciones")

# Input for stock ticker and date range
ticker = st.text_input("Ingrese el Ticker de la Acción (por ejemplo, AAPL, MSFT, TSLA):", value="AAPL").upper()

# Set the minimum date to January 1, 1980
start_date = st.date_input("Fecha de Inicio", value=pd.to_datetime("2023-01-01"), min_value=pd.to_datetime("1980-01-01"))

# Set the end date to "the day after today"
end_date = st.date_input("Fecha de Fin", value=datetime.today() + timedelta(days=1))

if st.button("Obtener Datos"):
    # Fetch data from yfinance
    stock_data = yf.download(ticker, start=start_date, end=end_date)

    if not stock_data.empty:
        # Calculate Percentage Variation from the previous trading day
        stock_data['Variación %'] = stock_data['Close'].pct_change() * 100
        
        # Calculate the distance between maximum and minimum values that day (in percentage)
        stock_data['Distancia Máx-Mín (%)'] = ((stock_data['High'] - stock_data['Low']) / stock_data['Low']) * 100
        
        # Calculate the distance between open and closing values that day (in percentage)
        stock_data['Distancia Apertura-Cierre (%)'] = ((stock_data['Close'] - stock_data['Open']) / stock_data['Open']) * 100
        
        # Prepare data for display, round to two decimals
        display_data = stock_data[['Close', 'Variación %', 'Distancia Máx-Mín (%)', 'Distancia Apertura-Cierre (%)']].round(2)

        # Add a ranking column starting from 1 after preparing the final display data
        display_data.insert(0, 'Ranking', range(1, len(display_data) + 1))
        
        # Display the data in a Streamlit data table
        st.dataframe(display_data)
    else:
        st.error("No hay datos disponibles para el rango de fechas seleccionado.")
