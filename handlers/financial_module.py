import csv
from handlers.db_coordinator import *
from handlers.processing_handlers import *
from datetime import datetime, timedelta
from flask import jsonify


def banking_operations(id, operation, coin, amount):

    # Fetch the coins that the user owns from the database
    coinAmounts = db_query("SELECT coins FROM users WHERE id = " + id)
    coins = db_query("SELECT * FROM coin_valuation")

    dic = {}
    # estao a ser removidos itens duplicados nos sets, ao escrever na base de dados,
    # estao a ser removidos e adicionados dados com origem desconhecida

    for element in coins:
        lst = list(element)
        lst[0] = lst[0].replace('€', '')
        dic.setdefault(lst[0], lst[1])

    data = [dict(coinAmounts[0][0]), dic]

    # Convert amount to integer and coin to a formatted string with 2 decimal places
    amount = int(amount)
    coin = "{:.2f}".format(float(coin))

    if operation == "deposit":
        # Perform deposit operation
        for coin_ in data[0]:
            if coin_ == str(coin):
                if register_operation(id, operation, coin, amount, data):
                    data[0][coin] = data[0][coin] + amount
                    query = 'UPDATE users SET coins = %s WHERE id = %s'
                    params = (json.dumps(data[0], indent=4), id)
                    db_query(query, params)
                    break
                else:
                    return False
    elif operation == "withdrawl":
        # Perform withdrawal operation
        for coin_ in data[0]:
            if coin_ == str(coin) and data[0][coin] >= amount and amount > 0:
                if register_operation(id, operation, coin, amount, data):
                    data[0][coin] = data[0][coin] - amount
                    query = 'UPDATE users SET coins = %s WHERE id = %s'
                    params = (json.dumps(data[0], indent=4), id)
                    db_query(query, params)
                    break
                else:
                    return False

    # Return True to indicate the operation was successful
    return True


def register_operation(id, operation, coin, amount, data):

    # Get the current account balance
    accountBalance = get_account_balance(data)
    print(accountBalance)

    try:
        # Check if the statement file exists and create it if necessary
        total = float(coin) * float(amount)

        if operation == "deposit":
            # Update account balance for a deposit
            accountBalance += total
        elif operation == "withdrawl":
            # Update account balance for a withdrawal
            accountBalance -= total
            total = -total
        else:
            # Invalid operation
            return False

        username = search_user_by_id(id)[1]

        tuple_to_insert = (
            datetime.now().strftime('%d-%m-%Y'),
            operation.title(),
            "{:.2f}".format(total) + " €",
            "{:.2f}".format(accountBalance) + " €"
        )

        query = f'INSERT INTO "{username}" ("Data", "descrição", "montante", "Saldo Contabilístico") VALUES (%s, %s, %s, %s);'
        db_query(query, tuple_to_insert)

        return True

    except:
        # An error occurred
        return False


def get_statement(id):

    # Get username based on the ID
    username = search_user_by_id(id)[1]

    # Build the query
    query = f'SELECT * FROM "{username}"'

    # Execute the query and retrieve the statement data
    data = db_query(query)

    return data[0]

def get_account_balance(data):

    # Initialize the total balance
    total = 0

    # Calculate the total balance by multiplying the coin amounts with their respective values
    for coin_, amount in data[0].items():
        total += float(amount) * float(data[1][coin_])

    # Return the total account balance
    return total


def get_date_balance(id):
    
    username = search_user_by_id(id)[1]
    
    query = f'SELECT * FROM "{username}"'
    data = db_query(query)

    dic = {}
    if len(data) > 0:

        # Traverse the inverted array and set {key : value} elements in the dictionary
        for row in data:
            dic[row[0]] = row[3]

    return dic