import pandas as pd
import numpy as np
from prophet import Prophet
from dateutil import parser
from datetime import datetime
import requests
from sklearn.preprocessing import StandardScaler
from scipy.special import expit
import pickle

# Hardcode API Key and Data Paths
api_key = 'cae38d1f50ab4d78b6041519241204'
input_data_path = 'master_dataframe_cleaned.csv'
output_path = 'forecast.csv'
model_pickle = 'best_logistic_model.pkl'

# Load and Preprocess Data
data = pd.read_csv(input_data_path)

###STEP ONE: INPUT DATA PREPROCESSING###
# Drop column if exists
if 'operation_level' in data.columns:
    data = data.drop(columns=['operation_level'])

# Replace commas in population and convert to str
data['population'] = data['population'].astype(str).str.replace(',', '')

# Hardcode details for facilities with scraping problems
for i in range(len(data)):
    if data.iloc[i]['title'] == 'USP THOMSON':
        data.at[i, 'full_address'] = '1100 ONE MILE ROAD, THOMSON, IL 61285'
        data.at[i, 'bop_region'] = 'North Central Region'
        data.at[i, 'county'] = 'CARROLL'
        data.at[i, 'judicial_district'] = 'Northern District of Illinois'
        data.at[i, 'gender'] = 'Male'
    elif data.iloc[i]['title'] == 'MCC New York':
        data.at[i, 'full_address'] = '150 PARK ROW, NEW YORK, NY 10007'
        data.at[i, 'bop_region'] = 'Northeast Region'
        data.at[i, 'county'] = 'New York'
        data.at[i, 'judicial_district'] = 'Southern New York'
        data.at[i, 'gender'] = 'Male'

# Remove entries with missing or 'nan' population
data.dropna(subset=['population'], inplace=True)
data = data[data['population'].str.lower() != 'nan']

# Reset index after modifications
data = data.reset_index(drop=True)

# Extract zip code from the full address
data['zip_code'] = data['full_address'].apply(lambda x: x[-5:])

# Remove specific facilities if required
data = data[data['title'] != 'MCC New York']

# Remove unnecessary columns 
data = data.loc[:, ~data.columns.str.startswith('Unnamed')]


### STEP TWO: CREATE FUTURE DATAFRAME WITH MODEL FEATURES###

# Add future political affiliation

# def prophet_preprocess_fac(df):
#     df['datetime_of_data'] = df['datetime_of_data'].apply(lambda x: parser.parse(x))
#     df['ds'] = pd.to_datetime(df['datetime_of_data'])
#     df['y'] = df["population"]
#     df.set_index('ds', inplace=True)

#     daily_data = df['y']
#     rolling_median = daily_data.rolling(window=5, min_periods=1, center=True).median()
#     daily_data_filled = daily_data.fillna(rolling_median)
#     daily_data_filled.index = daily_data_filled.index.tz_localize(None)
#     df_reset = daily_data_filled.reset_index()
#     df_reset = df_reset[['ds', 'y']]
#     return df_reset

# def get_future_weather(future_date, location):
#     today = datetime.now().date()
#     future_datetime = datetime.strptime(future_date, '%Y-%m-%d %H:%M:%S')
#     future_date = future_datetime.date()
#     delta = (future_date - today).days

#     default_temp = 60  # Default temperature
#     default_precip = 0  # Default precipitation

#     if 0 <= delta <= 10:
#         full_url = f"http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={location}&days=10"
#         response = requests.get(full_url)
#         if response.status_code == 200:
#             data = response.json()
#             for forecast in data['forecast']['forecastday']:
#                 if forecast['date'] == future_date.strftime('%Y-%m-%d'):
#                     avgtemp_f = forecast.get('day', {}).get('avgtemp_f', default_temp)
#                     totalprecip_mm = forecast.get('day', {}).get('totalprecip_mm', default_precip)
#                     return avgtemp_f, totalprecip_mm

#     # Return default values if no data is found or API call is not successful
#     return default_temp, default_precip

# def load_model_and_return_probabilities(new_data):
#     with open(model_pickle, 'rb') as file:
#         loaded_model = pickle.load(file)
#     decision_scores = loaded_model.decision_function(new_data)
#     probabilities = expit(decision_scores)
#     return probabilities

# # Load and Process Data
# facility_names = data['title'].unique()
# master_df = pd.DataFrame()

# for facility in facility_names:
#     print(f"Processing forecast for {facility}")
#     data_df = data[data['title'] == facility]
#     train = prophet_preprocess_fac(data_df)
#     if len(train) < 2:
#         print(f"Not enough data to fit the model for {facility}.")
#         continue

#     m = Prophet()
#     m.fit(train)
#     future = m.make_future_dataframe(periods=9)
#     forecast = m.predict(future)
#     new_columns = forecast[['ds', 'yhat']]
#     current_datetime = datetime.now()
#     future_dates_data = new_columns[new_columns['ds'] > current_datetime]
#     future_dates_data = future_dates_data[1:]  # Skip the first row (last known data)
#     future_dates_data['title'] = facility
#     zip_code = data_df['zip_code'].dropna().iloc[0] if not data_df['zip_code'].isnull().all() else 'Unknown'
#     future_dates_data['zip'] = zip_code

#     for i, row in future_dates_data.iterrows():
#         avgtemp_f, totalprecip_mm = get_future_weather(str(row['ds']), row['zip'])
#         future_dates_data.at[i, 'avgtemp_f'] = avgtemp_f
#         future_dates_data.at[i, 'totalprecip_mm'] = totalprecip_mm

#     master_df = pd.concat([master_df, future_dates_data], ignore_index=True)

# master_df.set_index('ds', inplace=True)
# master_df_pred = master_df[['avgtemp_f', 'totalprecip_mm', 'yhat']]
# master_df_pred.rename(columns={'avgtemp_f': 'daily_temperature', 'totalprecip_mm': 'daily_precipitation', 'yhat':'population'}, inplace=True)

# ### STEP THREE: USE FUTURE DATAFRAME TO MAKE PREDICTIONS ###
# scaler = StandardScaler()
# x_pred_sc_array = scaler.fit_transform(master_df_pred)
# x_pred_sc = pd.DataFrame(x_pred_sc_array, columns=master_df_pred.columns)
# predictions = load_model_and_return_probabilities(x_pred_sc)
# master_df['lockdown_probability'] = predictions

# # Save to CSV
# master_df.to_csv(output_path)

# print("Processing complete. Results saved to:", output_path)

data.to_csv('TEST_APRIL.csv')