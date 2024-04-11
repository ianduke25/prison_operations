import streamlit as st
import re
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go


st.title('US Prison Population and Visitation')
st.write('Nick Miller | Ian Duke | Tianyunxi (Emily) Yin | Caleb Hamblen | Lance Santerre')
file_path = 'https://raw.githubusercontent.com/lksanterre/prison/main/clean_data/total_df.csv'
# Simulate a simple user database
users = {
    "usfca": "dons",
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
    

    with open(file_path, "rb") as file:
        btn = st.download_button(
                label="Download Full DataSet",
                data=file,
                file_name="total_df.csv",
                mime="text/csv"
            )
    

    file_path_small = 'https://raw.githubusercontent.com/lksanterre/prison/main/clean_data//'
    user_input = st.text_input("Enter Name of Facility").upper()
    sanitized_view_name = re.sub(r'\W+', '_', user_input)
    complete_file_path = os.path.join(file_path_small, sanitized_view_name + "_df.csv")
    if os.path.exists(complete_file_path):
        try:
            with open(complete_file_path, "rb") as file:
                btn = st.download_button(
                    label=f"Download {user_input} DataSet",
                    data=file,
                    file_name=f"{sanitized_view_name}.csv",
                    mime="text/csv"
                )
        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        if user_input:  # If user_input is not empty
            st.warning("The specified facility name does not exist. Please try again.")

# Visualization accessible to all users
options = [f.replace('_df.csv', '') for f in os.listdir('https://raw.githubusercontent.com/lksanterre/prison/main/clean_data/') if f.endswith('_df.csv')]


facility_name = st.selectbox("Choose a Facility", options, index=0, placeholder="Choose an option")




if facility_name:
    # Normalize facility name to match file naming convention
    sanitized_facility_name = re.sub(r'\W+', '_', facility_name).upper()
    #complete_file_path = os.path.join('/Users/lancesanterre/prison_proj/prison/clean_data/', sanitized_facility_name + "_df.csv")
    complete_file_path = f'https://raw.githubusercontent.com/lksanterre/prison/main/clean_data/{sanitized_view_name}_df.csv'
    try:
        # Loading the data into a DataFrame
        data_df = pd.read_csv(complete_file_path)

        # Convert the 'datetime_of_data' column to datetime type for proper sorting
        if 'datetime_of_data' in data_df.columns and 'visiting_status' in data_df.columns:
            data_df['datetime_of_data'] = pd.to_datetime(data_df['datetime_of_data'])
            data_df.sort_values(by='datetime_of_data', inplace=True)

            # Plot with Plotly - creating a line chart for population
            fig = go.Figure()

            # Add line for population
            fig.add_trace(go.Scatter(x=data_df['datetime_of_data'], y=data_df['population'],
                                    mode='lines', name='Population',
                                    line=dict(color='blue')))

            # Add markers for points where the status is 'Suspended'
            suspended_data = data_df[data_df['visiting_status'] == 'Suspended']
            fig.add_trace(go.Scatter(x=suspended_data['datetime_of_data'], y=suspended_data['population'],
                                    mode='markers', name='Suspended',
                                    marker=dict(color='red', size=10)))

            # Update layout for better axis fit and to add title
            population_min = data_df['population'].min()
            population_max = data_df['population'].max()
            padding = (population_max - population_min) * 0.1  # 10% padding
            fig.update_layout(
                title=f"Data Visualization for: {facility_name}",
                yaxis=dict(range=[population_min - padding, population_max + padding]),
                transition_duration=500
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Required columns not found in the data.")
    except FileNotFoundError:
        st.error(f"Data file for {facility_name} not found.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

def sanitize_name(name):
    """Sanitize names for consistent comparison."""
    # Convert to lower case, strip whitespace, and replace special characters if needed
    sanitized = name.lower().strip().replace(' ', '_')  # Adjust this based on your specific needs
    return sanitized
new_df =  pd.read_csv('https://raw.githubusercontent.com/lksanterre/prison/main/facilities/facilities.csv')

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
        #hovertext="<b style='color:white;'>" + row['name'] + "</b>",  # Attempt to make hover text white
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
