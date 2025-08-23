from flask import Flask,request, render_template
from flask_mail import Mail, Message
from flask_pymongo import PyMongo
import  os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Use your email provider's SMTP server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')
mail = Mail(app)

app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)

@app.route('/')
def home():
    """
    Renders the homepage.
    """
    return render_template('index.html')

@app.route('/about')
def about():
    """
    Renders the about page.
    """
    return render_template('about.html')


@app.route('/post')
def post():
    """
    Renders the post page.
    """
    return render_template('post.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """
    Renders the contact page.
    """
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        phone = request.form['phone'].strip()
        message = request.form['message'].strip()


        # save the contact to mongoDB
        mongo.db.contacts.insert_one({'name': name,
            'email': email,
            'phone': phone_e164,
            'country_code': f"+{country_code}",
            'message': message,
            'date': datetime.utcnow()
        })

        # Send confirmation to user
        try:
            msg_to_user = Message("Thank You for Your Feedback!",
                                recipients=[email])
            msg_to_user.body = f"Hi {name},\n\nWe received your message:\n\"{message}\"\n\nThank you for getting in touch!"
            mail.send(msg_to_user)
        except Exception as e:
            print(f"Error sending to user: {e}")

        # Send notification to admin
        try:
            msg_to_admin = Message("New Feedback Submitted",
                                recipients=[app.config['MAIL_USERNAME']])  # your email
            msg_to_admin.body = f"New feedback from {name} ({email}):\n\n{message}"
            mail.send(msg_to_admin)
        except Exception as e:
            print(f"Error sending to admin: {e}")

        return render_template("contact.html", message="Thanks! Your feedback was submitted successfully.")
    return render_template("contact.html")


if __name__ == '__main__':
    app.run(debug=True)