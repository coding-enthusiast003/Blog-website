from flask import Flask,request, render_template, redirect, url_for,session,flash
from flask_mail import Mail, Message
from flask_pymongo import PyMongo
import  os
from dotenv import load_dotenv
from bson.objectid import ObjectId

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

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
    posts_cursor = mongo.db.posts.find().sort('date', -1).limit(3) # sorting the posts by date in descending order
    posts = list(posts_cursor)
    return render_template('index.html', posts=posts)

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
    post = next(post, None)   # next function is used to get the first item from the cursor
    if post:
        return redirect(url_for('show_post', post_id=str(post['_id'])))  # calling the show_post function with the latest post ID
    return "No post found.", 404



@app.route('/dashboard')
def dashboard():
    """
    Renders the dashboard page.
    """
    if 'user' not in session:
        return redirect(url_for('login'))

    user_email = session.get("email")
    return render_template('dashboard.html', username=session['user'], user_email=user_email)


@app.route('/logout')
def logout():
    """
    Logs the user out and clears the session.
    """
    session.clear()   # removes all session data
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Renders the login page.

    """
    if 'user' in session :
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password'].strip()
        
        #check
        user_find = mongo.db.users.find_one({'username': username, 'email': email, 'password': password})

        if user_find:
            session["user"] = user_find["username"]
            session["email"] = user_find["email"]
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Login failed. Please check your credentials.", "danger")
    
    return render_template('login.html')

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