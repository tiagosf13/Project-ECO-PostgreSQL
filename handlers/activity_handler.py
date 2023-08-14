from handlers.processing_handlers import *


def set_activity_timer(id):

    # Construct the SQL query
    query = "UPDATE users SET last_activity = TO_CHAR(NOW(), 'DD-MM-YYYY HH24:MI:SS') WHERE id = %s"
    
    # Execute the query using db_querie function
    db_query(query, (id,))



def last_activity_check(id):

    # Construct the SQL query to retrive the user's last recorded activity
    query = "SELECT id, last_activity FROM users WHERE id = %s AND last_activity IS NOT NULL"
    
    # Execute the query and get the result
    result = db_query(query, (id,))

    # Check if there a last recorded activity
    if not result:

        # If not, return False to indicate the user's session has expired
        return False

    # Set the user's ID, last recorded activity and username
    user_id, last_activity_str = result[0]
    username = get_username_by_id(id)
    
    # Format the user's last recorded activity
    last_activity = datetime.strptime(last_activity_str, "%d-%m-%Y %H:%M:%S")

    # Get the current date and time
    now = datetime.now()

    # Calculate the difference between them
    difference = now - last_activity

    # Check if the difference is greater than 10 minutes and if the user is still marked as online
    if difference.total_seconds() > 600 and check_if_online(username):

        # If the difference is greater than 10 minutes and the user is marked as online, inactivate him
        inactivate_user(id)

        # Return False to indicate the user's last recorded activity has expired
        return False

    elif not check_if_online(username):

        # If the user is marked has offline, return False to indicate the user's last recorded activity has expired
        return False

    else:

        # If the difference is less than 10 minutes and the user is still marked as online, set a new last recorded activity
        set_activity_timer(id)

        # Return True to indicate the user's last recorded activity is valid
        return True



def check_if_online(username):

    # Construct the SQL query
    query = "SELECT active FROM users WHERE username = %s"
    
    # Execute the query using db_querie function
    result = db_query(query, (username,))
    
    # Check if any rows were returned
    if result:

        # Return the value of the "active" column
        return result[0][0]

    else:

        return None


def inactivate_user(id):

    try:

        # Construct the SQL query
        query = "UPDATE users SET active = False WHERE id = %s"
    
        # Execute the query
        db_query(query, (id,))
        
        # Return True to indicate a successfull inactivation
        return True

    except:

        # Return False to indicate a unsuccessfull inactivation
        return False



def activate_user(id):

    try:

        # Construct the SQL query
        query = "UPDATE users SET active = True WHERE id = %s"
    
        # Execute the query
        db_query(query, (id,))
        
        # Return True to indicate a successfull inactivation
        return True

    except:

        # Return False to indicate a unsuccessfull inactivation
        return False