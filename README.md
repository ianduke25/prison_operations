
# Prison Operations Snapshot

## Description
The Prison Operations Snapshot is a data management and visualization tool designed to store and process information about prison populations and facility lockdown statuses. This project includes a Streamlit application that provides real-time data visualizations, aggregation functionalities, and future population + lockdown predictions. It also features several Python scripts for data cleaning, along with a dedicated folder that automates this process using bash commands.

## Hosting
The Prison Operations Snapshot is a Streamlit application that is hosted on the Streamlit Community Cloud. Due to this setup, any changes made to the webserver.py file or related data in this repository will be directly reflected in the application. The application is refeshed based on the contents of this repository whenever the application is opened, refreshed, or a user interacts with a feature on the page.

## Usage
To start the Streamlit application and visualize the data:
```
streamlit run webserver.py
```

## Functionality
The first piece of functionality in our application is the ability to download the lockdown data for each prison individually as a CSV file. This allows users to manipulate the data themselves and get a look behind the scenes at what is powering our models. The second piece of our application is the ability to select a prison from a drop down list and see the percentage of time that the prison was locked down. This is a helpful feature for lawyers or defense workers who are trying to advocate on behalf of their clients to a judge. The next piece of our application is the implementation of machine learning and time series models. Upon selecting a prison from the drop down the time series model will run automatically to predict the prison population for the next 7 days. In addition, a random forest model is trained to predict the probability of the selected prison being locked down. This probability can be seen when hovering over the time series plot with the user's mouse. This functionality is helpful for any user who may be traveling to a prison and is planning their visit.

## Directory of components
- **.streamlit**: Configuration file
- **Data_Update**: Folder that encompases the following:

    1.) All data storage. Data stored here is read by the webserver.py file and displayed/utilized in the application. The main data to be used in the application is stored in the mater_datafram_cleaned.csv file. Forecasted predictions are stored in the forecast.csv.
  
    2.) Scraping of web data from the BOP sites. This data is required to be scraped daily because of our time series model. Scraping is completed in the scrape_concatenate.py file. Modeling is completed in the future_closure_predictions.py file.
  
    3.) Automation of scraping scripts and organization of updated data in a bash script called data_update.sh.
  
- **facilties**: List of all facilties and their specific latitiude and longitude values.
- **requirements.txt**: Required libraries and dependencies
- **webserver.py**: The actual application source code. This file hosts the front end display as well as the intented functionality for the various application features.
- **lcokdown_prediction_modeling.ipynb**: Notebook for development of machine learning models to predict lockdowns.

## Contributors
We are a team of data scientests at the University of San Francisco. 

## Application Access
The application can be accessed through the landing page here: https://justice-data-collaborative.webflow.io/


