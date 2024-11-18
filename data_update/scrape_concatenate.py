# pylint: skip-file

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import csv
import pandas as pd
from datetime import datetime
import pytz
from fake_useragent import UserAgent

def scrape():
    # manually clean up csv and import
    # NOTE: replace with local filepath to facilities.csv
    bop_facilities = pd.read_csv('facilities.csv')

    # create list of facilities
    facility_list = bop_facilities['facilities']

    # Initialize UserAgent
    ua = UserAgent()

    list_of_dictionaries = []

    # Initialize the webdriver outside the loopto avoid opening a new browser
    # for each URL.
    chrome_options = Options()

    # Add the headless argument to run Chrome in the background
    chrome_options.add_argument("--headless")

    # Assign a random user agent for the driver
    chrome_options.add_argument(f"user-agent={ua.random}")

    # Initialize the Service object with the path to the ChromeDriver
    service = Service(ChromeDriverManager().install())

    # Use the service object when creating the Chrome WebDriver instance
    driver = webdriver.Chrome(service=service, options=chrome_options)

    for i in range(len(facility_list)):
        facility_dictionary = {}
        url = facility_list[i]
        print(url)

        driver.get(url)

        time.sleep(10)

        title_tag = driver.find_element(By.XPATH, '//*[@id="title_cont"]/h2')
        title = title_tag.text

        population_tag = driver.find_element(By.XPATH, '//*[@id="pop_count"]')
        population = population_tag.text

        address_tag = driver.find_element(By.XPATH, '//*[@id="address"]')
        address = address_tag.text
        city_tag = driver.find_element(By.XPATH, '//*[@id="city"]')
        city = city_tag.text
        state_tag = driver.find_element(By.XPATH, '//*[@id="state"]')
        state = state_tag.text
        zip_code_tag = driver.find_element(By.XPATH, '//*[@id="zip_code"]')
        zip_code = zip_code_tag.text
        full_address = address + ', ' + city + ', ' + state + ' ' + zip_code
        # operations_tag = driver.find_element(By.XPATH, '//*[@id="ops_level"]/a')
        # level = operations_tag.get_attribute('title')

        suspension_tag = driver.find_element(By.XPATH, '//*[@id="notice_cont"]/h3')
        suspension = suspension_tag.text

        gender_tag = driver.find_element(By.XPATH, '//*[@id="pop_gender"]')
        gender = gender_tag.text

        judicial_district_tag = driver.find_element(By.XPATH, '//*[@id="facl_facts"]/table/tbody/tr[3]/td[2]')
        judicial_district = judicial_district_tag.text

        county_tag = driver.find_element(By.XPATH, '//*[@id="county"]')
        county = county_tag.text

        bop_region_tag = driver.find_element(By.XPATH, '//*[@id="region"]')
        bop_region = bop_region_tag.text

        # Get the current datetime and make it timezone-aware using the system's
        # local timezone
        current_datetime = datetime.now().astimezone(pytz.utc).astimezone()
        # Format the datetime with timezone
        formatted_datetime_with_tz = current_datetime.strftime(
            '%Y-%m-%d %H:%M:%S %Z')

        facility_dictionary['title'] = title
        facility_dictionary['population'] = population
        facility_dictionary['operation_level'] = 'No Longer Available'
        facility_dictionary['gender'] = gender
        facility_dictionary['judicial_district'] = judicial_district
        facility_dictionary['county'] = county
        facility_dictionary['bop_region'] = bop_region
        facility_dictionary['full_address'] = full_address

        if len(suspension) > 0:
            facility_dictionary['visiting_status'] = 'Suspended'
            print_status = 'Suspended'
        else:
            facility_dictionary['visiting_status'] = 'Not Suspended'
            print_status = 'Not Suspended'

        facility_dictionary['datetime_of_data'] = formatted_datetime_with_tz

        list_of_dictionaries.append(facility_dictionary)

        # Delay between requests
        time.sleep(5)  # waits for 5 seconds to allow page to fully load

        # print(f'Title: {title}\nPopulation: {population}\nVisiting Status: {print_status}\
        #     \nGender: {gender}\nJudicial District: {judicial_district}\nCounty: {county}\nBOP Region: {bop_region}\
        #     \nFull Address: {full_address}\n')

    driver.quit()

    new_data = pd.DataFrame(list_of_dictionaries)
    return new_data


if __name__ == "__main__":
    new_data = scrape()
    columns_to_include = ['title', 'population', 'operation_level', 'gender', 'judicial_district', 'county', 'bop_region', 'full_address', 'visiting_status', 'datetime_of_data']
    new_data = new_data[columns_to_include]

    history = pd.read_csv('master_dataframe_cleaned.csv')

    result_df = pd.concat([new_data, history])
    result_df.to_csv('master_dataframe_cleaned.csv', index=False)