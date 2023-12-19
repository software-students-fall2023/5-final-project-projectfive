import smtplib
import time
from os import environ
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pymongo import MongoClient

# Create a connection to the MongoDB server
client = MongoClient(
    f"mongodb://{environ.get('MONGO_USERNAME')}:{environ.get('MONGO_PASSWORD')}@mongo?authSource=admin"
)
DB = client["DB"]

# Select the database


# Create or select the 'plans' collection
plans_collection = DB['plans']

def send_plan_content_email(to_email, content):
    sender_email = "writeyourplan@gmail.com"
    sender_password = environ.get("NOTIFIER_EMAIL_PASSWORD")

    # Create the MIMEText object
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = "Reminder from WriteYourPlan"

    # Body of email
    body = f"Your plan content:\n\n{content}"
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Setting up SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)  # Replace with your SMTP server details
        server.starttls()  # Secure the connection
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
        print(f"Email sent to {to_email} successfully")
    except Exception as e:
        print(f"Error: {e}")

def check_and_send_reminders():
    current_time = time.time()

    # Retrieve plans from MongoDB
    db_plans = plans_collection.find()

    for plan in db_plans:
        if plan["locked"] and current_time >= (plan["created"] + plan["duration"]):
            send_plan_content_email(plan['username'], plan['content'])
            # Update the plan in the DB to mark it as "unlocked" or take any other necessary actions
            plans_collection.update_one({"_id": plan["_id"]}, {"$set": {"locked": False}})

if __name__ == "__main__":
    while True:
        check_and_send_reminders()
        time.sleep(120)  # Sleep for 2 minutes before checking again
