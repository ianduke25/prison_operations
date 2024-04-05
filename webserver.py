import os
import re
import requests
import pandas as pd
import plotly.graph_objs as go
import streamlit as st


st.title('US Prison Population and Visitation')
st.write('Nick Miller | Ian Duke | Tianyunxi (Emily) Yin | Caleb Hamblen | Lance Santerre')

file_path = 'https://raw.githubusercontent.com/lksanterre/prison/main/clean_data/total_df.csv'

users = {
    "lance": "lance",
    "user2": "password2",
}

if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False


def login(user, password):
    if user in users and users[user] == password:
        st.session_state['authenticated'] = True
        st.success("Logged in successfully!")
    else:
        st.error("Incorrect username or password")


if not st.session_state['authenticated']:
    st.title("Login Page")
    user = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        login(user, password)

if st.session_state['authenticated']:
    st.title("Secure Data Page")
    st.write("Welcome! You can now download the data.")
    
    response = requests.get(file_path)
    if response.ok:
        csv_content = response.content
        st.download_button("Download Full DataSet", csv_content, "total_df.csv", "text/csv")
    else:
        st.error("Failed to download the dataset.")
    
    file_path_small = 'https://raw.githubusercontent.com/lksanterre/prison/main/clean_data/'
    user_input = st.text_input("Enter Name of Facility").upper()
    sanitized_view_name = re.sub(r'\W+', '_', user_input)
    complete_file_path = f"{file_path_small}{sanitized_view_name}_df.csv"

    response = requests.get(complete_file_path)
    if response.ok:
        csv_content = response.content
        st.download_button(f"Download {user_input} DataSet", csv_content, f"{sanitized_view_name}.csv", "text/csv")
    else:
        if user_input:
            st.warning("The specified facility name does not exist or there was an error fetching the dataset. Please try again.")

options = ['FMC_FORT_WORTH','FCI_BECKLEY','USP_YAZOO_CITY','FCI_BIG_SPRING','FCI_HAZELTON','FMC_DEVENS','FCI_SANDSTONE','FCI_PEKIN','FCI_YAZOO_CITY_LOW',
 'FCI_YAZOO_CITY_MEDIUM','USP_COLEMAN_I','FCI_SAFFORD','FCI_MCKEAN','MCC_NEW_YORK','FCI_TERRE_HAUTE','FCI_THREE_RIVERS','USP_BEAUMONT','FCI_OAKDALE_II',
 'USP_BIG_SANDY','FCI_BUTNER_LOW','FCI_DUBLIN','FCI_OXFORD','FCI_BEAUMONT_LOW','USP_ATWATER','MCC_SAN_DIEGO','FCI_VICTORVILLE_MEDIUM_II','FCI_TALLAHASSEE',
 'FCI_ALLENWOOD_LOW','FCI_DANBURY','FCI_LOMPOC','FDC_SEATAC','USP_LEAVENWORTH','MDC_GUAYNABO','FCI_GILMER','USP_HAZELTON','FCI_MANCHESTER','FCI_OTISVILLE',
 'FCI_PETERSBURG_LOW','FPC_DULUTH','FCI_PETERSBURG_MEDIUM','FCI_MORGANTOWN','FPC_PENSACOLA','FCI_SEAGOVILLE','FCI_ALICEVILLE','FCI_PHOENIX','FCI_ENGLEWOOD',
'FCI_FORREST_CITY_MEDIUM','FCI_MENDOTA','FCI_BUTNER_MEDIUM_II','FCI_BUTNER_MEDIUM_I','FCI_BEAUMONT_MEDIUM','MCC_CHICAGO','FCI_COLEMAN_LOW','FCI_LA_TUNA',
 'USP_COLEMAN_II','FCI_TALLADEGA','FCI_SCHUYLKILL','USP_LOMPOC','FCI_THOMSON','FCI_BERLIN','FCI_POLLOCK','FCI_WASECA','USP_LEE','FMC_ROCHESTER','FCI_BASTROP',
 'USP_MARION','FPC_MONTGOMERY','MDC_LOS_ANGELES','FCI_OAKDALE_I','FCI_ASHLAND','FCI_FORREST_CITY_LOW','MCFP_SPRINGFIELD','FCI_ALLENWOOD_MEDIUM','USP_TERRE_HAUTE',
 'FCI_JESUP','FCI_MARIANNA','FCI_ESTILL','USP_MCCREARY','FCI_BENNETTSVILLE','FCI_MCDOWELL','FCI_VICTORVILLE_MEDIUM_I','FCI_FLORENCE','FCI_ELKTON','FCI_FORT_DIX',
 'FCI_TERMINAL_ISLAND','FCI_WILLIAMSBURG','FCI_EDGEFIELD','FCI_TUCSON','FTC_OKLAHOMA_CITY','FMC_LEXINGTON','FCI_MIAMI','USP_LEWISBURG','FCI_EL_RENO','FMC_BUTNER',
'USP_VICTORVILLE','FCI_SHERIDAN','FCI_FAIRTON','FCI_GREENVILLE','FPC_YANKTON','FCI_MEMPHIS','FCI_HERLONG','FPC_ALDERSON','FDC_HOUSTON','FMC_CARSWELL','FCI_CUMBERLAND',
'USP_FLORENCE_HIGH','FDC_PHILADELPHIA','USP_TUCSON','FCI_MILAN','FCI_TEXARKANA','FCI_COLEMAN_MEDIUM','USP_ALLENWOOD','MDC_BROOKLYN','USP_FLORENCE_ADMAX','FPC_BRYAN',
 'USP_POLLOCK','USP_CANAAN','USP_THOMSON','FDC_HONOLULU','USP_ATLANTA','FDC_MIAMI','FCI_RAY_BROOK','FCI_LORETTO']

facility_name = st.selectbox("Choose a Facility", options, index=0, placeholder="Choose an option")

if facility_name:
    sanitized_facility_name = re.sub(r'\W+', '_', facility_name).upper()
    complete_file_path = f"{file_path_small}{sanitized_facility_name}_df.csv"

    try:
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
    except FileNotFoundError:
        st.error(f"Data

