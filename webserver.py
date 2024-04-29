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
warnings.filterwarnings("ignore")


st.title('US Prison Population and Visitation')
st.write('Nick Miller | Ian Duke | Tianyunxi (Emily) Yin | Caleb Hamblen | Lance Santerre')
file_path = 'https://raw.githubusercontent.com/lksanterre/prison/main/clean_data/master_dataframe_cleaned.csv'
total_content = requests.get(file_path).content
dataframe = pd.read_csv(StringIO(total_content.decode('utf-8')))

users = {
    "lance": "lance",
    "user2": "password2",
}

# Initialize session state for user authentication
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

# Function to verify login credentials


def login(user, password):
    if user in users and users[user] == password:
        st.session_state['authenticated'] = True
        st.success("Logged in successfully!")
    else:
        st.error("Incorrect username or password")


# Login form for unauthenticated users
if not st.session_state['authenticated']:
    st.title("Login Page")
    user = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        login(user, password)

# Content for authenticated users
if st.session_state['authenticated']:
    st.title("Secure Data Page")
    st.write("Welcome! You can now download the data.")

    response = requests.get(file_path)
    if response.ok:
        csv_content = response.content
        btn = st.download_button(
            label="Download Full DataSet",
            data=csv_content,
            file_name="total_df.csv",
            mime="text/csv"
        )
    else:
        st.error("Failed to download the dataset.")

    # file_path_small = 'https://raw.githubusercontent.com/lksanterre/prison/main/clean_data/'
    user_input = st.text_input("Enter Name of Facility").upper()
    sanitized_view_name = re.sub(r'\W+', '_', user_input)

    # Try to fetch the file to see if it exists
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

# Visualization accessible to all users
# options = ['FMC_FORT_WORTH','FCI_BECKLEY','USP_YAZOO_CITY','FCI_BIG_SPRING','FCI_HAZELTON','FMC_DEVENS','FCI_SANDSTONE','FCI_PEKIN','FCI_YAZOO_CITY_LOW',
#  'FCI_YAZOO_CITY_MEDIUM','USP_COLEMAN_I','FCI_SAFFORD','FCI_MCKEAN','MCC_NEW_YORK','FCI_TERRE_HAUTE','FCI_THREE_RIVERS','USP_BEAUMONT','FCI_OAKDALE_II',
#  'USP_BIG_SANDY','FCI_BUTNER_LOW','FCI_DUBLIN','FCI_OXFORD','FCI_BEAUMONT_LOW','USP_ATWATER','MCC_SAN_DIEGO','FCI_VICTORVILLE_MEDIUM_II','FCI_TALLAHASSEE',
#  'FCI_ALLENWOOD_LOW','FCI_DANBURY','FCI_LOMPOC','FDC_SEATAC','USP_LEAVENWORTH','MDC_GUAYNABO','FCI_GILMER','USP_HAZELTON','FCI_MANCHESTER','FCI_OTISVILLE',
#  'FCI_PETERSBURG_LOW','FPC_DULUTH','FCI_PETERSBURG_MEDIUM','FCI_MORGANTOWN','FPC_PENSACOLA','FCI_SEAGOVILLE','FCI_ALICEVILLE','FCI_PHOENIX','FCI_ENGLEWOOD',
# 'FCI_FORREST_CITY_MEDIUM','FCI_MENDOTA','FCI_BUTNER_MEDIUM_II','FCI_BUTNER_MEDIUM_I','FCI_BEAUMONT_MEDIUM','MCC_CHICAGO','FCI_COLEMAN_LOW','FCI_LA_TUNA',
#  'USP_COLEMAN_II','FCI_TALLADEGA','FCI_SCHUYLKILL','USP_LOMPOC','FCI_THOMSON','FCI_BERLIN','FCI_POLLOCK','FCI_WASECA','USP_LEE','FMC_ROCHESTER','FCI_BASTROP',
#  'USP_MARION','FPC_MONTGOMERY','MDC_LOS_ANGELES','FCI_OAKDALE_I','FCI_ASHLAND','FCI_FORREST_CITY_LOW','MCFP_SPRINGFIELD','FCI_ALLENWOOD_MEDIUM','USP_TERRE_HAUTE',
#  'FCI_JESUP','FCI_MARIANNA','FCI_ESTILL','USP_MCCREARY','FCI_BENNETTSVILLE','FCI_MCDOWELL','FCI_VICTORVILLE_MEDIUM_I','FCI_FLORENCE','FCI_ELKTON','FCI_FORT_DIX',
#  'FCI_TERMINAL_ISLAND','FCI_WILLIAMSBURG','FCI_EDGEFIELD','FCI_TUCSON','FTC_OKLAHOMA_CITY','FMC_LEXINGTON','FCI_MIAMI','USP_LEWISBURG','FCI_EL_RENO','FMC_BUTNER',
# 'USP_VICTORVILLE','FCI_SHERIDAN','FCI_FAIRTON','FCI_GREENVILLE','FPC_YANKTON','FCI_MEMPHIS','FCI_HERLONG','FPC_ALDERSON','FDC_HOUSTON','FMC_CARSWELL','FCI_CUMBERLAND',
# 'USP_FLORENCE_HIGH','FDC_PHILADELPHIA','USP_TUCSON','FCI_MILAN','FCI_TEXARKANA','FCI_COLEMAN_MEDIUM','USP_ALLENWOOD','MDC_BROOKLYN','USP_FLORENCE_ADMAX','FPC_BRYAN',
#  'USP_POLLOCK','USP_CANAAN','USP_THOMSON','FDC_HONOLULU','USP_ATLANTA','FDC_MIAMI','FCI_RAY_BROOK','FCI_LORETTO']


facility_name = st.selectbox(
    'Select Facility',
    dataframe['title'].unique(),
    placeholder="Choose an option")


# facility_name = st.selectbox("Choose a Facility", options, index=0, placeholder="Choose an option")


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

# ml_content = requests.get('https://raw.githubusercontent.com/lksanterre/prison/main/forecast/forecast_test.csv').content
# ml_df = pd.read_csv(StringIO(ml_content.decode('utf-8')))


if facility_name:

    try:
        # Loading the data into a DataFrame
        data_df = dataframe[dataframe['title'] == facility_name]
        # ml_pred = ml_df[ml_df['title'] == facility_name]
        train = prophet_preprocess_fac(data_df)
        # Convert the 'datetime_of_data' column to datetime type for proper
        # sorting
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
                        color='blue')))

            # Add markers for points where the status is 'Suspended'
            suspended_data = data_df[data_df['visiting_status'] == 'Suspended']
            fig.add_trace(
                go.Scatter(
                    x=suspended_data['datetime_of_data'],
                    y=suspended_data['population'],
                    mode='markers',
                    name='Suspended',
                    marker=dict(
                        color='red',
                        size=10)))

            # Update layout for better axis fit and to add title
            population_min = data_df['population'].min()
            population_max = data_df['population'].max()
            padding = (population_max - population_min) * 0.1  # 10% padding
            fig.update_layout(
                title=f"Data Visualization for: {facility_name}",
                yaxis=dict(range=[population_min - padding,
                           population_max + padding]),
                transition_duration=500
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Required columns not found in the data.")

        # time-series model

        m = Prophet()
        m.fit(train)
        future = m.make_future_dataframe(periods=7)
        forecast = m.predict(future).tail(7)
        # forecast_last_7_days = forecast.tail(7)
        ml_content = requests.get(
            'https://raw.githubusercontent.com/lksanterre/prison/main/data_update/forecast.csv').content
        ml_pred = pd.read_csv(StringIO(ml_content.decode('utf-8')))

        # Create a Plotly figure
        fig = go.Figure()
        # Add the predicted values and confidence intervals to the figure
        fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode='lines', name='Predicted',
                                line=dict(color='blue')))
        fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat_lower'], mode='lines', name='Lower Bound',
                                fill=None, line=dict(color='lightblue')))
        fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat_upper'], mode='lines', name='Upper Bound',
                                fill='tonexty', line=dict(color='lightblue')))
        marker_hover_text = [f"Population: {yhat:.0f}, Lockdown Probability: {lockdown_prob:.2f}" 
                               for yhat, lockdown_prob in zip(forecast['yhat'], ml_pred['lockdown_probability'])]
        fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode='markers', name='Lockdown Probability',
                                   text=marker_hover_text, hoverinfo='text', 
                               marker=dict(color='red', size=10)))
        
        # Set x-axis range to focus on the last 7 days
        fig.update_xaxes(tick0=None) # Start ticks from the first data point)
        # Update layout
        fig.update_layout(title='Next 7 Days Predictions',
                        xaxis_title='Date', yaxis_title='Population Prediction',
                        showlegend=True)
    
        st.plotly_chart(fig, use_container_width=True)

    
        #aggregated stats plot added below
        
        avg_population_by_prison = dataframe.groupby('title')['population'].mean().reset_index()
        recent_index = dataframe.groupby('title')['datetime_of_data'].idxmax()
        most_recent_data = dataframe.loc[recent_index]
        merged_df = avg_population_by_prison.join(most_recent_data.set_index('title'), on='title', rsuffix='_recent')
        merged_df = merged_df.rename(columns={'population': 'avg_population'})
        # Load the CSV file containing the average population and current population data
        
        # Extract relevant columns and filter data based on the selected facility
        avg_pop_filtered = merged_df[['title', 'avg_population', 'population_recent']]
        avg_pop_filtered = avg_pop_filtered[avg_pop_filtered['title'] == facility_name]
        
        # Check if data is available for the selected facility
        if not avg_pop_filtered.empty:
            # Create a bar plot for average population and current population
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(x=['Average Population', 'Current Population'],
                                     y=[avg_pop_filtered['avg_population'].iloc[0], avg_pop_filtered['population_recent'].iloc[0]],
                                     marker_color=['blue', 'lightblue'],
                                     text=[f"Average: {avg_pop_filtered['avg_population'].iloc[0]}",
                                           f"Current: {avg_pop_filtered['population_recent'].iloc[0]}"],
                                     textposition='auto'
                                     ))
            fig_bar.update_layout(title=f"Average and Current Population for {facility_name}",
                                  xaxis_title='Population Type',
                                  yaxis_title='Population',
                                  showlegend=False)
            
            st.plotly_chart(fig_bar, use_container_width=True)

    except FileNotFoundError:
        st.error(f"Data file for {facility_name} not found.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")


def sanitize_name(name):
    """Sanitize names for consistent comparison."""
    # Convert to lower case, strip whitespace, and replace special characters if needed
    # Adjust this based on your specific needs
    sanitized = name.lower().strip().replace(' ', '_')
    return sanitized


new_df = pd.read_csv(
    'https://raw.githubusercontent.com/lksanterre/prison/main/facilities/location_data.csv')

fig = go.Figure()

selected_facility = sanitize_name(facility_name)
for index, row in new_df.iterrows():
    # Sanitize the name from the DataFrame for comparison
    sanitized_name = sanitize_name(row['name'])

    color = 'red' if sanitized_name == selected_facility else 'blue'
    fig.add_trace(go.Scattermapbox(
        lon=[row['long']],
        lat=[row['lat']],
        mode='markers+text',  # For adding text labels beside markers
        marker=go.scattermapbox.Marker(
            size=9,
            color=color,
            opacity=1 if color == 'blue' else 0.9
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
