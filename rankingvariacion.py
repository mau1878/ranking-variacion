import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import requests
import plotly.express as px

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

        from_timestamp = int(datetime.combine(start_date, datetime.min.time()).timestamp())
        to_timestamp = int(datetime.combine(end_date, datetime.max.time()).timestamp())

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
                df['Date'] = pd.to_datetime(df['time'], unit='s').dt.date
                df = df.rename(columns={
                    'close': 'Close',
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'volume': 'Volume'
                })
                df = df.set_index('Date')
                return df[['Open', 'High', 'Low', 'Close', 'Volume']]
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching IOL data: {str(e)}")
        return pd.DataFrame()

# Function to standardize and flatten column names
def standardize_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]
    
    column_mapping = {
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume',
        'OPEN': 'Open',
        'HIGH': 'High',
        'LOW': 'Low',
        'CLOSE': 'Close',
        'VOLUME': 'Volume',
        'Adj Close': 'Close'
    }
    df = df.rename(columns=column_mapping)
    available_columns = [col for col in ['Open', 'High', 'Low', 'Close', 'Volume'] if col in df.columns]
    return df[available_columns]

# Function to resample data based on selected period
def resample_data(df, period):
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    
    st.write(f"Columns before resampling: {df.columns.tolist()}")
    
    agg_dict = {}
    if 'Open' in df.columns:
        agg_dict['Open'] = 'first'
    if 'High' in df.columns:
        agg_dict['High'] = 'max'
    if 'Low' in df.columns:
        agg_dict['Low'] = 'min'
    if 'Close' in df.columns:
        agg_dict['Close'] = 'last'
    if 'Volume' in df.columns:
        agg_dict['Volume'] = 'sum'

    if period == 'Daily':
        return df
    elif period == 'Weekly':
        return df.resample('W-MON').agg(agg_dict)
    elif period == 'Monthly':
        return df.resample('M').agg(agg_dict)

# Streamlit app
st.title("Tabla Histórica de Variación de Acciones, índices, ETFs, etc.")

# Add data source selector
data_source = st.radio(
    "Fuente de datos:",
    ('YFinance', 'IOL (Invertir Online)')
)

# Input for stock ticker and date range
ticker = st.text_input("Ingrese el Ticker de la Acción (por ejemplo, AAPL, MSFT, TSLA, ^SPX):", value="AAPL").upper()
start_date = st.date_input("Fecha de Inicio", value=pd.to_datetime("2023-01-01"), min_value=pd.to_datetime("1920-01-01"))
end_date = st.date_input("Fecha de Fin", value=datetime.today())

# Add period selector
period = st.selectbox(
    "Período de compresión:",
    ('Daily', 'Weekly', 'Monthly')
)

if st.button("Obtener Datos"):
    try:
        # Fetch data based on selected source
        if data_source == 'YFinance':
            stock_data = yf.download(ticker, start=start_date, end=end_date + timedelta(days=1))
        else:  # IOL
            stock_data = fetch_iol_data(ticker, start_date, end_date)
        
        if not stock_data.empty:
            # Standardize and flatten column names
            stock_data = standardize_columns(stock_data)
            
            # Debug initial columns
            st.write(f"Initial columns after standardization: {stock_data.columns.tolist()}")
            
            # Ensure index is date type and convert to DatetimeIndex
            if isinstance(stock_data.index[0], datetime):
                stock_data.index = pd.to_datetime(stock_data.index.date)
            
            # Resample data based on selected period
            stock_data = resample_data(stock_data, period)

            # Calculate metrics only for available columns
            if 'Close' in stock_data.columns:
                stock_data['Variación %'] = stock_data['Close'].pct_change() * 100
            
            if all(col in stock_data.columns for col in ['High', 'Low']):
                stock_data['Distancia Máx-Mín (%)'] = ((stock_data['High'] - stock_data['Low']) / stock_data['Low']) * 100
            
            if all(col in stock_data.columns for col in ['Close', 'Open']):
                stock_data['Distancia Apertura-Cierre (%)'] = ((stock_data['Close'] - stock_data['Open']) / stock_data['Open']) * 100

            # Prepare data for display, round to two decimals
            display_columns = [col for col in ['Close', 'Volume', 'Variación %', 'Distancia Máx-Mín (%)', 'Distancia Apertura-Cierre (%)'] 
                             if col in stock_data.columns]
            display_data = stock_data[display_columns].round(2)

            # Display the data in a Streamlit data table with a taller view
            st.dataframe(display_data, height=1200)

            # Add scatter plot for top 50 days by min-max spread
            if 'Distancia Máx-Mín (%)' in stock_data.columns:
                # Prepare data for scatter plot
                plot_data = stock_data[['Distancia Máx-Mín (%)']].copy()
                plot_data['Date'] = plot_data.index
                plot_data['Year'] = plot_data['Date'].dt.year
                
                # Get top 50 days by min-max spread
                top_50 = plot_data.nlargest(50, 'Distancia Máx-Mín (%)')
                
                # Create scatter plot
                fig = px.scatter(
                    top_50,
                    x='Date',
                    y='Distancia Máx-Mín (%)',
                    color='Year',
                    title=f'Top 50 Days by Min-Max Spread for {ticker}',
                    labels={'Distancia Máx-Mín (%)': 'Daily Min-Max Spread (%)'},
                    hover_data={'Date': '|%Y-%m-%d'}
                )
                
                # Update layout
                fig.update_layout(
                    showlegend=True,
                    height=600,
                    width=1000
                )
                
                # Display the plot
                st.plotly_chart(fig)

        else:
            st.error("No hay datos disponibles para el rango de fechas seleccionado.")
    except Exception as e:
        st.error(f"Error al procesar los datos: {str(e)}")
        import traceback
        st.write("Error completo:", traceback.format_exc())
