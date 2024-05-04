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
api_key = '48769aa9d81c48038f572120240405'
input_data_path = 'master_dataframe_cleaned.csv'
output_path = 'forecast.csv'
model_pickle = 'best_random_forest_model.pkl'
x_train = pd.read_csv('x_train.csv') # to properly fit scaler

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

def prophet_preprocess_fac(df):
    df['datetime_of_data'] = df['datetime_of_data'].apply(lambda x: parser.parse(x))
    df['ds'] = pd.to_datetime(df['datetime_of_data'])
    df['y'] = df["population"]
    df.set_index('ds', inplace=True)

    daily_data = df['y']
    rolling_median = daily_data.rolling(window=5, min_periods=1, center=True).median()
    daily_data_filled = daily_data.fillna(rolling_median)
    daily_data_filled.index = daily_data_filled.index.tz_localize(None)
    df_reset = daily_data_filled.reset_index()
    df_reset = df_reset[['ds', 'y']]
    return df_reset

def get_future_weather(future_date, location):
    today = datetime.now().date()
    future_datetime = datetime.strptime(future_date, '%Y-%m-%d %H:%M:%S')
    future_date = future_datetime.date()
    delta = (future_date - today).days

    default_temp = 60  # Default temperature
    default_precip = 0  # Default precipitation

    if 0 <= delta <= 10:
        full_url = f"http://api.weatherapi.com/v1/forecast.json?key={api_key}&q={location}&days=10"
        response = requests.get(full_url)
        if response.status_code == 200:
            data = response.json()
            for forecast in data['forecast']['forecastday']:
                if forecast['date'] == future_date.strftime('%Y-%m-%d'):
                    # Extract high and low temperatures from the forecast data
                    max_temp_f = forecast.get('day', {}).get('maxtemp_f', default_temp)
                    min_temp_f = forecast.get('day', {}).get('mintemp_f', default_temp)
                    totalprecip_mm = forecast.get('day', {}).get('totalprecip_mm', default_precip)
                    return max_temp_f, min_temp_f, totalprecip_mm
    
    return default_temp, default_temp, default_precip



def load_model_and_return_probabilities(new_data):
    with open(model_pickle, 'rb') as file:
        loaded_model = pickle.load(file)
    probabilities = loaded_model.predict_proba(new_data)
    return probabilities

# Load and Process Data
facility_names = data['title'].unique()
master_df = pd.DataFrame()

for facility in facility_names:
    print(f"Processing forecast for {facility}")
    data_df = data[data['title'] == facility]
    train = prophet_preprocess_fac(data_df)
    if len(train) < 2:
        print(f"Not enough data to fit the model for {facility}.")
        continue

    m = Prophet()
    m.fit(train)
    future = m.make_future_dataframe(periods=9)
    forecast = m.predict(future)
    new_columns = forecast[['ds', 'yhat']]
    current_datetime = datetime.now()
    future_dates_data = new_columns[new_columns['ds'] > current_datetime]
    future_dates_data = future_dates_data[1:]  # Skip the first row (last known data)
    future_dates_data['title'] = facility
    zip_code = data_df['zip_code'].dropna().iloc[0] if not data_df['zip_code'].isnull().all() else 'Unknown'
    future_dates_data['zip'] = zip_code

    for i, row in future_dates_data.iterrows():
        max_temp_f, min_temp_f, totalprecip_mm = get_future_weather(str(row['ds']), row['zip'])
        future_dates_data.at[i, 'max_temp_f'] = max_temp_f
        future_dates_data.at[i, 'min_temp_f'] = min_temp_f
        future_dates_data.at[i, 'totalprecip_mm'] = totalprecip_mm

    master_df = pd.concat([master_df, future_dates_data], ignore_index=True)

master_df.set_index('ds', inplace=True)
master_df_pred = master_df.copy()
#master_df_pred = master_df[['address','avgtemp_f', 'totalprecip_mm', 'yhat']]
master_df_pred.rename(columns={'max_temp_f': 'daily_high_temperature', 'min_temp_f': 'daily_low_temperature', 'totalprecip_mm': 'daily_precipitation', 'yhat':'population'}, inplace=True)

### STEP THREE: ADD ADDRESSES BASED ON FACILITY NAME ###

facility_dict = {'FPC ALDERSON': 'GLEN RAY RD. BOX A, ALDERSON, WV 24910',
 'FCI ALICEVILLE': '11070 HIGHWAY 14, ALICEVILLE, AL 35442',
 'FCI ALLENWOOD LOW': 'RT 15,2 MILES N OF ALLENWOOD, ALLENWOOD, PA 17810',
 'FCI ALLENWOOD MEDIUM': 'RT 15, 2 MI N OF ALLENWOOD, WHITE DEER, PA 17810',
 'USP ALLENWOOD': 'RT 15,2 MILES N OF ALLENWOOD, ALLENWOOD, PA 17810',
 'FCI ASHLAND': 'ST. ROUTE 716, ASHLAND, KY 41105',
 'USP ATLANTA': '601 MCDONOUGH BLVD SE, ATLANTA, GA 30315',
 'USP ATWATER': '1 FEDERAL WAY, ATWATER, CA 95301',
 'FCI BASTROP': '1341 HIGHWAY 95 NORTH, BASTROP, TX 78602',
 'FCI BEAUMONT LOW': '5560 KNAUTH ROAD, BEAUMONT, TX 77705',
 'FCI BEAUMONT MEDIUM': '5830 KNAUTH ROAD, BEAUMONT, TX 77705',
 'USP BEAUMONT': '6200 KNAUTH ROAD, BEAUMONT, TX 77705',
 'FCI BECKLEY': '1600 INDUSTRIAL ROAD, BEAVER, WV 25813',
 'FCI BENNETTSVILLE': '696 MUCKERMAN ROAD, BENNETTSVILLE, SC 29512',
 'FCI BERLIN': '1 SUCCESS LOOP ROAD, BERLIN, NH 03570',
 'USP BIG SANDY': '1197 AIRPORT ROAD, INEZ, KY 41224',
 'FCI BIG SPRING': '1900 SIMLER AVE, BIG SPRING, TX 79720',
 'MDC BROOKLYN': '80 29TH STREET, BROOKLYN, NY 11232',
 'FPC BRYAN': '1100 URSULINE AVENUE, BRYAN, TX 77803',
 'FCI BUTNER MEDIUM II': 'OLD NC HWY 75, BUTNER, NC 27509',
 'FCI BUTNER LOW': 'OLD NC HWY 75, BUTNER, NC 27509',
 'FCI BUTNER MEDIUM I': 'OLD NC HWY 75, BUTNER, NC 27509',
 'FMC BUTNER': 'OLD N. CAROLINA HWY 75, BUTNER, NC 27509',
 'USP CANAAN': '3057 ERIC J. WILLIAMS, WAYMART, PA 18472',
 'FMC CARSWELL': 'NAVAL AIR STATION, FORT WORTH, TX 76127',
 'MCC CHICAGO': '71 WEST VAN BUREN STREET, CHICAGO, IL 60605',
 'FCI COLEMAN LOW': '846 NE 54TH TERRACE, SUMTERVILLE, FL 33521',
 'FCI COLEMAN MEDIUM': '846 NE 54TH TERRACE, SUMTERVILLE, FL 33521',
 'USP COLEMAN II': '846 NE 54TH TERRACE, SUMTERVILLE, FL 33521',
 'USP COLEMAN I': '846 NE 54TH TERRACE, SUMTERVILLE, FL 33521',
 'FCI CUMBERLAND': '14601 BURBRIDGE RD SE, CUMBERLAND, MD 21502',
 'FCI DANBURY': '33 1/2 PEMBROKE STATION, DANBURY, CT 06811',
 'FMC DEVENS': '42 PATTON ROAD, AYER, MA 01432',
 'FCI DUBLIN': '5701 8TH ST - CAMP PARKS, DUBLIN, CA 94568',
 'FPC DULUTH': '4464 RALSTON DRIVE, DULUTH, MN 55811',
 'FCI EDGEFIELD': '501 GARY HILL ROAD, EDGEFIELD, SC 29824',
 'FCI EL RENO': '4205 HIGHWAY 66 WEST, EL RENO, OK 73036',
 'FCI ELKTON': '8730 SCROGGS ROAD, LISBON, OH 44432',
 'FCI ENGLEWOOD': '9595 WEST QUINCY AVENUE, LITTLETON, CO 80123',
 'FCI ESTILL': '100 PRISON ROAD, ESTILL, SC 29918',
 'FCI FAIRTON': '655 FAIRTON-MILLVILLE ROAD, FAIRTON, NJ 08320',
 'FCI FLORENCE': '5880 HWY 67 SOUTH, FLORENCE, CO 81226',
 'USP FLORENCE ADMAX': '5880 HWY 67 SOUTH, FLORENCE, CO 81226',
 'USP FLORENCE - HIGH': '5880 HWY 67 S, FLORENCE, CO 81226',
 'FCI FORREST CITY MEDIUM': '1400 DALE BUMPERS ROAD, FORREST CITY, AR 72335',
 'FCI FORREST CITY LOW': '1400 DALE BUMPERS ROAD, FORREST CITY, AR 72335',
 'FCI FORT DIX': '5756 HARTFORD &, JOINT BASE MDL, NJ 08640',
 'FMC FORT WORTH': '3150 HORTON ROAD, FORT WORTH, TX 76119',
 'FCI GILMER': '201 FCI LANE, GLENVILLE, WV 26351',
 'FCI GREENVILLE': '100 U.S. HWY 40, GREENVILLE, IL 62246',
 'MDC GUAYNABO': '652 CARRETERA 28, GUAYNABO, PR 00965',
 'FCI HAZELTON': '1640 SKY VIEW DRIVE, BRUCETON MILLS, WV 26525',
 'USP HAZELTON': '1640 SKY VIEW DRIVE, BRUCETON MILLS, WV 26525',
 'FCI HERLONG': '741-925 ACCESS ROAD A-25, HERLONG, CA 96113',
 'FDC HONOLULU': '351 ELLIOTT ST, HONOLULU, HI 96819',
 'FDC HOUSTON': '1200 TEXAS AVENUE, HOUSTON, TX 77002',
 'FCI JESUP': '2600 HIGHWAY 301 SOUTH, JESUP, GA 31599',
 'FCI LA TUNA': '8500 DONIPHAN ROAD, ANTHONY, TX 79821',
 'USP LEAVENWORTH': '1300 METROPOLITAN, LEAVENWORTH, KS 66048',
 'FCI LEAVENWORTH': '1300 METROPOLITAN LEAVENWORTH, KS  66048',
 'USP LEE': 'LEE COUNTY INDUSTRIAL PARK, PENNINGTON GAP, VA 24277',
 'USP LEWISBURG': '2400 ROBERT F. MILLER DRIVE, LEWISBURG, PA 17837',
 'FCI LEWISBURG': '2400 ROBERT F. MILLER DRIVE LEWISBURG, PA  17837',
 'FMC LEXINGTON': '3301 LEESTOWN ROAD, LEXINGTON, KY 40511',
 'FCI LOMPOC': '3600 GUARD ROAD, LOMPOC, CA 93436',
 'USP LOMPOC': '3901 KLEIN BLVD, LOMPOC, CA 93436',
 'FCI LORETTO': '772 SAINT JOSEPH ST., LORETTO, PA 15940',
 'MDC LOS ANGELES': '535 N ALAMEDA STREET, LOS ANGELES, CA 90012',
 'FCI MANCHESTER': '805 FOX HOLLOW ROAD, MANCHESTER, KY 40962',
 'FCI MARIANNA': '3625 FCI ROAD, MARIANNA, FL 32446',
 'USP MARION': '4500 PRISON ROAD, MARION, IL 62959',
 'USP MCCREARY': '330 FEDERAL WAY, PINE KNOT, KY 42635',
 'FCI MCDOWELL': '101 FEDERAL DRIVE, WELCH, WV 24801',
 'FCI MCKEAN': '6975 ROUTE 59, LEWIS RUN, PA 16738',
 'FCI MEMPHIS': '1101 JOHN A DENIE ROAD, MEMPHIS, TN 38134',
 'FCI MENDOTA': '33500 WEST CALIFORNIA AVENUE, MENDOTA, CA 93640',
 'FCI MIAMI': '15801 S.W. 137TH AVENUE, MIAMI, FL 33177',
 'FDC MIAMI': '33 NE 4TH STREET, MIAMI, FL 33132',
 'FCI MILAN': '4004 EAST ARKONA ROAD, MILAN, MI 48160',
 'FPC MONTGOMERY': 'MAXWELL AIR FORCE BASE, MONTGOMERY, AL 36112',
 'FCI MORGANTOWN': '446 GREENBAG ROAD, ROUTE 857, MORGANTOWN, WV 26501',
 'MCC NEW YORK': '150 PARK ROW, NEW YORK, NY 10007',
 'FCI OAKDALE II': '2105 EAST WHATLEY ROAD, OAKDALE, LA 71463',
 'FCI OAKDALE I': '1507 EAST WHATLEY ROAD, OAKDALE, LA 71463',
 'FTC OKLAHOMA CITY': '7410 S. MACARTHUR BLVD, OKLAHOMA CITY, OK 73169',
 'FCI OTISVILLE': 'TWO MILE DRIVE, OTISVILLE, NY 10963',
 'FCI OXFORD': 'COUNTY ROAD G & ELK AVENUE, OXFORD, WI 53952',
 'FCI PEKIN': '2600 S. SECOND ST., PEKIN, IL 61554',
 'FPC PENSACOLA': '110 RABY AVE, PENSACOLA, FL 32509',
 'FCI PETERSBURG MEDIUM': '1060 RIVER ROAD, HOPEWELL, VA 23860',
 'FCI PETERSBURG LOW': '1100 RIVER ROAD, HOPEWELL, VA 23860',
 'FDC PHILADELPHIA': '700 ARCH STREET, PHILADELPHIA, PA 19106',
 'FCI PHOENIX': '37900 N 45TH AVE, PHOENIX, AZ 85086',
 'FCI POLLOCK': '1000 AIRBASE ROAD, POLLOCK, LA 71467',
 'USP POLLOCK': '1000 AIRBASE ROAD, POLLOCK, LA 71467',
 'FCI RAY BROOK': '128 RAY BROOK ROAD, RAY BROOK, NY 12977',
 'FMC ROCHESTER': '2110 EAST CENTER STREET, ROCHESTER, MN 55904',
 'FCI SAFFORD': '1529 WEST HIGHWAY 366, SAFFORD, AZ 85546',
 'MCC SAN DIEGO': '808 UNION STREET, SAN DIEGO, CA 92101',
 'FCI SANDSTONE': '2300 COUNTY RD 29, SANDSTONE, MN 55072',
 'FCI SCHUYLKILL': 'INTERSTATE 81 & 901 W, MINERSVILLE, PA 17954',
 'FCI SEAGOVILLE': '2113 NORTH HWY 175, SEAGOVILLE, TX 75159',
 'FDC SEATAC': '2425 SOUTH 200TH STREET, SEATTLE, WA 98198',
 'FCI SHERIDAN': '27072 BALLSTON ROAD, SHERIDAN, OR 97378',
 'MCFP SPRINGFIELD': '1900 W. SUNSHINE ST, SPRINGFIELD, MO 65807',
 'FCI TALLADEGA': '565 EAST RENFROE ROAD, TALLADEGA, AL 35160',
 'FCI TALLAHASSEE': '501 CAPITAL CIRCLE, NE, TALLAHASSEE, FL 32301',
 'FCI TERMINAL ISLAND': '1299 SEASIDE AVENUE, SAN PEDRO, CA 90731',
 'FCI TERRE HAUTE': '4200 BUREAU ROAD NORTH, TERRE HAUTE, IN 47808',
 'USP TERRE HAUTE': '4700 BUREAU ROAD SOUTH, TERRE HAUTE, IN 47802',
 'FCI TEXARKANA': '4001 LEOPARD DRIVE, TEXARKANA, TX 75501',
 'FCI THOMSON': '1100 ONE MILE ROAD, THOMSON, IL 61285',
 'FCI THREE RIVERS': 'US HIGHWAY 72 WEST, THREE RIVERS, TX 78071',
 'FCI TUCSON': '8901 S. WILMOT ROAD, TUCSON, AZ 85756',
 'USP TUCSON': '9300 SOUTH WILMOT ROAD, TUCSON, AZ 85756',
 'FCI VICTORVILLE MEDIUM I': '13777 AIR EXPRESSWAY BLVD, VICTORVILLE, CA 92394',
 'FCI VICTORVILLE MEDIUM II': '13777 AIR EXPRESSWAY BLVD, VICTORVILLE, CA 92394',
 'USP VICTORVILLE': '13777 AIR EXPRESSWAY BLVD, VICTORVILLE, CA 92394',
 'FCI WASECA': '1000 UNIVERSITY DR, SW, WASECA, MN 56093',
 'FCI WILLIAMSBURG': '8301 HIGHWAY 521, SALTERS, SC 29590',
 'FPC YANKTON': '1016 DOUGLAS AVENUE, YANKTON, SD 57078',
 'FCI YAZOO CITY MEDIUM': '2225 HALEY BARBOUR PARKWAY, YAZOO CITY, MS 39194',
 'FCI YAZOO CITY LOW': '2225 HALEY BARBOUR PARKWAY, YAZOO CITY, MS 39194',
 'USP YAZOO CITY': '2225 HALEY BARBOUR PKWY, YAZOO CITY, MS 39194',
 'USP THOMSON': '1100 ONE MILE ROAD, THOMSON, IL 61285',
 'MCC New York': '150 PARK ROW, NEW YORK, NY 10007',
 'FCI ATLANTA' : '601 MCDONOUGH BLVD SE, ATLANTA, GA 30315',
 'FCI LOMPOC I': '3600 GUARD ROAD LOMPOC, CA  93436',
 'FCI LOMPOC II': '3901 KLEIN BLVD LOMPOC, CA  93436',
 'FCI MARION': '4500 PRISON ROAD MARION, IL 62959',
 'FPC MORGANTOWN': '446 GREENBAG ROAD, ROUTE 857 MORGANTOWN, WV  26501',
 'FCI YAZOO CITY LOW II': '2225 HALEY BARBOUR PARKWAY YAZOO CITY, MS  39194'}

master_df_pred['full_address'] = ''

for i in range(len(master_df_pred)):
    master_df_pred['full_address'][i] = facility_dict[master_df_pred['title'][i]]

### STEP FOUR: ADD ADDITIONAL FEATURES

# Address Components

def extract_address_components(df, address_column):
    # Create new columns with empty strings
    df['city'] = ''
    df['state'] = ''
    df['zip_code'] = ''
    
    # Iterate over the rows of the DataFrame
    for index, row in df.iterrows():
        try:
            # Assume the address format is "STREET, CITY, STATE ZIP"
            parts = row[address_column].split(',')
            # If there are at least 2 parts, the second to last is the city
            city_state_zip = parts[-1].strip().split(' ')
            df.at[index, 'city'] = parts[-2].strip() if len(parts) > 1 else ''
            
            # Check if there's a space in the last part to separate state and zip
            if len(city_state_zip) >= 2:
                df.at[index, 'state'] = city_state_zip[0].strip()
                df.at[index, 'zip_code'] = city_state_zip[1].strip()
            else:  # If there's no space, assume the last part is the state
                df.at[index, 'state'] = city_state_zip[0].strip()
        except Exception as e:
            # Handle any unexpected errors
            print(f"Error processing row {index}: {e}")
    
    return df

master_df_pred = extract_address_components(master_df_pred, 'full_address')


# Political Affiliation

state_political_leaning = {
    'AL': 'red', 'AK': 'red', 'AZ': 'purple', 'AR': 'red', 'CA': 'blue',
    'CO': 'purple', 'CT': 'blue', 'DE': 'blue', 'FL': 'purple', 'GA': 'purple',
    'HI': 'blue', 'ID': 'red', 'IL': 'blue', 'IN': 'red', 'IA': 'purple',
    'KS': 'red', 'KY': 'red', 'LA': 'red', 'ME': 'purple', 'MD': 'blue',
    'MA': 'blue', 'MI': 'purple', 'MN': 'blue', 'MS': 'red', 'MO': 'red',
    'MT': 'red', 'NE': 'red', 'NV': 'purple', 'NH': 'purple', 'NJ': 'blue',
    'NM': 'blue', 'NY': 'blue', 'NC': 'purple', 'ND': 'red', 'OH': 'purple',
    'OK': 'red', 'OR': 'blue', 'PA': 'purple', 'RI': 'blue', 'SC': 'red',
    'SD': 'red', 'TN': 'red', 'TX': 'purple', 'UT': 'red', 'VT': 'blue',
    'VA': 'purple', 'WA': 'blue', 'WV': 'red', 'WI': 'purple', 'WY': 'red', 'PR':'red'
}

def add_political_affiliation(data, state_political_leaning):
    # Create a new column for political affiliation with default value
    data['political_affiliation'] = 'unknown'
    
    # Iterate over the DataFrame using the correct indices
    for idx, row in data.iterrows():
        state = row['state']
        # Check if the state exists in the dictionary
        if state in state_political_leaning:
            data.at[idx, 'political_affiliation'] = state_political_leaning[state]
        else:
            print(f"Warning: State abbreviation {state} at index {idx} not found in dictionary")
    
    return data

master_df_pred = add_political_affiliation(master_df_pred, state_political_leaning)

# Gender identity

gender_dict = {'FPC ALDERSON': 'Female',
 'FCI ALICEVILLE': 'Female',
 'FCI ALLENWOOD LOW': 'Male',
 'FCI ALLENWOOD MEDIUM': 'Male',
 'USP ALLENWOOD': 'Male',
 'FCI ASHLAND': 'Male',
 'USP ATLANTA': 'Male',
 'USP ATWATER': 'Male',
 'FCI BASTROP': 'Male',
 'FCI BEAUMONT LOW': 'Male',
 'FCI BEAUMONT MEDIUM': 'Male',
 'USP BEAUMONT': 'Male',
 'FCI BECKLEY': 'Male',
 'FCI BENNETTSVILLE': 'Male',
 'FCI BERLIN': 'Male',
 'USP BIG SANDY': 'Male',
 'FCI BIG SPRING': 'Male',
 'MDC BROOKLYN': 'Male and Female',
 'FPC BRYAN': 'Female',
 'FCI BUTNER MEDIUM II': 'Male',
 'FCI BUTNER LOW': 'Male',
 'FCI BUTNER MEDIUM I': 'Male',
 'FMC BUTNER': 'Male',
 'USP CANAAN': 'Male',
 'FMC CARSWELL': 'Female',
 'MCC CHICAGO': 'Male and Female',
 'FCI COLEMAN LOW': 'Male',
 'FCI COLEMAN MEDIUM': 'Male',
 'USP COLEMAN II': 'Male',
 'USP COLEMAN I': 'Male',
 'FCI CUMBERLAND': 'Male',
 'FCI DANBURY': 'Male and Female',
 'FMC DEVENS': 'Male',
 'FCI DUBLIN': 'Female',
 'FPC DULUTH': 'Male',
 'FCI EDGEFIELD': 'Male',
 'FCI EL RENO': 'Male',
 'FCI ELKTON': 'Male',
 'FCI ENGLEWOOD': 'Male',
 'FCI ESTILL': 'Male',
 'FCI FAIRTON': 'Male',
 'FCI FLORENCE': 'Male',
 'USP FLORENCE ADMAX': 'Male',
 'USP FLORENCE - HIGH': 'Male',
 'FCI FORREST CITY MEDIUM': 'Male',
 'FCI FORREST CITY LOW': 'Male',
 'FCI FORT DIX': 'Male',
 'FMC FORT WORTH': 'Male',
 'FCI GILMER': 'Male',
 'FCI GREENVILLE': 'Male and Female',
 'MDC GUAYNABO': 'Male and Female',
 'FCI HAZELTON': 'Male and Female',
 'USP HAZELTON': 'Male',
 'FCI HERLONG': 'Male',
 'FDC HONOLULU': 'Male and Female',
 'FDC HOUSTON': 'Male and Female',
 'FCI JESUP': 'Male',
 'FCI LA TUNA': 'Male',
 'USP LEAVENWORTH': 'Male',
 'USP LEE': 'Male',
 'USP LEWISBURG': 'Male',
 'FMC LEXINGTON': 'Male and Female',
 'FCI LOMPOC': 'Male',
 'USP LOMPOC': 'Male',
 'FCI LORETTO': 'Male',
 'MDC LOS ANGELES': 'Male and Female',
 'FCI MANCHESTER': 'Male',
 'FCI MARIANNA': 'Male and Female',
 'USP MARION': 'Male',
 'USP MCCREARY': 'Male',
 'FCI MCDOWELL': 'Male',
 'FCI MCKEAN': 'Male',
 'FCI MEMPHIS': 'Male',
 'FCI MENDOTA': 'Male',
 'FCI MIAMI': 'Male',
 'FDC MIAMI': 'Male and Female',
 'FCI MILAN': 'Male',
 'FPC MONTGOMERY': 'Male',
 'FCI MORGANTOWN': 'Male',
 'MCC NEW YORK': 'Male',
 'FCI OAKDALE II': 'Male',
 'FCI OAKDALE I': 'Male',
 'FTC OKLAHOMA CITY': 'Male and Female',
 'FCI OTISVILLE': 'Male',
 'FCI OXFORD': 'Male',
 'FCI PEKIN': 'Male and Female',
 'FPC PENSACOLA': 'Male',
 'FCI PETERSBURG MEDIUM': 'Male',
 'FCI PETERSBURG LOW': 'Male',
 'FDC PHILADELPHIA': 'Male and Female',
 'FCI PHOENIX': 'Male and Female',
 'FCI POLLOCK': 'Male',
 'USP POLLOCK': 'Male',
 'FCI RAY BROOK': 'Male',
 'FMC ROCHESTER': 'Male',
 'FCI SAFFORD': 'Male',
 'MCC SAN DIEGO': 'Male and Female',
 'FCI SANDSTONE': 'Male',
 'FCI SCHUYLKILL': 'Male',
 'FCI SEAGOVILLE': 'Male',
 'FDC SEATAC': 'Male and Female',
 'FCI SHERIDAN': 'Male',
 'MCFP SPRINGFIELD': 'Male',
 'FCI TALLADEGA': 'Male',
 'FCI TALLAHASSEE': 'Male and Female',
 'FCI TERMINAL ISLAND': 'Male',
 'FCI TERRE HAUTE': 'Male',
 'USP TERRE HAUTE': 'Male',
 'FCI TEXARKANA': 'Male',
 'FCI THOMSON': 'Male',
 'FCI THREE RIVERS': 'Male',
 'FCI TUCSON': 'Male and Female',
 'USP TUCSON': 'Male',
 'FCI VICTORVILLE MEDIUM I': 'Male and Female',
 'FCI VICTORVILLE MEDIUM II': 'Male',
 'USP VICTORVILLE': 'Male',
 'FCI WASECA': 'Female',
 'FCI WILLIAMSBURG': 'Male',
 'FPC YANKTON': 'Male',
 'FCI YAZOO CITY MEDIUM': 'Male',
 'FCI YAZOO CITY LOW': 'Male',
 'USP YAZOO CITY': 'Male',
 'USP THOMSON': 'Male',
 'MCC New York': 'Male',
 'FCI ATLANTA': 'Male',
 'FCI LEAVENWORTH': 'Male',
 'FCI LEWISBURG': 'Male',
 'FCI LOMPOC I': 'Male',
 'FCI LOMPOC II': 'Male',
 'FCI MARION': 'Male',
 'FPC MORGANTOWN': 'Male',
 'FCI YAZOO CITY LOW II': 'Male'}

master_df_pred['gender'] = ''

for i in range(len(master_df_pred)):
    master_df_pred['gender'][i] = gender_dict[master_df_pred['title'][i]]

# Historical Lockdown Percentage
history = pd.read_csv('/Users/ianduke/Desktop/prison/data_update/master_dataframe_cleaned.csv')

def lockdown_percentage(facility_data):
    """
    Calculate the percentage of days a facility been locked down.
    """
    # Drop rows where visiting_status is None
    facility_data = facility_data.dropna(subset=['visiting_status'])
    # Count the number of times the facility was locked down
    lockdown_days = facility_data[facility_data['visiting_status'] == 'Suspended'].shape[0]
    total_days = facility_data.shape[0]
    if total_days > 0:
        lockdown_perc = (lockdown_days / total_days) * 100
    else:
        lockdown_perc = 0
    return lockdown_perc

facility_name = data["title"].unique()
facility_percentage = {}
for facility in facility_name:
    facility_data = data[data['title'] == facility]
    percentage = lockdown_percentage(facility_data)
    facility_percentage[facility] = percentage
facility_prob_df = pd.DataFrame(list(facility_percentage.items()), columns=["title", "lockdown_percentage"])

percentage_dict = {}

for i in range(len(facility_prob_df)):
    percentage_dict[facility_prob_df['title'][i]] = facility_prob_df['lockdown_percentage'][i]

master_df_pred['lockdown_percentage'] = ''

for i in range(len(master_df_pred)):
    facility = master_df_pred['title'][i]
    master_df_pred['lockdown_percentage'][i] = percentage_dict[facility]

### STEP FOUR: ML PREPROCESSING

modeling_columns = ['population','title','daily_high_temperature', 'daily_low_temperature', 'daily_precipitation', 'gender', 'political_affiliation', 'lockdown_percentage']

modeling_data = master_df_pred[modeling_columns]

# Dummy encode the specified columns
dummy_columns = ['gender', 'political_affiliation']
modeling_data_encoded = pd.get_dummies(modeling_data, columns=dummy_columns, drop_first=True, dtype = int)


### STEP THREE: USE FUTURE DATAFRAME TO MAKE PREDICTIONS ###
modeling_data_encoded_input = modeling_data_encoded.drop('title', axis = 1)
scaler = StandardScaler()
scaler = scaler.fit(x_train)
x_pred_sc_array = scaler.transform(modeling_data_encoded_input)
x_pred_sc = pd.DataFrame(x_pred_sc_array, columns=modeling_data_encoded_input.columns)
predictions = load_model_and_return_probabilities(x_pred_sc)
predictions = pd.DataFrame(predictions)
predictions.columns = predictions.columns.astype(str)
predictions = predictions['1']

modeling_data_encoded['lockdown_probability'] = predictions.values
pred = modeling_data_encoded['lockdown_probability']

modeling_data_encoded.to_csv('forecast.csv')