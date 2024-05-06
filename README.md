
# Prison Operations Snapshot

## Description
The Prison Operations Snapshot is a data management and visualization tool designed to store and process information about prison populations and facility lockdown statuses. This project includes a Streamlit application that provides real-time data visualizations, aggregation functionalities, and future population + lockdown predictions. It also features several Python scripts for data cleaning, along with a dedicated folder that automates this process using bash commands.

## Hosting
The Prison Operations Snapshot is a Streamlit application that is hosted on the Streamlit Community Cloud. Due to this setup, any changes made to the webserver.py file or related data in this repository will be directly reflected in the application. The application is refeshed based on the contents of this repository at regular intervals.

## Usage
To start the Streamlit application and visualize the data:
```
streamlit run webserver.py
```

## Features
- **Data Storage**: Efficiently stores data regarding prison populations and lockdown statuses.
- **Data Aggregation**: Allows complex aggregations on the stored data.
- **Real-time Visualization**: Provides real-time data visualization using a Streamlit application.
- **Data Cleaning Automation**: Automated scripts in Bash for consistent data cleaning processes.

## Data Cleaning Automation:
- 
### Data Storage:
- **Facilties**: List of all facilties and their specific latitiude and longitude values
- **Dirty_Data**: Compliation of all the preprocessed data
- **Clean_data**: Complation of all the processed data, Side note we now are using an aggerate of all the data into one csv instade of unique csv's based upon each faciliity
- **Data_Update**: 
### Data Aggregation and Real-time Visualization:
- Leveraging streamlit to help us aggeragte data based upon specific facilities.



## Contributing
We are a team of data scientests at the University of San Francisco. 

## Contact Information
For any queries, you can reach the website at the url: https://preview.webflow.com/preview/defense-data-center?utm_medium=preview_link&utm_source=designer&utm_content=defense-data-center&preview=d01abafb75ea72533c8cbdd0190b72cb&workflow=preview


