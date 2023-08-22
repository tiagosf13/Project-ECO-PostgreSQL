from time import localtime, strftime
import time
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session, send_file, send_from_directory
from handlers.processing_handlers import *
from handlers.activity_handler import *
from handlers.financial_module import *
from flask_socketio import send, leave_room, join_room
from werkzeug.utils import secure_filename




views = Blueprint(__name__, "views")


# This view returns the home page
@views.route("/")
def index():

    return render_template("index.html")


# This view returns a JSON object with the {Date : Balance}
# The JSON is used to build a line graphic with the evolution of the user's Balance
@views.route('/dados_saldo/<id>')
def get_dados_saldo(id):

    # Verify if the user session expired or not
    if last_activity_check(id):

        # If the session is valid, fetch the data
        dic = get_date_balance(id)


        # Initialize the array to store and send the data into a JSON object
        dados = []

        # For each bank operation, insert the {Date : Balance} into the array
        for data, saldo in dic.items():
            dados.append({
                'data': data,
                'saldo': saldo
            })

        # Send the data as JSON
        return jsonify(dados)

    else:

        # If the session isn't valid, return to the home page
        return redirect(url_for("views.index"))


# This view saves the line graphic with the evolution of the user's Balance
@views.route('/save-graphic/<id>', methods=['POST'])
def save_graphic(id):

    # Verify if the user session expired or not
    if last_activity_check(id):

        # Receive the image URL from the JavaScript of the Statement view
        image_url = request.json.get('imageUrl')

        # Save the image to the user's folder
        operation_status = save_image(image_url, id)

        # Return a JSON object to indicate 
        return jsonify({'status': operation_status})

    else:

        # If the session isn't valid, return to the home page
        return redirect(url_for("views.index"))


# This view is used to present the profile page to the user
@views.route("/profile/<username>")
def profile(username):

    # If no username is presented, retrieve it from the previous view
    if not username:
        username = request.referrer.split("/")[-1]

    # If the user is online, get the user's ID
    id=get_id_by_username(username)

    # Check if the user is online, the ID was found and the last recorded activity is valid
    if check_if_online(username) == True and id != None and last_activity_check(id):

        # Check if the user's profile photo exists
        if check_image_existence(id):

            # If the user's profile photo exists, return the user's ID to use the photo in the profile page
            return render_template("profile.html", name=username, id=id, image_number = id)

        else:

            # If the user's profile photo doesn't exist, return the default photo to be used in the profile page
            return render_template("profile.html", name=username, id=id, image_number = "default")

    # If user isn't online or the ID wasn't found or his last recorded activity has expired, return to the home page
    return redirect(url_for("views.index"))


# This view fetches the user's amount of coins and the valuation of the coins
# The retrieved information is sent has a JSON object
@views.route("/data/<id>")
def get_data(id):

    # Check if the last recorded activity is valid
    if last_activity_check(id):

        # Use db_query to fetch the user's coins and there valuation from the database
        coinAmounts = db_query("SELECT coins FROM users WHERE id = " + id)
        coins = db_query("SELECT * FROM coin_valuation")

        # If the information was fetched successfully
        if coinAmounts and coins:

            # Return the fetched data as JSON
            return jsonify({"coinAmounts" : coinAmounts[0][0], "coins": coins})

    # If the last recorded activity has expired or the information wasn't fetched successfully, return to the home page
    return redirect(url_for("views.index"))


# This view points to the home page
@views.route("/go-to-home")
def go_to_home():

    return redirect(url_for("views.index"))


# This view fetches the user's loan data
# The data will be displayed in a calendar
@views.route("/calendar/<id>")
def calendar(id):

    # Use db_query to fetch the user's loans
    dic = db_query("SELECT loans FROM users WHERE id = " + id)

    # Return a array with with the user's loans [{date : loan}]
    return dic[0][0]


# This view returns the login 2FA page
@views.route("/two-factor-auth-login/<username>", methods=["GET", "POST"])
def two_factor_auth_login(username):

    # Get the 2FA code that was set in the login session
    code = session.get("code")

    if code is None:
        return redirect(url_for("views.login"))
    
    # Fetch the user's data from the database using username
    user_data = db_query("SELECT id, active FROM users WHERE username = %s", (username,))
    
    # Check if user data was retrieved
    if user_data:

        # Set the user's ID
        user_id= user_data[0][0]

        # Check if the requested method is POST
        if request.method == "POST":

            # Retrieve the 2FA code inserted by the user
            entered_code = request.form.get("code")

            # If the entered 2FA code equals the 2FA that was sent to the user
            if entered_code == code:

                # Update user's active status
                db_query("UPDATE users SET active = %s WHERE id = %s", (True, user_id))

                # Update the user's last recorded activity in the database
                set_activity_timer(user_id)

                # Set the session username and ID in the session
                session["username"] = username
                session["id"] = user_id

                # Return the profile page
                return redirect(url_for("views.profile", username=username))
            
        # If the requested method isn't POST, return the 2FA login page
        return render_template("two-factor-auth-login.html", username=username)
    
    # If the user's data wasn't retrieved, return the login page
    return redirect(url_for("views.login"))


# This view returns the signup 2FA page, with the goal of verifying the user's email
@views.route("/two-factor-auth-signup/", methods=["GET", "POST"])
def two_factor_auth_signup():

    # Get the 2FA code, password, username and email that were set in the signup session
    code = session.get("code_signup")
    password = session.get("password_signup")
    username = session.get("username_signup")
    email = session.get("email_signup")

    if code is None:
        return redirect(url_for("views.login"))

    # Check if the requested method is POST
    if request.method == "POST":

        # Retrieve the 2FA code inserted by the user
        entered_code = request.form.get("code_signup")

        # If the entered 2FA code equals the 2FA that was sent to the user
        if entered_code == code:

            # Create the user in the database
            create_user(username, password, email)

            # Return the login page
            return redirect(url_for("views.login", username=username))

    # If the requested method isn't POST, return the 2FA login page
    return render_template("two-factor-auth-signup.html")


# This view returns the login page
@views.route("/login", methods=["GET", "POST"])
def login():

    # Check if the requested method is POST
    if request.method == "POST":

        # Get the password and username and email that were set in the signup session
        username = request.form.get("username")
        password = request.form.get("password")

        # Check if the username has a space
        if " " in username and len(username.split(" ")) == 2:

            # Merge the string into one username
            username = username.replace(" ", "")

        # Check if the username inserted is a email
        if "@" in username:

            # Search the username based on the email
            username = search_user_by_email(username)

        # Check if the login credentials are valid
        if validate_login(username, password) == True:

            # Generate a 2FA login code
            code = generate_two_factor_auth_code()

            # Set the code, username and ID in the session
            session["code"] = code
            session["username"] = username
            session["id"] = get_id_by_username(username)

            # Check if the last recorded activity is valid
            if last_activity_check(session["id"]):

                # Skip the 2FA login page and return the profile page
                return redirect(url_for("views.profile", username=username))

            else:

                # Sent the 2FA login code to the user's email
                send_two_factor_auth_code(username, code, "login")

            # Return the 2FA login page
            return redirect(url_for("views.two_factor_auth_login", username = username))


    # If the requested method isn't POST or the login credentials aren't valid
    return render_template("login.html")


# This view has the goal of logging out the user, returning him to the home page
@views.route("/logout/<name>", methods=["POST", "GET"])
def logout(name):

    # Get the user's ID based on the username
    id = get_id_by_username(name)

    # Check if the last recorded activity is valid
    if last_activity_check(id):

        # If the las recorded activity is valid, check if the inactivation of the user is successfull
        if inactivate_user(id):

            # If successful, clear the session
            session.clear()

            # Return the home page
            return redirect(url_for("views.index"))
        else:

            # If unsuccessfull, return the profile page
            return redirect(url_for("views.profile", username=name))
    else:

        # Return the home page if the last recorded activity has expired
        return redirect(url_for("views.index"))


# This view is used to let the user recorver he's password
@views.route("/recover-password", methods=["GET", "POST"])
def recover_password():

    # Check if the requested method is POST
    if request.method == "POST":

        # Get the user's email from the request
        email = request.form.get("email")

        # Get the username based on the email
        user = search_user_by_email(email)

        # Check if the user exists
        if user is None:

            # If the user doesn't exist, return the signup page
            return redirect(url_for("views.signup"))

        else:
            
            # Send recovery password to the user's email
            send_recovery_password(email)

            # Return the login page
            return redirect(url_for("views.login"))
    else:

        # If it isn't, return the same page
        return render_template("recover-password.html")


# This view is used to enroll new users into the platform
@views.route("/signup", methods=["GET", "POST"])
def signup():

    # Check if the requested method is POST
    if request.method == "POST":

        # Get the username, password and email from the request
        username = request.form.get("username")
        password = request.form.get("password")
        email = request.form.get("email")

        # Check if there is no user in the database using the same email or the same username
        if search_user_by_email(email) != None or search_user_by_username(username) != None:

            # Return signup page if there is
            return render_template("signup.html", message="User already exists.")

        else:
            
            # Generate a 2FA signup code to verify if the email is correct
            code = generate_two_factor_auth_code()

            # Set the 2FA signup code, username, email and password to the signup session
            session["code_signup"] = code
            session["username_signup"] = username
            session["email_signup"] = email
            session["password_signup"] = password

            # Create the dictionary with the data to send in the email
            content = {"username": username, "email": email}

            # Send the 2FA signup email
            send_two_factor_auth_code(content, code, "signup")

            # Return the 2FA signup page, in order to validate the email
            return redirect(url_for("views.two_factor_auth_signup"))

    else:

        # If the request methos isn't POST, return the same page
        return render_template("signup.html")


# This view is used to deposit coins into the user's account
# Possible Origin of errors!!
@views.route("/deposit/<name>", methods=["POST", "GET"])
def deposit(name):

    # Check if the last recorded activity is valid
    if last_activity_check(get_id_by_username(name)) is False:

        # If not, return the home page
        return redirect(url_for("views.index"))

    else:

        # Update the user's last recorded activity in the database
        set_activity_timer(get_id_by_username(name))

        # Get the type of coin and the respective amount from the request
        coin = request.form.get("coin-deposit")
        amount = request.form.get("amount-deposit")

        # Check the spelling on the coin type
        if "," in coin:

            # Correct the spelling on the coin type
            coin = coin.replace(",", ".")

        # Deposit the respective amounts of coins into the user's account
        banking_operations(get_id_by_username(name), "deposit", coin, amount)

        # Return the profile page
        return redirect(url_for("views.profile", username=name))


# This view is used to withdraw coins from the user's account
@views.route("/withdrawl/<name>", methods=["POST", "GET"])
def withdrawl(name):

    # Check if the last recorded activity is valid
    if last_activity_check(get_id_by_username(name)) is False:

        # Return the home page
        return redirect(url_for("views.index"))

    else:

        # Update the user's last recorded activity in the database
        set_activity_timer(get_id_by_username(name))

        # Get the type of coin and the respective amount from the request
        coin = request.form.get("coin-withdrawl")
        amount = request.form.get("amount-withdrawl")

        # Check the spelling on the coin type
        if "," in coin:

            # Correct the spelling on the coin type
            coin = coin.replace(",", ".")
        
        # Withdraw the respective amounts of coins into the user's account
        banking_operations(get_id_by_username(name), "withdrawl", coin, amount)
        
        # Return the profile page
        return redirect(url_for("views.profile", username=name))


# This view is used to download the ECO Statement of the user
@views.route("/download_pdf/<id>")
def download_pdf(id):

    # Check if the last recorded activity is valid
    if last_activity_check(id) is False:

        # Return the home page
        return redirect(url_for("views.index"))

    else:

        # Update the user's last recorded activity in the database
        set_activity_timer(id)

        # Get the username based on the ID
        username = search_user_by_id(id)[1]

        # Set the file name to be downloaded
        filename = os.getcwd()+f"/database/accounts/{id}/{id}.pdf"

        # Convert the CSV statement in a PDF file
        csv_to_pdf(username, filename)

        # Prepare the file to be sent
        response = send_file(filename, as_attachment=True)
        response.headers['Content-Disposition'] = f'attachment; filename=ECO_Statement_{username}.pdf'

        # Send the file to be downloaded
        return response


# This view is used to return the statement page with the respective economical analysis,
# or to retrieve a external statement
@views.route("/statement/<name>", methods=["POST", "GET"])
def statement(name):

    # Get the ID based on the username
    id = get_id_by_username(name)

    # Check if the last recorded activity is valid
    if last_activity_check(id) is False:

        # Return the home page
        return redirect(url_for("views.index"))

    else:

        # Update the user's last recorded activity in the database
        set_activity_timer(id)

        # Check if the requested method is POST (it means it's a upload) or GET (retrieve the economical analysis)
        if request.method == "POST":

            # Get the statement from the request
            file = request.files["file"]

            # Get the name of the statement
            filename = secure_filename(file.filename)

            # Get the statement extension
            ext = os.path.splitext(filename)[1].lower()

            # Check if the statement is a Excel or CSV file
            if ext == ".xlsx" or ext == ".csv" or ext == ".xls":

                # Store the statement into the user's account and get the store status
                store_status = store_statement(file, filename, ext, id)

                # Check if the store of the statement was unsuccessfull
                if not store_status:

                    # Return the appropriate error message as a JSON object
                    return jsonify({"status": "error", "message": "Erro ao armazenar arquivo. Só são aceites extratos do Santander e Caixa Geral de Depósitos."})
            
            else:

                # Return the appropriate error message as a JSON object
                return jsonify({"status": "error", "message": "Por favor, selecione um arquivo Excel ou CSV."})

            # Return a success response as a JSON object
            return jsonify({"status": "success", "message": "Arquivo submetido com sucesso!"})

        elif request.method == "GET":

            # Get the value of the user's expenses
            expenses= get_expenses(id)[0]

            # Get the value of the user's revenues
            profits= get_profits(id)[0]

            # Create the dictionary with the data to create the pie chart
            dic = {"Despesas": Decimal(expenses.split("€")[0]).quantize(Decimal('0.01')), "Receitas": Decimal(profits.split("€")[0]).quantize(Decimal('0.01'))}
            
            # Create the pie chart
            get_pizza_info(dic, id, "statement")

            # Return the statement page
            return render_template("statement.html", username=name, id=get_id_by_username(name))

        else:

            # Return the profile page
            return redirect(url_for("views.profile", username=name))


# This view is used to download the general economic report of the user
@views.route("/download_economic_report/<id>")
def download_economic_report(id):

    # Check if the last recorded activity is valid
    if last_activity_check(id) is False:

        # Return the home page
        return redirect(url_for("views.index"))

    else:

        # Update the user's last recorded activity in the database
        set_activity_timer(id)

        # Set the output file path
        output = os.getcwd()+f"/database/accounts/{id}/analysis/economic_report.pdf"

        # Set the pie chart directory
        chart_dir = os.getcwd()+f"/database/accounts/{id}/analysis/ECO_chart.png"

        # Check if the pie chart directory exists
        if not os.path.exists(chart_dir):

            # Nonexistent pie chart
            chart_dir = None

        # Create a array with the paths of the images of the economical analysis
        image_paths = [os.getcwd()+f"/database/accounts/{id}/analysis/expenses.png", os.getcwd()+f"/database/accounts/{id}/analysis/profits.png", os.getcwd()+f"/database/accounts/{id}/analysis/statement.png", chart_dir]
        
        # Get the user's expenses as Value, Dictionary
        expenses, expenses_dic = get_expenses(id)

        # Get the user's revenues as Value, Dictionary
        profits, profits_dic = get_profits(id)

        # Create the pie charts for the revenues and expenses 
        get_pizza_info(profits_dic, id, "profits") 
        get_pizza_info(expenses_dic, id, "expenses") 

        # Create the dictionary {Expenses, Revenue} to send 
        dic_profits_expenses = {"Despesas": Decimal(expenses.split("€")[0]).quantize(Decimal('0.01')), "Receitas": Decimal(profits.split("€")[0]).quantize(Decimal('0.01'))}
        
        # Generate general economic report
        generate_economic_report(output, image_paths, id, dic_profits_expenses, expenses_dic, profits_dic)

        # Prepare the file to be sent
        response = send_file(os.getcwd()+f"/database/accounts/{id}/analysis/economic_report.pdf", as_attachment=True)
        response.headers['Content-Disposition'] = f'attachment; filename=economic_report.pdf'

        # Send the file to be downloaded
        return response


# This view presents the expenses analysis
@views.route('/expenses/<id>')
def expenses(id):

    # Check if the last recorded activity is valid
    if last_activity_check(id) == False:

        # Return the home page
        return redirect(url_for("views.index"))

    else:

        # Get the user's expenses as Value, Dictionary
        expenses, expenses_dic = get_expenses(id)

        # Create the pie charts for the revenues and expenses 
        get_pizza_info(expenses_dic, id, "expenses")

        # Get the username based on the ID
        name = search_user_by_id(id)[1]

        # Return the expenses analysis page
        return render_template('expenses.html', expenses=expenses, expenses_dic=expenses_dic, id=id, username = name)


# This view presents the revenue analysis
@views.route('/profits/<id>')
def profits(id):

    # Check if the last recorded activity is valid
    if last_activity_check(id) == False:

        # Return the home page
        return redirect(url_for("views.index"))

    else:

        # Get the user's revenues as Value, Dictionary
        profits, profits_dic = get_profits(id)

        # Create the pie charts for the revenues and expenses 
        get_pizza_info(profits_dic, id, "profits")

        # Get the username based on the ID
        name = search_user_by_id(id)[1]

        # Return the expenses analysis page
        return render_template('profits.html', profits=profits, profits_dic=profits_dic, id=id, username = name)


# This view returns the account settings page
@views.route("/account/<username>")
def account(username):
    
    # Get ID based on the username
    id = get_id_by_username(username)

    # Check if the last recorded activity is valid
    if last_activity_check(id) == False:

        # Return the home page
        return redirect(url_for("views.index"))

    else:

        # Return the account settings page
        return render_template("account.html", username=username, id=id)


# This view is used to fetch the user's account image
@views.route("/database/accounts/<id>/<image>", methods=["POST", "GET"])
def account_image(id, image):
    
    # Check if the last recorded activity is valid
    if last_activity_check(id) == False:

        # Return the home page
        return redirect(url_for("views.index"))

    else:

        # Send the user's account image
        return send_file(os.getcwd()+f"/database/accounts/{id}/{image}", mimetype='image/png')


# This view is used to get a image
@views.route('/get_image/<path:filename>')
def get_image(filename, cache_timeout=0):

    # Send the image
    path = "/".join(filename.split("/")[:-1])
    filename = filename.split("/")[-1]
    return send_from_directory(path, filename, cache_timeout=0)


# This view is used to update the user's account
@views.route("/update_account/<id>", methods=["POST"])
def update_account(id):

    # Check if the last recorded activity is valid
    if last_activity_check(id) == False:

        # Return the home page
        return redirect(url_for("views.index"))

    else:

        # Set the user's account image file path
        file_path = os.getcwd()+f"/database/accounts/{id}/{id}.png"

        # Get the new uploaded user's account image
        profile_photo = request.files.get("profile_photo")

        # If there is a image
        if profile_photo:

            # Save the image to the user's account
            profile_photo.save(file_path)

        # Get the username, email and password, from the user's session
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("psw")

        # Check if the username field wasn't empty and occupied by another user
        if username != "" and not check_username_exists(username):

            # Update the username
            update_username(id, username)

            # Set the sessions username
            session["username"] = username

        else:

            # If there is a problem with the username, get the username based on the ID
            username = search_user_by_id(id)[1]

        # Check if the email field wasn't empty and occupied by another user
        if email != "" and not check_email_exists(email):

            # Update the email
            update_email(id, email)

        else:

            # If there is a problem with the username, get the username based on the ID
            email = search_user_by_id(id)[3]

        # Check if the password wasn't empty
        if password != "":

            # Update the password
            update_password(id, password)
        
        # Return the profile page
        return redirect(url_for("views.profile", username=get_username_by_id(id)))


# This view is used to check if te username exits
@views.route('/check_username', methods=['POST'])
def check_username():

    # Get the username from the request
    username = request.form.get('username')

    # Check if the username exists
    exists = check_username_exists(username)

    # Build response dictionary with the boolean
    response = {'exists': exists}

    # Return the response as a JSON object
    return jsonify(response)


# This view is used to check if te email exits
@views.route('/check_email', methods=['POST'])
def check_email():

    # Get the email from the request
    email = request.form.get('email')

    # Check if the username exists
    exists = check_email_exists(email)

    # Build response dictionary with the boolean
    response = {'exists': exists}

    # Return the response as a JSON object
    return jsonify(response)


# This view is used to join or create a chat room
@views.route("/chat_home/<id>", methods=["POST", "GET"])
def chat_home(id):

    # Check if the last recorded activity is valid
    if last_activity_check(id) == False:

        # Return to the home page
        return redirect(url_for("views.index"))

    else:

        # Get the username based on the ID
        username = get_username_by_id(id)

        # Clear the session
        session.clear()

        # Check if the requested method is POST
        if request.method == "POST":

            # Get the code, join trigger, create trigger from the request
            code = request.form.get("code")
            join = request.form.get("join", False)
            create = request.form.get("create", False)

            # Check if the join trigger was triggered and a code wasn't inserted
            if join != False and not code:

                # Return the same page with a error message
                return render_template("chat_home.html", error="Please enter a room code.", code=code, name=id, username=username)

            # Set the room code
            room_code = code

            # Check if the create trigger was triggered
            if create != False:

                # Create a chat room and retrieve it's code
                room_code = create_room()

            # Check if the room exists
            elif check_room_code_exists(code) == False:

                # Return the same page with a error message
                return render_template("chat_home.html", error="Room does not exist.", code=code, name=id, username=username)
            
            # Set the room code and username to the session
            session["room"] = room_code
            session["name"] = username

            # Update the user's last recorded activity in the database
            set_activity_timer(id)

            # Return the chat room page
            return redirect(url_for("views.chat_room", id = id, name=username))

        # Return the same page
        return render_template("chat_home.html", code="", name=id, username=username)


# This view allows the user's to chat with each other
@views.route("/chat_room/<id>")
def chat_room(id):

    # Check if the last recorded activity is valid
    if last_activity_check(id) == False:

        # Return to the home page
        return redirect(url_for("views.index"))

    else:

        # Get the room code from the session
        room = session.get("room")

        # Check if the room code exists and if there is a room with that code
        if room is None or check_room_code_exists(room) == False:

            # Return the chat home page
            return redirect(url_for("views.chat_home", id=id))

        # Fetch all the messages from the chat room
        messages = get_room_messages(room)

        for element in messages:

            # Correct the spelling on the image file path
            element["image"] = element["image"].replace("\\", "/")

        # Return the chat room page
        return render_template("chat_room.html", code=room, messages=messages, id=id, name=get_username_by_id(id))


# This function is used to create a new message in the chat room
def new_message(data):

    # Get the room code
    room = session.get("room")

    # Check if the room exists
    if check_room_code_exists(room):

        # Get the username based on the ID
        name = get_username_by_id(data["name"])

        # Set the dictionary with the relevant data to be sent
        content = {
            "name": name,
            "id" : data["name"],
            "message": data["message"],
            "time": strftime("%d-%m-%Y %H:%M", localtime()),
            "image": get_image_path(data["name"])
        }

        # Send the data with the message
        send(content, to=room)
        
        # Add the room message to the database
        add_room_message(room, content)


# This function is used to connect the user to the chat room
def on_connect(auth, place):

    # Check if the user comes from the profile page
    if "profile" in place:

        # Get the username from the URL
        name = place.split("/")[-1]

        # Get the ID based on the username
        id = get_id_by_username(name)

        # Set the username and ID to the session 
        session["username"] = name
        session["id"] = id

        # Activate the user
        activate_user(id)

        return

    elif "chat_room" in place:

        # Get the room code and the username from the session
        room = session.get("room")
        name = session.get("name")

        # Check if there is a room code or a username
        if not room or not name: return

        # Check if exists a room with that code
        if check_room_code_exists(room) == False:

            # Leave the room
            leave_room(room)

            return

        # Join the room
        join_room(room)

        # Send the inicial connect message
        send({"name": name, "id": get_id_by_username(name), "message": name+" has entered the room", "time": strftime("%d-%m-%Y %H:%M", localtime()), "image":get_image_path(get_id_by_username(name))}, to=room)
        
        # Add the user to the room as a member
        add_room_member(room, name, get_id_by_username(name))


# This view is used to disconnect a user from the chat room
def on_disconnect(place):

    # Check if the user comes from the profile page
    if "profile" in place:

        # Get the username from the URL
        name = place.split("/")[-1]

        # Get the ID based on the username
        id = get_id_by_username(name)

        # Inactivate the user
        inactivate_account(id)

        return

    elif "chat_room" in place:

        # Get the room code and the username from the session
        room = session.get("room")
        name = session.get("name")

        # Check if exists a room with that code
        if check_room_code_exists(room):
            
            # Execute a query to retrieve the rooms members
            result = db_query("SELECT members FROM rooms WHERE code = %s", (room,))

            # Convert the result into a array
            array = list(result[0][0])
            
            # Remove the user from the members array
            array.remove({"name": name, "id": get_id_by_username(name)})

            # Execute a query to update the rooms table with the new members array
            db_query("UPDATE rooms SET members = %s WHERE code = %s", (json.dumps(array, indent=4), room))

            # Put the execution to sleep to give time to process
            time.sleep(5)

            # Check if the room isn't empty
            if get_number_of_room_members(room) <= 0:
                
                # Delete the room from the database
                delete_room(room)
                return
        
        # Send a disconnect message to the room, warning other users
        send({"name": name, "id": get_id_by_username(name), "message": name+" has left the room", "time": strftime("%d-%m-%Y %H:%M", localtime()), "image":get_image_path(get_id_by_username(name))}, to=room)
        
        # Disconnect the user from the room
        leave_room(room)
    else: return


# This function is used to inactivate an account
def inactivate_account(id):

    # Inactivate user
    inactivate_user(id)

    # Clear the session
    session.clear()


# This function is used to activate an account
def activate_account(name):

    # Get ID based on username
    id = get_id_by_username(name)

    # Activate user's account
    activate_user(id)
