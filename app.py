from flask import Flask,render_template,jsonify,request,redirect,url_for,session
import pymysql
import math
import requests
import threading
from datetime import datetime, timedelta , timezone
import random
import os
import binascii
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json

app = Flask(__name__)
secret_key = binascii.hexlify(os.urandom(24)).decode('utf-8')
app.secret_key = secret_key

# Database connection
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        db='college_bus_tracking',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on Earth."""
    try:
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = [float(x) * math.pi / 180.0 for x in [lat1, lon1, lat2, lon2]]
        
        # Or using map:
        # lat1, lon1, lat2, lon2 = map(lambda x: float(x) * math.pi / 180.0, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        r = 6371  # Radius of Earth in kilometers
        return c * r
    except Exception as e:
        print(f"Error in haversine calculation: {e}")
        raise


@app.route("/")
def root():
    connection = get_db_connection()
    return render_template('admin_login.html')


@app.route("/get-bus-numbers", methods=["GET"])
def get_bus_numbers():
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT route_no FROM bus_info")
            buses = cursor.fetchall()

            print(buses)
        connection.close()
        return jsonify({"success": True, "buses": buses})
    except Exception as e:
        print(f"Error fetching bus numbers: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/get-bus-stops", methods=["GET"])
def get_bus_stops():
    bus_number = request.args.get("bus_number")
    if not bus_number:
        return jsonify({"success": False, "message": "Bus number is required"}), 400

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT via FROM bus_info WHERE route_no = %s", (bus_number,))
            result = cursor.fetchone()
        connection.close()

        if not result:
            return jsonify({"success": False, "message": "Bus route not found"}), 404

        # Split the comma-separated list of stops
        stops = [stop.strip() for stop in result['via'].split(',')]
        return jsonify({"success": True, "stops": stops})
    except Exception as e:
        print(f"Error fetching bus stops: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/set-notification", methods=["POST"])
def set_notification():
    data = request.json
    user_id = data.get("user_id")  # You would get this from authentication
    bus_number = data.get("bus_number")
    stop_location = data.get("stop_location")
    user_lat = data.get("user_lat")
    user_lng = data.get("user_lng")

    if not all([bus_number, stop_location, user_lat, user_lng]):
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Store notification preferences in user_data table
            cursor.execute(
                "UPDATE user_data  SET bus_number = %s, stop_location = %s, user_lat = %s, user_lng = %s WHERE Username = %s",
                (bus_number, stop_location, user_lat, user_lng, user_id)
            )
        connection.commit()
        connection.close()

        return jsonify({"success": True, "message": "Notification set successfully"})
    except Exception as e:
        print(f"Error setting notification: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/get-route", methods=["GET"])
def get_route():
    bus_number = request.args.get("bus_number")
    if not bus_number:
        return jsonify({"success": False, "message": "Bus number is required"}), 400

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Get bus route information
            cursor.execute(
                "SELECT arrival, departure, via FROM bus_info WHERE route_no = %s",
                (bus_number,)
            )
            bus_info = cursor.fetchone()

            cursor.execute("SELECT latitude, longitude FROM bus_stops WHERE place=%s", bus_info['arrival'],)
            arrival_points = cursor.fetchone()

            cursor.execute("SELECT latitude, longitude FROM bus_stops WHERE place=%s", bus_info['departure'], )
            departure_points = cursor.fetchone()

            if not bus_info:
                return jsonify({"success": False, "message": "Bus route not found"}), 404

            # Get via points coordinates
            via_points = []
            stops = [stop.strip() for stop in bus_info['via'].split(',')]

            for stop in stops:
                cursor.execute("SELECT latitude, longitude FROM bus_stops WHERE place = %s", (stop,))
                stop_coords = cursor.fetchone()
                if stop_coords:
                    via_points.append((float(stop_coords['latitude']), float(stop_coords['longitude'])))

        connection.close()

        # Get route coordinates
        start_lat  = float(departure_points['latitude'])
        start_lng  = float(departure_points['longitude'])
        end_lat    = float(arrival_points['latitude'])
        end_lng    = float(arrival_points['longitude'])

        route_coords = fetch_route_coordinates_with_via(start_lat, start_lng, end_lat, end_lng, via_points)

        return jsonify({
            "success": True,
            "route": route_coords,
            "via_points": via_points
        })
    except Exception as e:
        print(f"Error getting route: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/check-proximity", methods=["POST"])
def check_proximity():
    """This method is used to check the proximity of the bus to the selected stop location."""
    data = request.json
    user_id = data.get("user_id", "anonymous")

    user_lat = data.get("user_lat")
    user_lng = data.get("user_lng")

    if not all([user_lat, user_lng]):
        return jsonify({"success": False, "message": "Missing coordinates"}), 400

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Get user notification preferences
            cursor.execute(
                "SELECT bus_number, stop_location FROM user_data WHERE Username = %s",
                (user_id,)
            )
            user_pref = cursor.fetchone()

            if not user_pref:
                return jsonify({"success": False, "message": "No notification set"}), 404

            # Get bus current location
            cursor.execute(
                "SELECT latitude, longitude FROM bus_info WHERE route_no = %s",
                (user_pref['bus_number'],)
            )
            bus_location = cursor.fetchone()

            # Get selected stop location
            cursor.execute(
                "SELECT latitude, longitude FROM bus_stops WHERE place = %s",
                (user_pref['stop_location'],)
            )
            stop_location = cursor.fetchone()

            if not bus_location or not stop_location:
                return jsonify({"success": False, "message": "Location data not found"}), 404

            # Calculate distance between bus and selected stop
            bus_to_stop_distance = haversine(
                float( bus_location['latitude']), float(bus_location['longitude']),
                float(stop_location['latitude']), float(stop_location['longitude'])
            )

            # Get user email
            cursor.execute("SELECT email FROM user_data WHERE Username = %s", (user_id,))
            user_email = cursor.fetchone()

        connection.close()

        # Check if bus is near the selected stop (within 1 km)
        proximity_threshold = 3.0  # 1 kilometer
        if bus_to_stop_distance <= proximity_threshold:
            # Send email notification
            if user_email and user_email['email']:
                send_proximity_email(
                    user_email['email'],
                    user_pref['bus_number'],
                    user_pref['stop_location'],
                    bus_to_stop_distance
                )
                return jsonify({
                    "success": True,
                    "notification": True,
                    "message": "Bus approaching your stop, email notification sent",
                    "distance": bus_to_stop_distance
                })

        return jsonify({
            "success": True,
            "notification": False,
            "distance": bus_to_stop_distance
        })
    except Exception as e:
        print(f"Error checking proximity: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


def send_proximity_email(email, bus_number, stop_location, distance):
    try:
        # Email configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_username = "samcharles290@gmail.com"
        smtp_password = "nepf hqtt clmw hzdd"

        # Sender and recipient email addresses
        sender_email = "samcharles290@gmail.com"
        recipient_email = email

        # Create a MIME object
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = recipient_email
        message['Subject'] = f"Bus Approaching: {bus_number}"

        # Construct the email body
        email_body = f"""
        <html>
          <head>
            <style>
              body {{
                font-family: 'Arial', sans-serif;
                background-color: #f5f5f5;
                color: #333;
                padding: 20px;
              }}
              .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #fff;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
              }}
              h1 {{
                color: #009688;
              }}
              ul {{
                list-style-type: none;
                padding: 0;
              }}
              li {{
                margin-bottom: 10px;
              }}
            </style>
          </head>
          <body>
            <div class="container">
              <h1>Bus Approaching Alert</h1>
              <p><strong>You're about to reach your stop:</strong></p>
              <ul>
                <li><strong>Bus Number:</strong> {bus_number}</li>
                <li><strong>Stop:</strong> {stop_location}</li>
                <li><strong>Distance:</strong> {distance:.2f} km</li>
              </ul>
              <p>Get ready to disembark!</p>
            </div>
          </body>
        </html>
        """

        # Attach the email body
        message.attach(MIMEText(email_body, 'html'))

        # Connect to SMTP server and send
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, recipient_email, message.as_string())

        print("Proximity email sent successfully.")
        return True
    except Exception as e:
        print(f"Error sending proximity email: {e}")
        return False


def fetch_route_coordinates_with_via(start_lat, start_lng, end_lat, end_lng, via_points):
    """
    Fetch the route coordinates between two locations using the OSRM API, including via points.
    """
    try:
        # Constructing the locations string with via points
        locations = f"{start_lng},{start_lat};"
        for lat, lng in via_points:
            locations += f"{lng},{lat};"
        locations += f"{end_lng},{end_lat}"

        url = f"http://router.project-osrm.org/route/v1/driving/{locations}"
        params = {
            "overview": "full",
            "geometries": "geojson"
        }
        response = requests.get(url, params=params, timeout=10)

        if response.status_code != 200:
            print(f"Error: Unable to fetch route. Status Code: {response.status_code}")
            return []

        data = response.json()
        route = data["routes"][0]["geometry"]["coordinates"]
        coordinates = [(lat, lng) for lng, lat in route]  # Convert to (lat, lng)
        return coordinates

    except Exception as e:
        print(f"Error fetching route coordinates: {e}")
        return []


@app.route("/find-nearest", methods=["POST"])
def find_nearest():
    data = request.json
    user_lat = data.get("latitude")
    user_lng = data.get("longitude")

    if user_lat is None or user_lng is None:
        return jsonify({"success": False, "message": "Invalid coordinates."}), 400

    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT place, latitude, longitude FROM bus_stops")
            bus_stops = cursor.fetchall()
        connection.close()

        nearest_place = None
        min_distance = float("inf")

        # Find the nearest stop
        for stop in bus_stops:
            distance = haversine(
                user_lat, user_lng,
                float(stop['latitude']), float(stop['longitude'])
            )
            if distance < min_distance:
                min_distance = distance
                nearest_place = stop['place']

        return jsonify({
            "success": True,
            "nearest_place": nearest_place,
            "distance": min_distance
        })

    except Exception as e:
        print(f"Error finding nearest stop: {e}")
        return jsonify({"success": False, "message": str(e)}), 500





######################################### Following program Contents are copied from support project ########################################
@app.route(rule='/map',methods=['GET'])
def map():
    email=session['email']
    user_id=session['user_id']
    username=session['username']
    return render_template(template_name_or_list='main.html',email=email,user_id=user_id,username=username)
  


@app.route(rule='/check_user', methods=['POST','GET'])
def check_user():
    mesage = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM user_data WHERE email = % s AND password = % s', (email, password, ))
            user = cursor.fetchone()
            print(user)
            if user:
                session['loggedin'] = True
                session['email'] = email
                session['user_id'] = user['id']
                session['username'] = user['Username']
         
                mesage = 'Logged in successfully !'
                return  redirect(url_for('map'))
            else:
                mesage = 'Please enter correct email / password !'
                return render_template('admin_login.html', mesage = mesage)
        






@app.route(rule='/forgot_password',methods=['GET'])
def forgot_password():
    return render_template(template_name_or_list='forgot_password.html')

@app.route(rule='/change_password', methods=['POST'])
def change_password():
    try:

        data = request.json
        email= data.get('email')
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute( f"SELECT * FROM `user_data` WHERE `email` = '{email}'")
            count = cursor.fetchone()
            if count:
                otp = generate_otp()
                session['otp_data'] = {'otp': otp, 'timestamp': datetime.now()}
                session['email'] = email
                session['forget_email'] = email
                email_thread = threading.Thread(target=send_otp_email, args=(email, otp))
                email_thread.start()
                return jsonify({'message': 'success'})


            else:
                return jsonify({ 'message': 'Account was not Found!'})
    except Exception as e:
        return jsonify({'message': 'error', 'error': str(e)})


@app.route(rule='/otp_verification',methods=['GET'])
def otp_verification():
    return render_template(template_name_or_list='otp_verification.html')


@app.route(rule='/verify_otp', methods=['POST'])
def verify_otp():
    print("control Here")
    entered_otp = request.json.get('otp')
    print("Entered OTP",entered_otp)
    print ('otp_data' in session )
    if 'otp_data' in session and 'email' in session:
        print("otp data")
        if not is_otp_session_expired(session['otp_data']['timestamp']):
            stored_otp = session['otp_data']['otp']
            if entered_otp == stored_otp:
                return jsonify({'message': 'success'})
            else:
                return jsonify({'message': 'error'})
    else:
        return jsonify({'message':'timeout'})

    # Add a default return statement in case the conditions are not met


@app.route(rule='/timeout',methods=['GET'])
def timeout():
    return render_template(template_name_or_list='session_closed.html')


@app.route(rule='/update_password',methods=['GET'])
def update_password():
    return render_template(template_name_or_list='change_password.html')


@app.route(rule='/update_password_data', methods=['POST'])
def update_password_data():
    try:
        data = request.json
        email=session['forget_email']
        new_password = data.get('confirmpassword')
        print("UPDATE_PASSWORD_DATA() EMAIL---->",email)
        # Check if the email exists in the database
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM user_data WHERE email = '{email}'")
            count = cursor.fetchone()[0]

            if count > 0:
                # Update the password for the given email
                connection = get_db_connection()
                with connection.cursor() as cursor:
                    cursor.execute(f"UPDATE user_data SET password = '{new_password}' WHERE email = '{email}'")
                    connection.commit()
                    confirmation_email_thread = threading.Thread(target=confirmation_email, args=(email,))
                    confirmation_email_thread.start()
                    return jsonify({'message': 'success'})

            else:

                return  jsonify({'message': 'error', 'error': 'Email not found in the database'})


    except Exception as e:
        print("UPDATE_PASSWORD_DATA()---->ERROR:", e)
        return jsonify({'message': 'error', 'error': str(e)})


def confirmation_email(email):
    try:
        # Fetch email id from the database based on the provided email
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT email FROM user_data WHERE email = '{email}'")
            recipient_email = cursor.fetchone()[0]

            # Email configuration (update with your SMTP server details)
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            smtp_username = "samcharles290@gmail.com"
            smtp_password = "nepf hqtt clmw hzdd"

            # Sender and recipient email addresses
            sender_email = "samcharles290@gmail.com"

            # Create a MIME object to represent the email
            message = MIMEMultipart()
            message['From'] = sender_email
            message['To'] = recipient_email
            message['Subject'] = "Password Change Confirmation"

            # Construct the email body
            current_time = time.strftime("%Y-%m-%d %H:%M:%S")
            email_body = f"Dear User,\n\nYour password for the account {email} was changed at {current_time}.\n\nThis change is confirmed.\n\nBest regards,\nYour App Team"

            # Attach the email body to the MIME object
            message.attach(MIMEText(email_body, 'plain'))

            # Connect to the SMTP server and send the email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail(sender_email, recipient_email, message.as_string())

            print("Confirmation Email sent successfully.")

    except Exception as e:
        print(f"Error sending email: {e}")


def generate_otp():
    return str(random.randint(100000, 999999))


def is_otp_session_expired(timestamp):
    # Make the current time offset-aware
    current_time = datetime.now(timezone.utc)
    # Ensure that the timestamp is offset-aware
    if timestamp.tzinfo is None or timestamp.tzinfo.utcoffset(timestamp) is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return current_time > timestamp + timedelta(minutes=10)


def send_otp_email(email,otp):
    try:
        # Fetch email id from the database based on the provided rfid_tag
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT email FROM user_data WHERE email = '{email}'")
            temp = cursor.fetchone()
            recipient_email = temp['email']
            
            # Email configuration (update with your SMTP server details)
            smtp_server = "smtp.gmail.com"
            smtp_port = 587
            smtp_username = "samcharles290@gmail.com"
            smtp_password = "nepf hqtt clmw hzdd"

            # Sender and recipient email addresses
            sender_email = "samcharles290@gmail.com"

            # Create a MIME object to represent the email
            message = MIMEMultipart()
            message['From'] = sender_email
            message['To'] = recipient_email
            message['Subject'] = "One Time Password for Account Recovery"

            # Construct the email body
            email_body = f"Dear User,\n\nYour One Time Password for the account {email} is: {otp}\n\nThis OTP is valid for 10 Minutes\nYour App Team"

            # Attach the email body to the MIME object
            message.attach(MIMEText(email_body, 'plain'))

            # Connect to the SMTP server and send the email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail(sender_email, recipient_email, message.as_string())
            print("Email Sent Successfully")
            return 1

    except Exception as e:
        print(f"Error sending email: {e}")


@app.route(rule='/sign_up',methods=['GET'])
def sign_up():
    return render_template('sign_up.html')


from flask import jsonify


@app.route(rule='/signupdata', methods=['POST'])
def signupdata():
    try:
        data = request.json
        name = data.get('firstName')
        email = data.get('email')
        password = data.get('password')
        phoneNumber = data.get('phoneNumber')
        otp=data.get('otp')
        print("SIGNUPDATA()--->Entered name", name)
        print("SIGNUPDATA()--->Entered email", email)
        print("SIGNUPDATA()--->Entered Password", password)
        print("SIGNUPDATA()--->Entered Phone number", phoneNumber)
        print("SIGNUPDATA()--->Entered OTP", otp)
        print('SIGNUPDATA()--->otp_data' in session)
        if 'otp_data' in session and 'email' in session:
            print("otp data")
            if not is_otp_session_expired(session['otp_data']['timestamp']):
                stored_otp = session['otp_data']['otp']
                print("SIGNUPDATA()--->Stored OTP", stored_otp)
                if otp == stored_otp:
                    connection = get_db_connection()
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "INSERT INTO user_data (Username, email, password, phone_number) VALUES (%s, %s, %s, %s)",
                            (name, email, password, phoneNumber))
                        connection.commit()
                    return jsonify({'message': 'success'})
                else:
                    return jsonify({'message': 'error'})
            else:
                return render_template(template_name_or_list='session_closed.html')
        else:
            return jsonify({'message': 'timeout'})

    except Exception as e:
        return jsonify({'message': 'error', 'error': str(e)})


@app.route(rule='/logout',methods=['GET'])
def logout():
    session['loggedin'] = False
    session['email'] = ""
    print("Successfully Looged Outx`")
    return render_template(template_name_or_list='admin_login.html')


@app.route(rule='/signup_otp', methods=['POST'])
def signup_otp():
    try:
        print("Control in signup_otp")
        data = request.json
        email = data.get('email')

        # Check if the email already exists in the database
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM `user_data` WHERE `email` = %s", args=(email,))
            existence = cursor.fetchall()

            if not existence:
                otp = generate_otp()
                session['otp_data'] = {'otp': otp, 'timestamp': datetime.now()}
                session['email'] = email
                email_thread = threading.Thread(target=signup_send_otp_email, args=(email, otp))
                email_thread.start()
                return jsonify({'message': 'success'})
            else:
                return jsonify({'message': "This User is Already Taken!"})

    except Exception as e:
        print("SIGNUP_OTP----> Error:", e)
        return jsonify({'message': 'error'})


def signup_send_otp_email(email,otp):
    try:
        recipient_email=email
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_username = "samcharles290@gmail.com"
        smtp_password = "tcud zgsz mjsk nokp"

        # Sender and recipient email addresses
        sender_email = "samcharles290@gmail.com"

        # Create a MIME object to represent the email
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = recipient_email
        message['Subject'] = "One Time Password for SignUp Account"

        # Construct the email body
        email_body = f"Dear User,\n\nYour One Time Password for the account {email} is: {otp}\n\nThis OTP is valid for 10 Minutes\nSam Charles's App "

        # Attach the email body to the MIME object
        message.attach(MIMEText(email_body, 'plain'))

        # Connect to the SMTP server and send the email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        print("Email Sent Successfully")
        return 1

    except Exception as e:
        print(f"Error sending email: {e}")

@app.route('/location_update', methods=['POST'])
def location_update():
    """Bus Location Update API"""
    try:
        # Get data from the POST form data (not query parameters)
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        bus_no = request.form.get('bus_no')
        
        print("Bus Data:", bus_no, latitude, longitude)
        
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Check if the bus number exists in the database
            cursor.execute("SELECT `bus_no` FROM `bus_info` WHERE `route_no`= %s", (bus_no,))
            detected = cursor.fetchone()
            
            # If bus number does not exist, insert new location data
            if not detected:
                cursor.execute("INSERT INTO `bus_info`(`route_no`, `latitude`, `longitude`) VALUES (%s, %s, %s)",
                           (bus_no, latitude, longitude))
            # If bus number exists, update existing location data
            else:
                cursor.execute("UPDATE `bus_info` SET `latitude`=%s, `longitude`=%s WHERE `route_no`=%s",
                           (latitude, longitude, bus_no))
            
            connection.commit()
        
        return 'Location updated successfully', 200
    
    except Exception as e:
        print("ERROR:", e)
        # Return an error response with more details for debugging
        return f'Error processing the request: {str(e)}', 500











if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)