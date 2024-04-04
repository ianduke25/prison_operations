import streamlit as st
import re
import os
st.title('US Prison Population and Visitation')
st.write('Nick Miller | Ian Duke | Tianyunxi (Emily) Yin | Caleb Hamblen | Lance Santerre')
file_path = 'https://github.com/lksanterre/prison/edit/main/clean_data/total_df.csv'

with open(file_path, "rb") as file:
    btn = st.download_button(
            label="Download Full DataSet",
            data=file,
            file_name="total_df.csv",
            mime="text/csv"
        )
file_path_small = 'https://github.com/lksanterre/prison/edit/main/clean_data/'
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
