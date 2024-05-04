# Import packages
from prophet.plot import plot_plotly, plot_components_plotly
import os
import re
import requests
import pandas as pd
import plotly.graph_objs as go
import streamlit as st
from io import StringIO
from prophet import Prophet
from dateutil import parser
import matplotlib.pyplot as plt
import warnings
from datetime import datetime
from datetime import timedelta
warnings.filterwarnings("ignore")

###STEP ONE: DEFINE FUNCTIONS###

# Funciton: Analyze suspension rates
def suspension_count(data, facility, before):
    filtered_df = data[data['datetime_of_data'] >= before]
    filtered_df = filtered_df[filtered_df['title'] == facility]
    suspended = filtered_df[filtered_df['visiting_status'] == 'Suspended']
    not_suspended = filtered_df[filtered_df['visiting_status'] == 'Not Suspended']
    count = len(suspended)
    total = len(suspended) + len(not_suspended)
    return (count / total) * 100 if total > 0 else 0

# Function: Preprocess data for timeseries modeling (Prophet)

def prophet_preprocess_fac(df):
    df['datetime_of_data'] = df['datetime_of_data'].apply(
        lambda x: parser.parse(x))
    df['ds'] = pd.to_datetime(df['datetime_of_data'],
                              format='%Y-%m-%d %H:%M:%S %Z')
    df['ds'] = df['ds'].dt.tz_localize(None)
    df['y'] = df["population"]
    df.set_index('ds', inplace=True)

    daily_data = df.copy()
    daily_data = daily_data['y']
    # fill missing days with median rolling window = 5
    rolling_median = daily_data.rolling(
        window=5, min_periods=1, center=True).median()
    daily_data_filled = daily_data.fillna(rolling_median)
    # Remove timezone from the 'Datetime' index
    daily_data_filled.index = daily_data_filled.index.tz_localize(None)

    # Reset the index to make the Datetime a regular column
    df_reset = daily_data_filled.reset_index()
    # Isolate time and predictor columns
    df_reset = df_reset[['ds', 'y']]

    return df_reset

# Function: Preprocess prison names
def sanitize_name(name):
    """Sanitize names for consistent comparison."""
    # Convert to lower case, strip whitespace, and replace special characters if needed
    # Adjust this based on your specific needs
    sanitized = name.lower().strip().replace(' ', '_')
    return sanitized


###STEP TWO: DEFINE GUI INTERFACE TO MATCH THE LANDING PAGE###
def set_css():
    st.markdown("""
        <style>
        html, body, [class*="css"] {
            font-family: 'Open Sans', sans-serif;
            color: black;
            background-color: #c2d9ff;
            line-height: 1.5;
        }
        .stTextInput > div > div > input {
            background-color: #fff;
            color: black;
            border-radius: 0;
            border: 1px solid black;
        }
        .st-bb {
            background-color: #white;
        }
        .st-bj {
            color: white;
        }
        .stDownloadButton>button {
            background-color: #c2d9ff;
            color: black;
            font-family: 'Open Sans', sans-serif;
            border-radius: 0;
            border: 1px solid black;
        }
        .css-1d391kg {
            background-color: #c2d9ff;
            color: #c2d9ff;
        }
        .stSelectbox > div > div > div {
            background-color: #fff;
            color: black;
            border-radius: 0;
            border: 1px solid black;
        }
        .st-b7 {
            background-color: #fff;
            border-radius: 0;
            border: none;
        }
        .st-cx {
            border-radius: 0;
        }
        .st-dd {
            border-radius: 0;
        }
        .st-bw {
            border-radius: 0;
        }
        .st-bs {
            border-radius: 0;
        }
        .stButton > button {
            border-radius: 0;
            border: 1px solid #c2d9ff;
        }
        .st-dr {
            border: 1px solid #fff;
            border-radius: 0;
        }
        /* Fix for select dropdown arrow */
        .st-d2 {
            background-color: #fff !important;
        }
        .stDropdown > div > div > div {
            border: black !important;
        }
        /* Plotly chart styles */
        .js-plotly-plot .plotly {
            border-radius: 0 !important;
        }
        /* New styles for dropdown hover and date input */
        .stSelectbox > div > div > div:hover {
            background-color: #c2d9ff;  /* Hover background color for dropdown */
        }
        .stDateInput > div > div > div > input {
            border: 1px solid black;  /* Black border for date input */
            border-radius: 0;  /* Sharp corners for the date input */
            background-color: #white;  /* Ensure background color is white */
            color: black;  /* Text color black */
        }
        </style>
        """, unsafe_allow_html=True)

set_css()

# Top of application: Link back to landing page
st.markdown("[Back to Defense Data Center](https://defense-data-center.webflow.io)", unsafe_allow_html=True)

# Display title
st.title('Prison Operations Snapshot')

# Define data input
file_path = 'https://raw.githubusercontent.com/lksanterre/prison/main/data_update/master_dataframe_cleaned.csv'
total_content = requests.get(file_path).content
dataframe = pd.read_csv(StringIO(total_content.decode('utf-8')))

###STEP THREE: START BUILDING STREAMLIT APP##
###BEGIN BY DEFINING BUTTONS###

# Create Button 1: Complete DDC Dataset Download
response = requests.get(file_path)
if response.ok:
    csv_content = response.content
    btn = st.download_button(
        label="Download Complete DDC DataSet",
        data=csv_content,
        file_name="total_df.csv",
        mime="text/csv"
    )
else:
    st.error("Failed to download the dataset.")

# Create Button 2: Facility-Specific Dataset Download
user_input = st.text_input("Facility Specific Spreadsheet Generator - Enter Name of Facility:").upper()
sanitized_view_name = re.sub(r'\W+', '_', user_input)

if response.ok:
    # Filter the DataFrame based on user input
    csv_content = response.content
    total_df = pd.read_csv(StringIO(csv_content.decode('utf-8')))
    selected_data = total_df[total_df['title'] == user_input]

    if not selected_data.empty:
        btn_facility = st.download_button(
            label=f"Download {user_input} Data",
            data=selected_data.to_csv(index=False).encode(),
            file_name=f"{sanitized_view_name}_data.csv",
            mime="text/csv"
        )
    else:
        if user_input:  # Only show the warning if the user has actually input something
            st.warning(
                "The specified facility name does not exist in the dataset. Please try again.")
else:
    st.error("Failed to load the dataset.")

# Suspension Analysis Section
st.header('Operations Analysis')
facility_name = st.selectbox(
    'Choose a Facility for Analysis',
    dataframe['title'].unique(),  
    key='facility_name_for_analysis'
)
input_date = st.date_input(
    "My Client Has Been Incarcerated Since:",
    min_value=datetime(2023, 1, 1),  
    max_value=datetime.today(),
    key='analysis_date'
)
# Button 3: Suspension Analysis
if st.button('Analyze Suspension Rates'):
    # Convert the selected date to string and then to datetime to match DataFrame formatting
    input_date_str = input_date.strftime('%Y-%m-%d')
    suspension_percentage = suspension_count(dataframe, facility_name, input_date_str)
    st.write(f"Percentage of days with suspended visitation after {input_date_str}: {suspension_percentage:.2f}%")

### STEP FOUR: DISPLAY HISTORICAL DATA PLOT AND PREDICTIONS ###


if facility_name:
    try:
        # Load the data into a DataFrame
        data_df = dataframe[dataframe['title'] == facility_name]

        data_df['population'] = data_df['population'].astype(str)
        
        data_df['population'] = data_df['population'].str.replace(',', '')

        data_df['population'] = data_df['population'].astype(int)

        train = prophet_preprocess_fac(data_df)
        # Convert the 'datetime_of_data' column to datetime type for proper sorting
        if 'datetime_of_data' in data_df.columns and 'visiting_status' in data_df.columns:
            data_df['datetime_of_data'] = data_df['datetime_of_data'].astype(
                str).str[:-4]
            data_df['datetime_of_data'] = pd.to_datetime(
                data_df['datetime_of_data'])
            data_df = data_df.sort_values(by='datetime_of_data')

            # Plot with Plotly - creating a line chart for population
            fig = go.Figure()

            # Add line for population

            fig.add_trace(
                go.Scatter(
                    x=data_df['datetime_of_data'],
                    y=data_df['population'],
                    mode='lines',
                    name='Population',
                    line=dict(
                        color='#000552')))

            # Add markers for points where the status is 'Suspended'
            suspended_data = data_df[data_df['visiting_status'] == 'Suspended']
            fig.add_trace(
                go.Scatter(
                    x=suspended_data['datetime_of_data'],
                    y=suspended_data['population'],
                    mode='markers',
                    name='Visitation Suspended',
                    marker=dict(
                        color='#6e0004',
                        size=10)))

            # Update layout for better axis fit and to add title
            data_df['population'] = pd.to_numeric(data_df['population'], errors='coerce')
            population_min = data_df['population'].min()
            population_max = data_df['population'].max()
            padding = (population_max - population_min) * 0.1  # 10% padding
            fig.update_layout(
                title=f"Historical Population: {facility_name}",
                yaxis=dict(range=[population_min - padding,
                           population_max + padding]),
                transition_duration=500,
                xaxis_title='Past Date',
                yaxis_title = 'Population'
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Required columns not found in the data.")
        
        # Plot timeseries model

        m = Prophet()
        m.fit(train)
        future = m.make_future_dataframe(periods=8)
        forecast = m.predict(future).tail(7)
        # forecast_last_7_days = forecast.tail(7)
        ml_content = requests.get('https://raw.githubusercontent.com/lksanterre/prison/main/data_update/forecast.csv').content
        ml_pred = pd.read_csv(StringIO(ml_content.decode('utf-8')))
        # Filter predictions for the selected facility
        ml_pred_facility = ml_pred[ml_pred['title'] == facility_name]
        
        
        #st.dataframe(ml_pred_facility)  # This line displays the DataFrame in the Streamlit app

        # Adjusting the 'ds' column to show the day before
        forecast['ds'] = forecast['ds'] - timedelta(days=1)

        # Continue with your existing code, now using the adjusted 'ds' for plotting
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode='lines', name='Predicted',
                                line=dict(color='#001942')))
        fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat_lower'], mode='lines', name='Lower Bound',
                                fill=None, line=dict(color='lightblue')))
        fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat_upper'], mode='lines', name='Upper Bound',
                                fill='tonexty', line=dict(color='lightblue')))

        # Reset the index after adjusting the dates
        ml_pred_facility_reset = ml_pred_facility.reset_index()
        forecast_reset = forecast.reset_index()

        marker_hover_text = [f"Predicted Population: {yhat:.0f}, Lockdown Probability: {lockdown_prob * 100:.0f}%" 
                            for yhat, lockdown_prob in zip(forecast_reset['yhat'], ml_pred_facility_reset['lockdown_probability'])]

        fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode='markers', name='Lockdown Probability',
                                text=marker_hover_text, hoverinfo='text', 
                                marker=dict(color='#6b0207', size=10)))

        # Update layout as per the original settings
        fig.update_layout(title='Next 7 Days Predictions',
                        xaxis_title='Date', yaxis_title='Population Prediction',
                        showlegend=True)

        st.plotly_chart(fig, use_container_width=True)

        

    except FileNotFoundError:
        st.error(f"Data file for {facility_name} not found.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

### STEP FIVE: Display BOP Facilities on Interactive Map ###
new_df = pd.read_csv(
    'https://raw.githubusercontent.com/lksanterre/prison/main/facilities/location_data.csv')

fig = go.Figure()

selected_facility = sanitize_name(facility_name)
for index, row in new_df.iterrows():
    # Sanitize the name from the DataFrame for comparison
    sanitized_name = sanitize_name(row['name'])

    color = 'red' if sanitized_name == selected_facility else '#001942'
    fig.add_trace(go.Scattermapbox(
        lon=[row['long']],
        lat=[row['lat']],
        mode='markers+text',  # For adding text labels beside markers
        marker=go.scattermapbox.Marker(
            size=9,
            color=color,
            opacity=1 if color == '#001942' else 0.9
        ),
        text=row['name'],  # Original name for display
        hoverinfo='text+name',
        # hovertext="<b style='color:white;'>" + row['name'] + "</b>",  #
        # Attempt to make hover text white
        name=row['name']
    ))
mapbox_access_token = 'pk.eyJ1IjoibGtzYW50ZXJyZSIsImEiOiJjbHMwdWZwaGswNHZwMmtucTZvdXQ0dmQ4In0.atoTB2hBdxOrfAszlnLEfg'

# Set mapbox and layout attributes
fig.update_layout(
    mapbox=dict(
        accesstoken=mapbox_access_token,
        zoom=3,
        center=dict(lat=37.0902, lon=-95.7129),
        style='streets'
    ),
    showlegend=False,
    title='Interactive Map of Locations',
    hoverlabel=dict(
        bgcolor="black",  # Background color for hover
        font_color="white",  # Font color for hover text
        font_size=12,
        font_family="Arial"
    )
)

new_df = pd.read_csv(
    'https://raw.githubusercontent.com/lksanterre/prison/main/facilities/location_data.csv')

fig = go.Figure()

selected_facility = sanitize_name(facility_name)
for index, row in new_df.iterrows():
    # Sanitize the name from the DataFrame for comparison
    sanitized_name = sanitize_name(row['name'])

    color = '#6b0207' if sanitized_name == selected_facility else '#001942'
    fig.add_trace(go.Scattermapbox(
        lon=[row['long']],
        lat=[row['lat']],
        mode='markers+text',  # For adding text labels beside markers
        marker=go.scattermapbox.Marker(
            size=9,
            color=color,
            opacity=1 if color == '#001942' else 0.9
        ),
        text=row['name'],  # Original name for display
        hoverinfo='text+name',
        # hovertext="<b style='color:white;'>" + row['name'] + "</b>",  #
        # Attempt to make hover text white
        name=row['name']
    ))
mapbox_access_token = 'pk.eyJ1IjoibGtzYW50ZXJyZSIsImEiOiJjbHMwdWZwaGswNHZwMmtucTZvdXQ0dmQ4In0.atoTB2hBdxOrfAszlnLEfg'

# Set mapbox and layout attributes
fig.update_layout(
    mapbox=dict(
        accesstoken=mapbox_access_token,
        zoom=3,
        center=dict(lat=37.0902, lon=-95.7129),
        style='streets'
    ),
    showlegend=False,
    title='Interactive Map of Locations',
    hoverlabel=dict(
        bgcolor="black",  # Background color for hover
        font_color="white",  # Font color for hover text
        font_size=12,
        font_family="Arial"
    )
)

# Streamlit: Display the Plotly figure
st.plotly_chart(fig, use_container_width=True)
