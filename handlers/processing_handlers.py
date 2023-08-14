import json
import os
import pprint
import random
import csv
import shutil
import bleach
import matplotlib.pyplot as plt
import numpy as np
import base64
from handlers.converter import *
from handlers.db_coordinator import *
from decimal import Decimal
from datetime import datetime
from string import ascii_uppercase
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.colors import Color
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Image, Paragraph, Spacer, PageBreak
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import psycopg2



def send_email(to, subject, body):

    # Read Email credentials file
    credentials = read_json("/handlers/email_credentials.json")

    # Create a MIMEText object to represent the email body
    msg = MIMEMultipart()
    msg['From'] = credentials["email"]
    msg['To'] = to
    msg['Subject'] = subject

    # Attach the body of the email
    msg.attach(MIMEText(body, 'html'))

    # Connect to the SMTP server
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)  # Replace with your email provider's SMTP server

    try:
        # Login to your email account
        server.login(credentials["email"], credentials["password"])

        # Send the email
        server.sendmail(credentials["email"], to, msg.as_string())

    except Exception as e:
        print(f"An error occurred: {str(e)}")

    finally:
        # Close the connection to the SMTP server
        server.quit()

    # Return True to indicate the email was sent successfully
    return True


def send_two_factor_auth_code(to, code, op):

    # Determine the email address based on the operation type
    if op == "login":
        email = search_user_by_username(to)[3]
    else:
        email = to["email"]
        to = to["username"]

    # Compose the email body with HTML formatting
    email_body = """
        <html>
        <head>
            <style>
            body {
                font-family: Arial, sans-serif;
                font-size: 14px;
                color: #333;
            }
            h1 {
                color: #007bff;
            }
            p {
                margin-bottom: 10px;
            }
            </style>
        """
    email_body += f"""
        </head>
        <body>
            <h1>Two Factor Authentication Code</h1>
            <p>Hello, {to}</p>
            <p>Your login code is: <strong>{code}</strong></p>
        </body>
        </html>
    """

    # Send the email with the composed body
    send_email(email, "Two Factor Authentication Code", email_body)


def generate_two_factor_auth_code():

    # Generate a random 6-digit code
    return str(random.randint(100000, 999999))


def search_user_by_id(id):

    # Construct the SQL query
    query = "SELECT * FROM users WHERE id = %s"

    # Execute the query and get the result
    result = db_query(query, (id,))

    # If no user is found, return None
    if not result:
        return None

    # Return the user data
    return result[0]


def search_user_by_email(email):

    # Construct the SQL query
    query = "SELECT * FROM users WHERE email = %s"
    
    # Execute the query and get the result
    result = db_query(query, (email,))

    # If no user is found, return None
    if not result:

        return None

    # Return the user data
    return result[0][1]


def search_user_by_username(username):
    # Construct the SQL query
    query = "SELECT * FROM users WHERE username = %s"
    
    # Execute the query and get the result
    result = db_query(query, (username,))

    # If no user is found, return None
    if not result:
        return None

    # Return the user data
    return result[0]


def validate_login(username, password):

    # If username is None, return False (user not found)
    if username is None:
        return False
    else:
        
        # Fetch the user's password
        query = "SELECT password FROM users WHERE username = %s"
        result = db_query(query, (username,))

        # Check if there is a password
        if not result:
            return None
        
        # Check if the provided password matches the user's password
        if result[0][0] == password:

            # Return True to indicate the login has been validated
            return True

        else:
            # Return False to indicate the login credentials aren't valid
            return False


def send_recovery_password(email):

    # Search for the user with the given email
    user = search_user_by_email(email)

    # If user is None, return False (user not found)
    if user is None:

        return False
    else:

        # Extract the username and password from the user
        name = user["username"]
        password = user["password"]

        # Build the HTML body
        HTMLBody = f"""
            <html>
            <head>
                <style>
                body {{
                    font-family: Arial, sans-serif;
                    font-size: 14px;
                    color: #333;
                }}
                h1 {{
                    color: #007bff;
                }}
                p {{
                    margin-bottom: 10px;
                }}
                </style>
            </head>
            <body>
                <h1>Recover Password</h1>
                <p>Hello, {name}</p>
                <p>Your password is: <strong>{password}</strong></p>
            </body>
            </html>
        """

        # Send the recovery email to the user
        send_email(user["email"], "Recover your password", HTMLBody)

        # Return True to indicate the email was sent successfully
        return True


def generate_random_id():
    # Generate a random ID
    random_id = random.randint(100000, 999999)

    # Check if the generated ID already exists, regenerate if necessary
    while check_id_existence(random_id):
        random_id = random.randint(100000, 999999)

    return random_id


def check_id_existence(id):
    result = db_query("SELECT EXISTS(SELECT 1 FROM users WHERE id = %s);", (id,))
    return result[0][0]


def get_id_by_username(username):
    # Construct the SQL query
    query = "SELECT id FROM users WHERE username = %s"

    # Execute the query and get the result
    result = db_query(query, (username,))

    # Check if 
    if result:
        return str(result[0][0])
    else:
        return None



def get_username_by_id(id):
    # Construct the SQL query to retrieve the username
    query = "SELECT username FROM users WHERE id = %s"
    
    # Execute the query and get the result
    result = db_query(query, (id,))

    # Check if the username was found
    if result:

        # If it was, return the username
        return result[0][0]

    else:

        # If it wasn't return None
        return None


def check_image_existence(id):
    directory = os.getcwd()

    # Check if the image file exists
    if not os.path.exists(directory + f"/database/accounts/{id}/{id}.png"):
        return False
    else:
        return True


def csv_to_pdf(username, output_path):

    result = db_query(f'SELECT * FROM "{username}"')
    result.insert(0, ("Data", "descrição", "montante", "Saldo Contabilístico"))
    
    # Set up input and output paths
    input_path = result

    
    # Read the CSV file and convert it to a list of rows
    rows = result

    # Define the table style
    style = TableStyle([
        # Header row style
        ("BACKGROUND", (0, 0), (-1, 0), colors.Color(77/255, 155/255, 75/255)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 14),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        # Data rows style
        ("BACKGROUND", (0, 1), (-1, -1), colors.Color(102/255, 102/255, 102/255)),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.whitesmoke),
        ("ALIGN", (0, 1), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 1, colors.black)
    ])

    # Create the table object
    table = Table(rows)

    # Apply the table style
    table.setStyle(style)

    # Create the PDF document and add the table to it
    doc = SimpleDocTemplate(output_path, pagesize=letter, encoding="utf-8")

    # Create the logo image object
    logo_path = os.getcwd() + f"/static/images/Eco.png"
    logo = Image(logo_path, width=1.5*inch, height=1*inch)

    # Create the username and ID paragraph
    username_style = ParagraphStyle(
        name='UsernameStyle',
        fontName='Helvetica',
        fontSize=12,
        textColor=colors.black,
        alignment=TA_CENTER
    )
    id = search_user_by_username(username)[0]
    username_text = f"{username} ({id})"
    username_para = Paragraph(username_text, username_style)

    # Create the date and time paragraph
    datetime_style = ParagraphStyle(
        name='DateTimeStyle',
        fontName='Helvetica',
        fontSize=12,
        textColor=colors.black,
        alignment=TA_CENTER
    )
    now = datetime.now()
    datetime_text = f"Date: {now.strftime('%d-%m-%Y %H:%M:%S')}"
    datetime_para = Paragraph(datetime_text, datetime_style)

    # Add the logo, spacer, username/ID paragraph, table, and datetime paragraph to the PDF document
    elements = [
        logo,
        Spacer(width=0, height=0.5*inch),
        username_para,
        Spacer(width=0, height=0.2*inch),
        table,
        Spacer(width=0, height=0.2*inch),
        datetime_para
    ]

    doc.build(elements)
    return True


def update_username(id, new_username):

    # Get the old username based on the ID
    old_username = search_user_by_id(id)[1]

    # Build the query to alterate the statement username's table
    alter_query = f'ALTER TABLE "{old_username}" RENAME TO "{new_username}";'

    # Execute the query
    db_query(alter_query)

    # Build the query to update the username in the user's table
    update_query = 'UPDATE users SET username = %s WHERE id = %s'

    # Set the parameters for the query
    update_params = (new_username, id)

    # Execute the query
    db_query(update_query, update_params)


def update_email(id, email):

    # Build the query to update the email in the user's table
    update_query = 'UPDATE users SET email = %s WHERE id = %s'

    # Set the parameters for the query
    update_params = (email, id)

    # Execute the query
    db_query(update_query, update_params)


def update_password(id, password):

    # Build the query to update the password in the user's table
    update_query = 'UPDATE users SET password = %s WHERE id = %s'

    # Set the parameters for the query
    update_params = (password, id)

    # Execute the query
    db_query(update_query, update_params)


def check_username_exists(username):

    # Execute the query to check if the username exists in the user's table
    result = db_query("SELECT exists(select 1 from users where username=%s)", (username,))

    # Return the boolean
    return result[0][0]


def check_email_exists(email):

    #Execute the query to check if the email exists in the user's table
    result = db_query("SELECT exists(select 1 from users where email=%s)", (email,))

    # Return the boolean
    return result[0][0]


def create_user_folder(id):

    # Get the current working directory
    directory = os.getcwd()

    # Create a directory for the user using their ID
    os.mkdir(directory+f"/database/accounts/{id}")

    # Set the paths for the source and destination files
    src_path = directory+f"/static/images/default.png"
    dst_path = directory+f"/database/accounts/{id}/{id}.png"

    # Copy the source file to the destination file
    shutil.copy(src_path, dst_path)


def create_room():

    # Generate a unique room code
    room_code = generate_unique_code(4)

    # Add the rooom to the ROOM table
    db_query("INSERT INTO rooms (code, members, creation) VALUES (%s, %s, TO_CHAR(NOW(), 'DD-MM-YYYY HH24:MI:SS'));",
            (room_code, "[{}]")
    )

    # Create a table for the room
    db_query("""CREATE TABLE IF NOT EXISTS """ + room_code + """ (
            name VARCHAR,
            id INT,
            message VARCHAR,
            time VARCHAR,
            image VARCHAR
    );""")
    
    # Return the generated room code
    return room_code


def get_rooms():

    query = f'SELECT * FROM rooms'
    data = db_query(query)
    
    # Return the data containing all the rooms
    return data[0]


def generate_unique_code(length):

    while True:
        code = ""
        # Generate a code with the specified length
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        # Check if the generated code already exists
        if not check_room_code_exists(code):
            # If the code does not exist, break out of the loop
            break
    
    # Return the unique code
    return code


def check_room_code_exists(code):
    
    # Execute the query to check if the room exists in the rooms table
    result = db_query("SELECT exists(select 1 from rooms where code=%s)", (code,))

    # Return the boolean
    return result[0][0]


def get_room_messages(code):

    # Execute the query to check if the room exists in the specific room(code) table
    result = db_query("SELECT * FROM " + code)
    
    # Iterate over each room in the data
    for message_index in range(len(result)):

        # Convert the set into a array
        message = list(result[message_index])

        # Clean the message using filters
        message[0] = bleach.clean(message[0], tags=[], attributes={})
        message[2] = bleach.clean(message[2], tags=["a", "abbr", "acronym", "b", "blockquote", "code", "em", "i", "li", "ol", "strong", "ul"], attributes={"a": ["href", "title"]})
        message[2] = message[2].replace('\n', '<br>')

        # Set a dictionary with the relevant data to send
        result[message_index] = {"name" : message[0], "id" : message[1], "message" : message[2], "time" : message[3], "image" : message[4]}

    # Return the room messages
    return result


def get_room_members(code):

    # Fetch the existing members array
    result = db_query("SELECT members FROM rooms WHERE code = %s", (code,))

    # Convert the data into a array
    array = list(result[0][0])

    return array


def add_room_member(code, name, id):

    # Set the member's dictionary
    json_member = {
            "name" : name,
            "id" : id
    }

    array = get_room_members(code)

    # Check if there are members in the room
    if len(array[0]) == 0:
        
        # Clean the data format
        array.pop(0)
    
    # Add the user to the members array
    array.append(json_member)

    #Update the members column in the rooms table
    db_query("UPDATE rooms SET members = %s WHERE code = %s", (json.dumps(array, indent=4), code))
    
    return True


def add_room_message(code, content):

    # Execute a query to insert the message into the specific room(code)
    db_query("INSERT INTO " + code + " (name, id, message, time, image) VALUES (%s, %s, %s, %s, %s);",
            (content["name"], content["id"], content["message"], content["time"], content["image"])
    )

    return True


def get_number_of_room_members(code):

    # Fetch the existing members array

    array = get_room_members(code)

    # Check if there are members in the room
    if array:

        # Get number of members
        members_array = array

        # Return number of members
        return len(members_array)

    else:

        # Assume empty
        return 0


def delete_room(code):

    # Delete the specific room(code) table from the database
    db_query("DROP TABLE IF EXISTS " + code + ";")

    # Delete the room row from the rooms talbe
    db_query("DELETE FROM rooms WHERE code = %s;", (code,))



def get_image_path(id):
    # Construct the image path based on the provided user id
    return f"/database/accounts/{id}/{id}.png"


def create_user(username, password, email):
    # Generate a unique user id
    id = str(generate_random_id())

    # Prepare the data to add to the users.json file
    data_to_add = {
        "username": username,
        "password": password,
        "email": email,
        "id": id,
        "active": False,
        "last_activity": None
    }

    # Define the initial coin data for the user
    json_coins = {
            "0.01": 0,
            "0.02": 0,
            "0.05": 0,
            "0.10": 0,
            "0.20": 0,
            "0.50": 0,
            "1.00": 0,
            "2.00": 0,
            "5.00": 0,
            "10.00": 0,
            "20.00": 0,
            "50.00": 0,
            "100.00": 0,
            "200.00": 0
    }

    # Create the table for the statement
    db_query("""CREATE TABLE IF NOT EXISTS """ + username + """ (
            Data VARCHAR,
            descrição VARCHAR, 
            montante VARCHAR, 
            "Saldo Contabilístico" VARCHAR);
    """)
    
    # Add the user to the USER table
    db_query("INSERT INTO users (id, username, password, email, active, last_activity, coins, loans) VALUES (%s, %s, %s, %s, %s, TO_CHAR(NOW(), 'DD-MM-YYYY HH24:MI:SS'), %s, %s);",
            (id, username, password, email, False, json.dumps(json_coins, indent=4), "{}")
    )

    # Create a folder for the user
    create_user_folder(id)

    # Return the created user
    return id


def store_statement(file, filename, ext, id):
    # Save the file to disk
    file_path = os.path.join(os.getcwd(), "database/accounts", id, "uploads", filename)
    
    # Create the directory if it doesn't exist
    if not os.path.exists(os.path.join(os.getcwd(), "database/accounts", id, "uploads")):
        os.makedirs(os.path.join(os.getcwd(), "database/accounts", id, "uploads"))
    
    # Save the file
    file.save(file_path)
    
    # Read the file as Excel or CSV
    if ext == ".xlsx" or ext == ".xls":
        # Convert Excel to CSV
        convert_status = convert_excel_to_csv(file_path)
        os.remove(file_path)
        if convert_status == None:
           return False
        file_path = os.path.splitext(file_path)[0] + ".csv"
    
    # Clean the CSV file
    clean_csv_file(file_path)
    
    # Identify the bank from the statement
    bank = get_statement_bank(file_path)

    if bank != "Santander" and bank != "CGD":

        # Remove the file
        os.remove(file_path)
        return False
    
    # Extract statement data
    username = search_user_by_id(id)[1]
    lst = get_external_statement_data(file_path)
    
    # Define the path for storing bank-specific statement data
    file_path_bank = os.path.join(os.getcwd(), "database/accounts", id, "uploads", bank + ".csv")
    
    if lst != []:
        # Store the statement data in a bank-specific file
        store_external_statement_data(lst, file_path_bank, bank)
    
    if os.path.splitext(file_path)[0] != os.path.splitext(file_path_bank)[0]:
        # Remove the original file
        os.remove(file_path)
    
    # Return statement processing result
    return True


def get_statement_bank(filepath):
    # Read the file as CSV

    lst = read_csv(filepath)
        
    # Iterate over each row in the CSV
    for row in lst:
        # Check for specific keywords to identify the bank
        if "Consultar saldos e movimentos" in row[0]:
            return "CGD"  # If the keyword is found, the bank is CGD
        elif "Listagem de Movimentos" in row[0]:
            return "Santander"  # If the keyword is found, the bank is Santander
    
    # If no bank is identified, return None
    return None


def get_statement_data(username):

    result = db_query(f'SELECT * FROM "{username}"')
    result.insert(0, ("Data", "descrição", "montante", "Saldo Contabilístico"))
    
    return result


def get_external_statement_data(filepath):
    lst = []
    
    # Check if the file exists
    if not os.path.exists(filepath):
        return lst
    
    # Open the file as CSV
    with open(filepath, "r", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        
        # Iterate over each row in the CSV and append it to the list
        for row in reader:
            lst.append(row)
    
    return lst


def store_external_statement_data(lst, filepath, bank):
    # Check if the file exists and remove it if it does
    if os.path.exists(filepath):
        os.remove(filepath)
    
    # Open the file in write mode and create a CSV writer
    with open(filepath, 'w+', newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        
        # Write the header row based on the bank
        if bank == "CGD":
            writer.writerow(["Data", "Descrição", "Montante", "Saldo Contabilístico"])
            lst = lst[7:-1]  # Skip the first 7 rows and the last row
            for element in lst:
                if element[3] != "":
                    element[3] = "-" + element[3]
                else:
                    element[3] = element[4]
                new_lst = [element[1], element[2], element[3], element[6]]
                writer.writerow(new_lst)
        elif bank == "Santander":
            writer.writerow(["Data", "Descrição", "Montante", "Saldo Contabilístico"])
            lst = lst[7:]  # Skip the first 7 rows
            for element in lst:
                element = element[1:]  # Skip the first column
                writer.writerow(element)
 


def clean_platform_csv(id):
    csv_file_path = os.path.join(os.getcwd(), "database/accounts", id, f"{id}.csv")
    
    # Check if the CSV file exists
    if not os.path.exists(csv_file_path):
        return []
    
    # Iterate through each row in the CSV file and append only the necessary columns to the list
    lst = [[row[0], row[1], row[-2], row[-1]] for row in read_csv(csv_file_path)]
    
    if lst != []:
        lst.pop(0)  # Remove the header row
    
    return lst


def foreign_statement(bank, id):
    csv_file_path = os.path.join(os.getcwd(), "database/accounts", id, "uploads", f"{bank}.csv")
    
    # Check if the CSV file exists
    if not os.path.exists(csv_file_path):
        return []
    
    lst = read_csv(csv_file_path)
    
    return lst


def insert_char(string, char, index):
    return string[:index] + char + string[index:]


def calculate_bank_expenses(lst):
    dic = {}  # Dictionary to store expense totals for each description
    expenses = 0  # Total expenses

    for i, element in enumerate(lst):
        # Create a copy of the element
        lst[i] = list(element)
        if "." in lst[i][2] and len(lst[i][2]) > 6:
            lst[i][2] = lst[i][2].replace(".", "")
            lst[i][2] = insert_char(lst[i][2], ".", -2)
        if lst[i][2] != "" and float(lst[i][2]) < 0:
            # Convert the expense amount to positive value
            expense = round(float(lst[i][2]) * -1, 2)
            # Add the expense to the total expenses
            expenses += expense  

            # Update the dictionary with the expense amount for the description
            if lst[i][1] not in dic:
                dic[lst[i][1]] = expense
            else:
                dic[lst[i][1]] += expense
    #print(round(expenses, 2))
    #print(dic)
    return round(expenses, 2), dic


def calculate_bank_profits(lst):
    dic = {}  # Dictionary to store profit totals for each description
    profits = Decimal('0')  # Total profits

    for element in lst:
        element = list(element)
        if "€" in element[2]:
            element[2] = element[2].replace("€", "")
        if "." in element[2] and len(element[2]) > 6:
            element[2] = element[2].replace(".", "")
            element[2] = insert_char(element[2], ".", -2)
        if element[2] != "" and float(element[2]) > 0:
            profit = Decimal(element[2]).quantize(Decimal('0.01'))  # Convert the profit amount to decimal with two decimal places
            profits += profit  # Add the profit to the total profits

            # Update the dictionary with the profit amount for the description
            if element[1] not in dic:
                dic[element[1]] = profit
            else:
                dic[element[1]] += profit

    return round(profits, 2), dic


def read_csv_statement_file(filepath):

    lst = read_csv(filepath)

    return lst[1:]  # Return all rows except the header (skipping the first row)


def get_expenses(id):

    # Check if CGD bank statement exists for the given ID
    if check_bank_statement_exists("CGD", id):

        # Read the CSV statement file
        cgd = read_csv_statement_file(os.getcwd()+f"/database/accounts/{id}/uploads/CGD.csv")

    else:

        # No CGD bank movements
        cgd = []

    # Check if Santander bank statement exists for the given ID
    if check_bank_statement_exists("Santander", id):

        # Read the CSV statement file
        santander = read_csv_statement_file(os.getcwd()+f"/database/accounts/{id}/uploads/Santander.csv")

    else:

        # No Santander bank movements
        santander = []

    # Get the username based on the ID
    username = search_user_by_id(id)[1]

    # Get ECO statement data from the user's ECO statement
    eco_statement = get_statement_data(username)

    # For each index of each row in ECO statement
    for i, element in enumerate(eco_statement):

        # Create a copy of the element as an array
        eco_statement[i] = list(element)

        # Remove currency symbols from the ECO statement
        eco_statement[i][-1] = eco_statement[i][-1].replace("€", "").strip()
        eco_statement[i][-2] = eco_statement[i][-2].replace("€", "").strip()

    # Calculate expenses for CGD, Santander and Eco statements as Value, Dictionary
    eco_expenses, eco_dic_expenses = calculate_bank_expenses(eco_statement[1:])
    expenses_cgd, expenses_dic_cgd = calculate_bank_expenses(cgd)
    expenses_santander, expenses_dic_santander = calculate_bank_expenses(santander)

    # Calculate the value of the total expenses
    expenses = round(expenses_cgd + expenses_santander + eco_expenses, 2)

    # Merge dictionaries of expenses from each bank
    expenses_dic = expenses_dic_cgd | expenses_dic_santander | eco_dic_expenses

    # Filter and sort the dictionary of expenses
    expenses_dic = filter_operations(expenses_dic)
    expenses_dic = dict(sorted(expenses_dic.items(), key=lambda x: x[1], reverse=True))

    # Return the Value, Dictionary
    return str(expenses) + " €", expenses_dic


def get_profits(id):

    # Check if CGD bank statement exists for the given ID
    if check_bank_statement_exists("CGD", id):

        # Read the CSV statement file
        cgd = read_csv_statement_file(os.getcwd()+f"/database/accounts/{id}/uploads/CGD.csv")

    else:

        # No CGD bank movements
        cgd = []

    # Check if Santander bank statement exists for the given ID
    if check_bank_statement_exists("Santander", id):

        # Read the CSV statement file
        santander = read_csv_statement_file(os.getcwd()+f"/database/accounts/{id}/uploads/Santander.csv")

    else:

        # No Santander bank movements
        santander = []

    # Get the username based on the ID
    username = search_user_by_id(id)[1]

    # Get ECO statement data from the user's ECO statement
    eco_statement = get_statement_data(username)

    # For each index of each row in ECO statement
    for i, element in enumerate(eco_statement):

        # Create a copy of the element as an array
        eco_statement[i] = list(element)

        # Remove currency symbols from the ECO statement
        eco_statement[i][-1] = eco_statement[i][-1].replace("€", "").strip()
        eco_statement[i][-2] = eco_statement[i][-2].replace("€", "").strip()

    # Calculate revenues for CGD, Santander and Eco statements as Value, Dictionary
    eco_profits, eco_dic_profits = calculate_bank_profits(eco_statement[1:])
    profits_cgd, profits_dic_cgd = calculate_bank_profits(cgd)
    profits_santander, profits_dic_santander = calculate_bank_profits(santander)

    # Calculate the value of the total revenues
    profits = round(profits_cgd + profits_santander + eco_profits, 2)

    # Merge dictionaries of expenses from each bank
    profits_dic = profits_dic_cgd | profits_dic_santander | eco_dic_profits

    # Filter and sort the dictionary of revenues
    profits_dic = filter_operations(profits_dic)
    profits_dic = dict(sorted(profits_dic.items(), key=lambda x: x[1], reverse=True))

    # Return the Value, Dictionary
    return str(profits) + " €", profits_dic


def check_bank_statement_exists(bank, id):
    filepath = os.getcwd() + f"/database/accounts/{id}/uploads/{bank}.csv"
    return os.path.exists(filepath)


def filter_operations(dic):
    # Retrieve categories
    dic_options = dict(db_query("""SELECT * FROM categories;"""))
    
    if dic_options == None:
        dic_options = {}
    
    dic_operations = {}
    
    for element in dic_options:
        dic_operations.setdefault(element, 0)
    dic_operations.setdefault("Outros", 0)

    # Initialize a new dictionary to store the categorized operation values
    new_dic = {}

    # Iterate over each element in the input dictionary
    for element in dic:
        # Convert the value to decimal with two decimal places
        valor = Decimal(dic[element]).quantize(Decimal('0.01'))

        # Extract the first two words from the element
        element = element.split(" ")[:2]

        # Convert the first word to uppercase
        upper_element_1 = element[0].upper()

        # Join the words back into a string
        element = " ".join(element)

        # Convert the joined element to uppercase
        upper_element_join = element.upper()

        # Check if the element matches any of the keywords for each category
        for category in dic_options:
            if upper_element_1 in dic_options[category] or upper_element_join in dic_options[category]:
                # If a match is found, add the value to the corresponding category
                dic_operations[category] += valor
                break
        else:
            # If no match is found, add the value to the "Outros" category
            dic_operations["Outros"] += valor

    # Iterate over each element in the categorized operation dictionary
    for element in dic_operations:
        if dic_operations[element] != 0:
            # If the value is not zero, add it to the new dictionary
            new_dic[element] = dic_operations[element]

    # Return the new dictionary with categorized operation values
    return new_dic


def get_pizza_info(dic, id, page):

    # Extract keys and values from the dictionary
    keys = list(dic.keys())
    values = list(dic.values())
    
    # Convert values to floats using Decimal
    values = [float(Decimal(str(value))) for value in values]

    # Define the minimum size for a slice
    min_size = 1

    # Filter out values below the minimum size
    total_sum = sum(values)

    if total_sum != 0:

        filtered_values, filtered_keys = zip(*filter(lambda x: 100 * x[0] / total_sum >= min_size, zip(values, keys)))

    else:

        # If all values are zero, create a slice with default values
        filtered_values = [1]
        filtered_keys = ["Sem dados"]

    # Create a pie chart with the dictionary information
    fig, ax = plt.subplots()
    wedges, _, autotexts = ax.pie(filtered_values, autopct='%1.1f%%', textprops={'color': 'black'})

    # Add labels for each slice
    for i, val in enumerate(filtered_values):

        angle = 2 * np.pi * (sum(filtered_values[:i]) + val / 2) / sum(filtered_values)
        x, y = np.cos(angle), np.sin(angle)
        text = '{}'.format(filtered_keys[i])

        # Add the label with a line pointing to the slice
        ax.annotate(text, xy=(x, y), xytext=(x*1.34, y*1.34), fontsize=10,
                    ha='center', va='center', arrowprops=dict(arrowstyle='-', color=(77/255, 155/255, 75/255)))

        # Reduce the font size of the slice percentages
        autotexts[i].set_fontsize(8)

    # Set the color of the lines and text
    for w in wedges:

        w.set_edgecolor("none")

    for t in ax.texts:

        if t not in autotexts:
            t.set_color("white")

    plt.axis('equal')

    # Create the directory if it doesn't exist
    dir_path = os.path.join(os.getcwd(), f"database/accounts/{id}/analysis")
    os.makedirs(dir_path, exist_ok=True)

    # Save the figure in the directory
    filename = f"{page}.png"
    filepath = os.path.join(dir_path, filename)
    plt.savefig(filepath, format='png', transparent=True)

    # Clear the plot to free up memory
    plt.clf()

    return filepath


def generate_economic_report(output_path, image_paths, id, dic_profits_expenses, expenses_dic, profits_dic):

    # Check if there is a pie chart directory
    if image_paths[-1] == None:

        # Remove the pie chart directory
        image_paths.pop(-1)

    # Reverse the array with the paths of the images of the economical analysis
    image_paths = image_paths[::-1]

    # Traverse the revenues/expenses dictionary
    for value in dic_profits_expenses.values():

        # Add the currency symbol
        value = str(value) + " €"
    
    # Traverse the expenses dictionary
    for value in expenses_dic.values():

        # Add the currency symbol
        value = str(value) + " €"
    
    # Traverse the revenues dictionary
    for value in profits_dic.values():

        # Add the currency symbol
        value = str(value) + " €"

    # Create the PDF document and add the table to it

    # Define the margins of the page
    left_margin = 0.2 * inch    # Left margin in inches
    right_margin = 0.2 * inch   # Right margin in inches
    top_margin = 0.2 * inch     # Top margin in inches
    bottom_margin = 0.2 * inch  # Bottom margin in inches

    # Create the SimpleDocTemplate object with the costum margins
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin,
        encoding="utf-8"
    )


    # Create the username and ID paragraph
    username_style = ParagraphStyle(
        name='UsernameStyle',
        fontName='Helvetica',
        fontSize=12,
        textColor=colors.black,
        leading=inch * 2,  # Spacing between the lines
        alignment=1  # Value 1 to center the text
    )

    datetime_style = ParagraphStyle(
        name='DateTimeStyle',
        fontName='Helvetica',
        fontSize=11,
        textColor=colors.black,
        alignment=1  # Value 1 to center the text
    )

    # Add the username/ID paragraph to the PDF document
    username = search_user_by_id(id)[1]
    username_text = f"{username} ({id})"
    username_para = Paragraph(username_text, username_style)

    elements = []

    # FIRST PAGE

    # Calculate the vertical position for centering horizontally
    cover_text_height = username_para.wrapOn(doc, doc.width, doc.height)[1]
    vertical_position = (doc.height - cover_text_height) / 2

    # Add vertical spacing to position the text in the center
    elements.append(Spacer(width=0, height=vertical_position))

    # Create the logo image object
    logo_path = os.getcwd() + "/static/images/Eco.png"
    logo = Image(logo_path, width=1.5*inch, height=1*inch)

    elements.append(logo)
    elements.append(Spacer(width=0, height=2.5*inch))
    elements.append(username_para)

    # Create the date and time paragraph
    now = datetime.now()
    datetime_text = f"{now.strftime('%d-%m-%Y')}"
    datetime_para = Paragraph(datetime_text, datetime_style)
    elements.append(datetime_para)

    # FOLLOWING PAGES
    dic_names = {"Expenses": "Despesas", "Profits": "Receitas", "Statement": "Geral", "Eco_Chart": "Saldo Eco"}

    # Create the logo image objects with colored background
    for path in image_paths:

        name = os.path.splitext(os.path.basename(path))[0].title()

        # Create the image and apply the colored background to the table cell
        image = Image(path, width=6.5*inch, height=5*inch)
        image_data = [[image]]

        # Define a colored background for the image cell
        bg_color = Color(52/255, 53/255, 65/255, alpha=1)
        image_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg_color),
        ])
        image_table = Table(image_data, style=image_style)

        elements.append(PageBreak())
        # Add custom cover page

        # Add text to cover page
        cover_text = dic_names[name]
        cover_text_style = ParagraphStyle(
            name='CoverTextStyle',
            fontName='Helvetica',
            fontSize=24,
            textColor=colors.black,
            leading=inch * 2,  # Spacing between the lines
            alignment=1  # Value 1 to center the text
        )
        cover_text_para = Paragraph(cover_text, cover_text_style)

        # Calculate the vertical position for centering horizontally
        cover_text_height = cover_text_para.wrapOn(doc, doc.width, doc.height)[1]
        vertical_position = (doc.height - cover_text_height) / 2

        # Add vertical spacing to position the text in the center
        elements.append(Spacer(width=0, height=vertical_position))
        elements.append(cover_text_para)
        elements.append(PageBreak())

        if name == "Statement":

            # Create the table for the first dictionary data
            elements.append(Spacer(width=0, height=1*inch))
            table_data1 = [[str(key), str(value)] for key, value in dic_profits_expenses.items()]
            table1 = Table(table_data1, colWidths=[200, 200])
            table1.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND', (0, 0), (0, -1), (77/255, 155/255, 75/255)),  # Define the left column with a background color
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center the data and header
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),  # Define the font for the header
                ('FONTSIZE', (0, 0), (0, -1), 12),  # Define the size of the header's font
            ]))
            elements.append(Spacer(width=0, height=vertical_position-250))
            elements.append(table1)

        elif name == "Expenses":

            # Create the table for the second dictionary data
            elements.append(Spacer(width=0, height=1*inch))
            table_data2 = [["Despesa", "Montante"]] + [[str(key), str(value)] for key, value in expenses_dic.items()]
            table2 = Table(table_data2, colWidths=[200, 200])
            table2.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND', (0, 0), (-1, 0), (77/255, 155/255, 75/255)),  # Define the left column with a background color
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center the data and header
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Define the font for the header
                ('FONTSIZE', (0, 0), (-1, 0), 12),  # Define the size of the header's font
            ]))
            elements.append(Spacer(width=0, height=vertical_position-200))
            elements.append(table2)
            elements.append(Spacer(width=0, height=0.1*inch))
            elements.append(PageBreak())
        elif name == "Profits":

            # Create the table for the third dictionary data
            elements.append(Spacer(width=0, height=1*inch))
            table_data3 = [["Receita", "Montante"]] + [[str(key), str(value)] for key, value in profits_dic.items()]
            table3 = Table(table_data3, colWidths=[200, 200])
            table3.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND', (0, 0), (-1, 0), (77/255, 155/255, 75/255)),  # Define the left column with a background color
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center the data and header
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Define the font for the header
                ('FONTSIZE', (0, 0), (-1, 0), 12),  # Define the size of the header's font
            ]))
            elements.append(Spacer(width=0, height=vertical_position-200))
            elements.append(table3)
            elements.append(Spacer(width=0, height=0.1*inch))
            elements.append(PageBreak())

        if path != image_paths[0]:

            # Add vertical spacing to position the image in the center
            elements.append(Spacer(width=0, height=vertical_position-150))

        elements.append(Spacer(width=0, height=0.3*inch))
        elements.append(image_table)

    doc.build(elements)

    return True


# This function saves a image into the user's folder
def save_image(image_data_url, id):
    
    try:

        # Remove the "data:image/png;base64," prefix from the data URL
        base64_data = image_data_url.split(',')[1]

        # Decode the base64 image data
        image_data = base64.b64decode(base64_data)

        # Specify the directory to save the image
        save_directory = os.path.join(os.getcwd(), 'database', 'accounts', id, "analysis")

        # Create the directory if it doesn't exist
        os.makedirs(save_directory, exist_ok=True)

        # Generate a unique filename for the image (e.g., using a timestamp)
        filename = 'ECO_chart.png'  # Replace with your preferred filename logic

        # Save the image to the specified directory
        save_image_db_coordinator(os.path.join(save_directory, filename), image_data)

        # Return 'success' to indicate the image was successfully saved
        return 'success'

    except:
        
        # If something goes wrong, return 'error' to indicate the image wasn't saved
        return 'error'
