#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests

def get_postcode(row):
    ''' This function uses latitude and longitude data to extract zip code.
        The input is a dataframe, and the output is zipcode '''
    
    # Get longitude and latitude values from dataframe
    lon = row['Longitude']
    lat = row['Latitude']
    
    # Base URL for Nominatim API
    base_url = 'https://nominatim.openstreetmap.org/reverse'
    
    # Build URL with longitude and latitude parameters
    url = f"{base_url}?format=jsonv2&lat={lat}&lon={lon}"
    
    try:
        # Make API request and retrieve JSON response
        response = requests.get(url)
        response.raise_for_status()
        json_data = response.json()
        
        # Extract postcode from address dictionary
        address = json_data.get('address')
        postcode = None
        if address:
            postcode = address.get('postcode')
        
        # Return postcode
        return postcode
        
    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')
    except Exception as err:
        print(f'Other error occurred: {err}')


# In[2]:


import pandas as pd

def get_zillow_data(cur, conn, zipcode):
    ''' This function takes postgres connection information and 
        user input of zip to extract zillow information from Postgres 
        and return a df filtered on zipcode '''
    
    zipcode = int(zipcode)
    zillow_data = """ SELECT borough, street_address, zipcode, bathrooms_full, bedrooms, 
                    living_area, currency, price, yearbuilt, description
                    FROM property_location AS loc
                    JOIN property_details AS det ON loc.zpid = det.zpid
                    JOIN price_tax_info AS price ON det.zpid = price.zpid
                    JOIN property_features AS fea ON price.zpid = fea.zpid
                    WHERE zipcode = %s """
    cur.execute(zillow_data, (zipcode,))
    try:
        zillow_df = pd.read_sql(zillow_data, conn, params=[zipcode])
    except pd.errors.EmptyDataError:
        print(f"No data found for zip code {zipcode}.")
        zillow_df = pd.DataFrame()
    return zillow_df


# In[3]:


import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
import io

def get_graphs(collection, zipcode):
    ''' This function takes Mongodb collection details and zipcode, 
        extracts data from mongodb based on user provided zipcode and 
        returns a list of plots'''
    
    try:
        # Convert string to int
        zipcode_int = int(zipcode)

        cursor = collection.find({"zipcode": zipcode_int})

        # Convert into dataframe
        zipcode_df = pd.DataFrame(list(cursor))

        # Raise an error if the dataframe is empty
        if zipcode_df.empty:
            raise pd.errors.EmptyDataError("No data found for the provided zipcode: " + str(zipcode))

        figs = []

        # Convert zipcode to string for title
        zipcode = str(zipcode)

        # Bar chart of top 5 offense types
        offense_count = zipcode_df['OFNS_DESC'].value_counts().nlargest(5)
        fig = plt.figure()
        plt.barh(offense_count.index, offense_count.values)
        plt.title('Top 5 Offense Types in ' + zipcode)
        plt.xlabel('Frequency')
        plt.ylabel('Offense Type Description')
        figfile = io.BytesIO()
        plt.savefig(figfile, format='png')
        figfile.seek(0)
        figdata_png = base64.b64encode(figfile.getvalue()).decode('utf8')
        figs.append(figdata_png)

        # Pie chart of age distribution of suspects
        age_count = zipcode_df['SUSP_AGE_GROUP'].value_counts()
        fig = plt.figure()
        plt.pie(age_count.values, labels=age_count.index, autopct='%1.1f%%')
        plt.title('Age Distribution of Suspects in ' + zipcode)
        figfile = io.BytesIO()
        plt.savefig(figfile, format='png')
        figfile.seek(0)
        figdata_png = base64.b64encode(figfile.getvalue()).decode('utf8')
        figs.append(figdata_png)

        # Pie chart of race distribution of suspects
        race_count = zipcode_df['SUSP_RACE'].value_counts()
        fig = plt.figure()
        plt.pie(race_count.values, labels=race_count.index, autopct='%1.1f%%')
        plt.title('Race Distribution of Suspects in ' + zipcode)
        figfile = io.BytesIO()
        plt.savefig(figfile, format='png')
        figfile.seek(0)
        figdata_png = base64.b64encode(figfile.getvalue()).decode('utf8')
        figs.append(figdata_png)

        # Bar chart of top 5 premise types
        premise_count = zipcode_df['PREM_TYP_DESC'].value_counts().nlargest(5)
        fig = plt.figure()
        plt.barh(premise_count.index, premise_count.values)
        plt.title('Top 5 Premise Types in ' + zipcode)
        plt.xlabel('Frequency')
        plt.ylabel('Premise Type Description')
        figfile = io.BytesIO()
        plt.savefig(figfile, format='png')
        figfile.seek(0)
        figdata_png = base64.b64encode(figfile.getvalue()).decode('utf8')
        figs.append(figdata_png)
        
        # Return the list of encoded images
        return figs

    except pd.errors.EmptyDataError as e:
        print(e)
        return []

