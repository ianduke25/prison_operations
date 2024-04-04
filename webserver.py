import streamlit as st
import requests
import re

st.title('US Prison Population and Visitation')
# Team members names listed
st.write('Nick Miller | Ian Duke | Tianyunxi (Emily) Yin | Caleb Hamblen | Lance Santerre')

# Corrected file path to the raw content on GitHub
file_path = 'https://raw.githubusercontent.com/lksanterre/prison/main/clean_data/total_df.csv'

# Download full dataset button
try:
    response = requests.get(file_path)
    response.raise_for_status()  # Raise an HTTPError for bad responses
    btn = st.download_button(
        label="Download Full DataSet",
        data=response.content,
        file_name="total_df.csv",
        mime="text/csv"
    )
except Exception as e:
    st.error(f"Failed to download the full dataset: {e}")

# Facility-specific dataset download
user_input = st.text_input("Enter Name of Facility").upper()
if user_input:
    sanitized_view_name = re.sub(r'\W+', '_', user_input)
    file_path_small = f'https://raw.githubusercontent.com/lksanterre/prison/main/clean_data/{sanitized_view_name}_df.csv'
    
    try:
        response = requests.get(file_path_small)
        response.raise_for_status()  # Check if the URL was fetched successfully
        btn = st.download_button(
            label=f"Download {user_input} DataSet",
            data=response.content,
            file_name=f"{sanitized_view_name}.csv",
            mime="text/csv"
        )
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            st.warning("The specified facility name does not exist. Please try again.")
        else:
            st.error("An unexpected error occurred. Please try again later.")
    except Exception as e:
        st.error(f"An error occurred: {e}")
