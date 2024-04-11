import plotly.graph_objs as go
import streamlit as st


st.title('US Prison Population and Visitation')
st.write('Nick Miller | Ian Duke | Tianyunxi (Emily) Yin | Caleb Hamblen | Lance Santerre')

file_path = 'https://raw.githubusercontent.com/lksanterre/prison/main/clean_data/total_df.csv'


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
        st.download_button("Download Full DataSet", csv_content, "total_df.csv", "text/csv")
        btn = st.download_button(
            label="Download Full DataSet",
            data=csv_content,
            file_name="total_df.csv",
            mime="text/csv"
        )
    else:
        st.error("Failed to download the dataset.")



    file_path_small = 'https://raw.githubusercontent.com/lksanterre/prison/main/clean_data/'
    user_input = st.text_input("Enter Name of Facility").upper()
    sanitized_view_name = re.sub(r'\W+', '_', user_input)
    complete_file_path = f"{file_path_small}{sanitized_view_name}_df.csv"


    # Try to fetch the file to see if it exists
    response = requests.get(complete_file_path)
    if response.ok:
        # If the request was successful, enable downloading
        csv_content = response.content
        st.download_button(f"Download {user_input} DataSet", csv_content, f"{sanitized_view_name}.csv", "text/csv")
        btn = st.download_button(
            label=f"Download {user_input} DataSet",
            data=csv_content,
            file_name=f"{sanitized_view_name}.csv",
            mime="text/csv"
        )
    else:
        if user_input:
        # If the request failed, show an appropriate message
        if user_input:  # Only show the warning if the user has actually input something
            st.warning("The specified facility name does not exist or there was an error fetching the dataset. Please try again.")


# Visualization accessible to all users
options = ['FMC_FORT_WORTH','FCI_BECKLEY','USP_YAZOO_CITY','FCI_BIG_SPRING','FCI_HAZELTON','FMC_DEVENS','FCI_SANDSTONE','FCI_PEKIN','FCI_YAZOO_CITY_LOW',
 'FCI_YAZOO_CITY_MEDIUM','USP_COLEMAN_I','FCI_SAFFORD','FCI_MCKEAN','MCC_NEW_YORK','FCI_TERRE_HAUTE','FCI_THREE_RIVERS','USP_BEAUMONT','FCI_OAKDALE_II',
 'USP_BIG_SANDY','FCI_BUTNER_LOW','FCI_DUBLIN','FCI_OXFORD','FCI_BEAUMONT_LOW','USP_ATWATER','MCC_SAN_DIEGO','FCI_VICTORVILLE_MEDIUM_II','FCI_TALLAHASSEE',
@@ -73,29 +92,54 @@ def login(user, password):
'USP_FLORENCE_HIGH','FDC_PHILADELPHIA','USP_TUCSON','FCI_MILAN','FCI_TEXARKANA','FCI_COLEMAN_MEDIUM','USP_ALLENWOOD','MDC_BROOKLYN','USP_FLORENCE_ADMAX','FPC_BRYAN',
 'USP_POLLOCK','USP_CANAAN','USP_THOMSON','FDC_HONOLULU','USP_ATLANTA','FDC_MIAMI','FCI_RAY_BROOK','FCI_LORETTO']


facility_name = st.selectbox("Choose a Facility", options, index=0, placeholder="Choose an option")




if facility_name:
    # Normalize facility name to match file naming convention
    sanitized_facility_name = re.sub(r'\W+', '_', facility_name).upper()
    complete_file_path = f"{file_path_small}{sanitized_facility_name}_df.csv"
    complete_file_path = f'https://raw.githubusercontent.com/lksanterre/prison/main/clean_data/{sanitized_facility_name}_df.csv'

    try:
        # Loading the data into a DataFrame
        data_df = pd.read_csv(complete_file_path)
        data_df['datetime_of_data'] = data_df['datetime_of_data'].str[:-4]
        data_df['datetime_of_data'] = pd.to_datetime(data_df['datetime_of_data'])

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data_df['datetime_of_data'], y=data_df['population'],
                                 mode='lines', name='Population', line=dict(color='blue')))
        suspended_data = data_df[data_df['visiting_status'] == 'Suspended']
        fig.add_trace(go.Scatter(x=suspended_data['datetime_of_data'], y=suspended_data['population'],
                                 mode='markers', name='Suspended', marker=dict(color='red', size=10)))
        fig.update_layout(title=f"Data Visualization for: {facility_name}",
                          yaxis=dict(range=[data_df['population'].min() * 0.9, data_df['population'].max() * 1.1]),
                          transition_duration=500)
        st.plotly_chart(fig, use_container_width=True)

        # Convert the 'datetime_of_data' column to datetime type for proper sorting
        if 'datetime_of_data' in data_df.columns and 'visiting_status' in data_df.columns:
            data_df['datetime_of_data'] = data_df['datetime_of_data'].str[:-4]
            data_df['datetime_of_data'] = pd.to_datetime(data_df['datetime_of_data'])

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
