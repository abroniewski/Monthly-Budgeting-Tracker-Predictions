# this code was created by typing prompts as comments and having GitHub CoPilot complete the code
# some minor edits were made to the code to make it work

# import necessary libraries
import pandas as pd
import os
import requests
from zipfile import ZipFile
from io import BytesIO


# create a function to import a csv as dataframe from a given directory
def import_csv(csv_file):
    """Import a csv file as a dataframe"""
    df = pd.read_csv(csv_file)
    return df


# create a function to iterate through a list of dataframes and export them to a csv file
def export_csv(df, csv_file):
    """Export a dataframe to a csv file"""
    df.to_csv(csv_file, index=False)


# create a function to iterate through the list of csv files and import them as dataframes if they are not hidden files
def import_csv_list(csv_list):
    """Import a list of csv files as dataframes"""
    df_list = []
    # add condition to ignore hidden files
    for csv_file in csv_list:
        # only include files with "statement" in the name
        if csv_file.endswith('.csv') and 'statement' in csv_file:
            csv_file = csv_dir + '/' + csv_file  # variable to combine the directory and csv file name
            df = import_csv(csv_file)
            df_list.append(df)
    df = pd.concat(df_list)
    return df


# create a funciton to remove the text similar to "Card transaction of 1300.00 AED issued by" from the description column
def remove_description_text(df):
    """Remove text from the description column"""
    df['Description'] = df['Description'].str.replace(r'Card transaction of \d+\.\d+ \w+ issued by ', '')
    return df


# create function to create data/processed directory if it does not exist
def create_processed_dir(path='data/processed'):
    """Create a directory to store processed data"""
    if not os.path.exists(path):
        os.makedirs(path)


# create a function to create a new column called location and populate it with the location of the transaction
def create_location_column(df):
    """Create a new column called location and populate it with the location of the transaction"""
    df['Location'] = df['Description'].str.extract(r'([A-Z][a-z]+, [A-Z]{2})')
    return df


# create a function to download all the city names in the world and save it to a list
def download_city_list():
    """Download a list of all the cities in the world"""
    # download the list of cities from the website
    url = 'https://simplemaps.com/static/data/world-cities/basic/simplemaps_worldcities_basicv1.75.zip'
    # open zip with multiple files and extract the worldcities.csv file
    with ZipFile(BytesIO(requests.get(url).content)) as myzip:
        with myzip.open('worldcities.csv') as myfile:
            # read the csv file as a dataframe
            df = pd.read_csv(myfile)
    # create a list from the df
    city_list = df['city_ascii'].tolist()
    return city_list


# search through description column for city names based on online database of cities, extract the city name and add it to a new column called "Location"
def create_location_column(df, city_list):
    """Create a new column called location and populate it with the location of the transaction"""
    # Create a location column in dataframe and populated it with last word in description column
    df['Location'] = df['Description'].str.split().str[-1]
    # Convert all location names to title case
    df['Location'] = df['Location'].str.title()
    # check if the string in the location column matches a city name in the city lis. if it does, replace the string in the location column with the city name. if it does not, replace the string in the location column with "Unknown"
    df['Location'] = df['Location'].apply(lambda x: x if x in city_list else 'Unknown')
    return df


# create a funciton that identifies words that appear frequently in the description column
def identify_frequent_words(df, city_list):
    """Identify words that appear frequently in the description column"""
    # create a list of words to exclude from the word count
    exclude_list = ['money', 'transaction', 'to', 'the', 'and', 'of', 'for', 'in', 'on', 'at', 'from', 'with', 'by', 'as', 'an', 'a', 'is', 'are', 'be', 'was', 'were', 'will', 'would', 'could', 'should', 'have', 'has', 'had', 'may', 'might', 'must', 'can']
    #combine exclude_list with city_list lower case
    exclude_list = exclude_list + [x.lower() for x in city_list]
    # create a list of words that appear more than 5 times in the description column
    frequent_words = df['Description'].str.split(expand=True).stack().value_counts()[df['Description'].str.split(expand=True).stack().value_counts() > 3].index.tolist()
    # remove words from the frequent words list that are in the exclude list not case-sensitive
    frequent_words = [word for word in frequent_words if word.lower() not in exclude_list]
    # make all frequent words lower case
    frequent_words = [word.lower() for word in frequent_words]
    # create a list of substrings to remove from words in frequent words list
    substrings = ['www.', '.com', '.gov.uk/cp', '*', '.de', '.com/bill', '.ca']
    # for each word in the frequent words list, place the substrings from the word with an empty string
    for word in frequent_words:
        for substring in substrings:
            word.replace(substring, '')
    # remove words that are less than 3 characters long
    frequent_words = [word for word in frequent_words if len(word) > 3]
    # remove words that include digits
    frequent_words = [word for word in frequent_words if not any(char.isdigit() for char in word)]

    return frequent_words


# create a function that creates a column named "keywords" and populates it with the most frequent words in the description column
def create_keywords_column(df, city_list):
    """Create a column named "keywords" and populate it with the most frequent words in the description column"""
    frequent_words = identify_frequent_words(df, city_list)
    # create a column called "keywords" and populate it with the any frequent words that appear in the description column
    df['Keywords'] = df['Description'].str.lower().str.split().apply(lambda x: [item for item in x if item in frequent_words])

    return df


# create a function to print the total sum of amount to console
def print_total_amount(df):
    """Print the total sum of amount to console"""
    print('Total amount spent: ' + str(df['Amount'].sum()))


# variable to store directory of csv statements
csv_dir = '/Users/adambroniewski/Documents/Finances/Budgets and Tracking/Statements'


csv_list = os.listdir(csv_dir)  # create a list of csv files in the directory
df = import_csv_list(csv_list)  # import the list of csv statement files as dataframes
remove_description_text(df)
city_list= download_city_list()
create_location_column(df, city_list)
create_keywords_column(df, city_list)
print_total_amount(df)

create_processed_dir('data/processed')  # create directory to store processed data
export_csv(df, 'data/processed/all_statements.csv')  # export dataframe to csv