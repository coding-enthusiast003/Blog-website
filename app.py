from flask import Flask,request, render_template, redirect, url_for
from flask_mail import Mail, Message
from flask_pymongo import PyMongo
import  os
from dotenv import load_dotenv
from bson.objectid import ObjectId

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
    Renders the homepage with all posts.
    """
    posts_cursor = mongo.db.posts.find().sort('date', -1)
    posts = list(posts_cursor)
    sample_post_id = str(posts[0]['_id']) if posts else None
    return render_template('index.html', posts=posts, sample_post_id=sample_post_id)

@app.route('/about')
def about():
    """
    Renders the about page.
    """
    return render_template('about.html')


@app.route('/post/<post_id>')
def show_post(post_id):
    """
    Renders the post page.
    """
    post = mongo.db.posts.find_one({'_id': ObjectId(post_id)})

    return render_template('post.html', post=post)

@app.route('/post/')
def show_latest_post():
    """
    Redirects /post/ to the latest blog post's URL.
    """
    post = mongo.db.posts.find().sort('date', -1).limit(1)
    post = next(post, None)
    if post:
        return redirect(url_for('show_post', post_id=str(post['_id'])))
    return "No post found.", 404


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """
    Renders the contact page.
    """
    try:
        if request.method == 'POST':
            name = request.form['name'].strip()
            email = request.form['email'].strip().lower()
            phone = request.form['phone'].strip()
            message = request.form['message'].strip()


            # save the contact to mongoDB
            mongo.db.contacts.insert_one({'name': name,
                'email': email,
                'phone': phone,
                'message': message})

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

    except Exception as e:
        print(f"Error: {e}")
        return render_template("contact.html", message="An error occurred. Please try again later.")

if __name__ == '__main__':
    app.run(debug=True)