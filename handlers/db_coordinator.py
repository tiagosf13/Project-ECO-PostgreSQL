import os
import json
import csv
import psycopg2


def read_json(filename):

    # Read the file and load its content as JSON
    with open(os.getcwd() + filename, "r", encoding="utf8") as file:
        data = json.load(file)
    file.close()

    return data


def read_csv(filename):

    # Read the CSV file and store the content in a array
    with open(filename, "r", newline = "", encoding = "utf8") as file:
        csv_reader = csv.reader(file, delimiter=";")
        lst = list(csv_reader)
    file.close()

    # There isn't records in the CSV file if the array is None
    if lst == None:
        return []
    else:
        return lst


def write_csv(filename, data):
    try:
        with open(filename, "w", newline="", encoding="utf8") as file:
            csv_writer = csv.writer(file, delimiter=";")
            csv_writer.writerows(data)
            
        file.close()
        return True
    except:
        # An error occurred
        return False


def save_image_db_coordinator(path, image_data):
    with open(path, 'wb') as f:
        f.write(image_data)
    f.close()


def db_query(query, params=None):

    # Get the credentials for accessing the database
    credentials = read_json("/handlers/db_credentials.json")

    # Connect to the database
    conn = psycopg2.connect(
        host=credentials["host"],
        dbname=credentials["dbname"],
        user=credentials["user"],
        password=credentials["password"],
        port=credentials["port"]
    )

    # Initiate the cursor
    cur = conn.cursor()

    # Check if there is any parameters
    if params:

        # Execute query with parameters
        cur.execute(query, params)

    else:

        # Execute query without parameters
        cur.execute(query)

    # Define select_in_query as False by default
    select_in_query = False

    # Check if the query has SELECT
    if "SELECT" in query:

        # Fetch all the data
        data = cur.fetchall()
        select_in_query = True

    # Commit the connection
    conn.commit()

    # Close the cursor
    cur.close()

    # Close the connection
    conn.close()

    # Check if the query has SELECT
    if select_in_query:

        # Return the requested data
        return data