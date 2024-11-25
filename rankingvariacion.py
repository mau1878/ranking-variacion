import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests

# Function to calculate the percentage variation between two values
def calculate_percentage_change(new_value, old_value):
  return ((new_value - old_value) / old_value) * 100

# Function to fetch data from IOL
def fetch_iol_data(ticker, start_date, end_date):
    try:
        cookies = {
            'intencionApertura': '0',
            '__RequestVerificationToken': 'DTGdEz0miQYq1kY8y4XItWgHI9HrWQwXms6xnwndhugh0_zJxYQvnLiJxNk4b14NmVEmYGhdfSCCh8wuR0ZhVQ-oJzo1',
            'isLogged': '1',
            'uid': '1107644',
        }

        headers = {
            'accept': '*/*',
            'content-type': 'text/plain',
            'referer': 'https://iol.invertironline.com/titulo/cotizacion/BCBA/',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        }

        # Convert dates to timestamps
        # Set start_date to beginning of day (00:00:00)
        from_timestamp = int(datetime.combine(start_date, datetime.min.time()).timestamp())
        # Set end_date to end of day (23:59:59)
        to_timestamp = int(datetime.combine(end_date, datetime.max.time()).timestamp())

        # Debug timestamps
        st.write(f"From timestamp: {from_timestamp} ({datetime.fromtimestamp(from_timestamp)})")
        st.write(f"To timestamp: {to_timestamp} ({datetime.fromtimestamp(to_timestamp)})")

        params = {
            'symbolName': ticker.replace('.BA', ''),
            'exchange': 'BCBA',
            'from': str(from_timestamp),
            'to': str(to_timestamp),
            'resolution': 'D',
        }

        response = requests.get(
            'https://iol.invertironline.com/api/cotizaciones/history',
            params=params,
            cookies=cookies,
            headers=headers,
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'ok' and 'bars' in data:
                df = pd.DataFrame(data['bars'])
                # Debug raw data
                st.write("Raw data from API:", df.tail())
                
                df['Date'] = pd.to_datetime(df['time'], unit='s').dt.date
                df = df.rename(columns={
                    'close': 'Close',
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'volume': 'Volume'
                })
                df = df.set_index('Date')
                
                # Debug processed data
                st.write("Processed data:", df.tail())
                
                return df[['Open', 'High', 'Low', 'Close', 'Volume']]
            else:
                st.warning(f"API Response: {data}")
        else:
            st.warning(f"API Status Code: {response.status_code}")
        
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching IOL data: {str(e)}")
        import traceback
        st.write("Error traceback:", traceback.format_exc())
        return pd.DataFrame()

# Streamlit app
st.title("Tabla Histórica de Variación de Acciones, índices, ETFs, etc.")

# Add data source selector
data_source = st.radio(
  "Fuente de datos:",
  ('YFinance', 'IOL (Invertir Online)')
)

# Input for stock ticker and date range
ticker = st.text_input("Ingrese el Ticker de la Acción (por ejemplo, AAPL, MSFT, TSLA):", value="AAPL").upper()

# Set the minimum date to January 1, 1980
start_date = st.date_input("Fecha de Inicio", value=pd.to_datetime("2023-01-01"), min_value=pd.to_datetime("1980-01-01"))

# Set the end date to "the day after today"
# Instead of adding one day to today, use end of current day
end_date = st.date_input("Fecha de Fin", value=datetime.today())

if st.button("Obtener Datos"):
  try:
      # Fetch data based on selected source
      if data_source == 'YFinance':
          stock_data = yf.download(ticker, start=start_date, end=end_date + timedelta(days=1))
      else:  # IOL
          stock_data = fetch_iol_data(ticker, start_date, end_date)
      if not stock_data.empty:
          # Ensure index is date type
          if isinstance(stock_data.index[0], datetime):
              stock_data.index = stock_data.index.date

          # Calculate Percentage Variation from the previous trading day
          stock_data['Variación %'] = stock_data['Close'].pct_change() * 100

          # Calculate the distance between maximum and minimum values that day (in percentage)
          stock_data['Distancia Máx-Mín (%)'] = ((stock_data['High'] - stock_data['Low']) / stock_data['Low']) * 100

          # Calculate the distance between open and closing values that day (in percentage)
          stock_data['Distancia Apertura-Cierre (%)'] = ((stock_data['Close'] - stock_data['Open']) / stock_data['Open']) * 100

          # Prepare data for display, round to two decimals
          display_data = stock_data[['Close', 'Volume', 'Variación %', 'Distancia Máx-Mín (%)', 'Distancia Apertura-Cierre (%)']].round(2)

          # Display the data in a Streamlit data table with a taller view
          st.dataframe(display_data, height=1200)
      else:
          st.error("No hay datos disponibles para el rango de fechas seleccionado.")
  except Exception as e:
      st.error(f"Error al procesar los datos: {str(e)}")
      import traceback
      st.write("Error completo:", traceback.format_exc())
