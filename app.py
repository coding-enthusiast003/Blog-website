from flask import Flask,request, render_template, redirect, url_for,session,flash
from flask_mail import Mail, Message
from flask_pymongo import PyMongo
import  os
from dotenv import load_dotenv
from bson.objectid import ObjectId
from datetime import datetime
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher()

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
    page = int(request.args.get('page', 1))
    posts_per_page = 3

    # Count total posts in MongoDB
    total_posts = mongo.db.posts.count_documents({})

    # Calculate how many posts to skip
    skip = (page - 1) * posts_per_page

    posts_cursor = mongo.db.posts.find().sort('date', -1).skip(skip).limit(posts_per_page)
    posts = list(posts_cursor)

    # Total number of pages
    total_pages = (total_posts + posts_per_page - 1) // posts_per_page
    return render_template('index.html', posts=posts, total_pages=total_pages, current_page=page)

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
    Renders the dashboard page. b
    """
    if 'user' not in session:
        return redirect(url_for('login'))

    user_email = session.get("email")
    posts = mongo.db.posts.find({'email': user_email}).sort('date', -1)
    return render_template('dashboard.html', username=session['user'], user_email=user_email, posts=posts)


@app.route('/add', methods=['GET', 'POST'])
def add_blog():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title'].strip()
        subtitle = request.form['subtitle'].strip()
        content = request.form['content'].strip()
        img_file = request.files.get('file1')
        author = session.get("user")
        date = datetime.now().strftime("%B %d, %Y")
        email = session.get("email")

        
         
        post_data = {
            'title': title,
            'subtitle': subtitle,
            'content': content,
            'email': email,
            'author': author,
            'date': date
        }
         

        mongo.db.posts.insert_one(post_data)
        flash("Post added successfully!", "success")
        return redirect(url_for('dashboard'))

    return render_template('add.html')


@app.route('/edit/<post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    """
    Edits an existing post.
    """
    if 'user' not in session:
        return redirect(url_for('login'))

    post = mongo.db.posts.find_one({'_id': ObjectId(post_id)})

    if request.method == 'POST':
        title = request.form['title'].strip()
        content = request.form['content'].strip()

        mongo.db.posts.update_one({'_id': ObjectId(post_id)}, {'$set': {'title': title, 'content': content}})
        flash("Post updated successfully!", "success")
        return redirect(url_for('dashboard'))

    return render_template('edit.html', post=post)


@app.route("/delete/<post_id>")
def delete_post(post_id):
    if "user" not in session:
        return redirect(url_for("login"))

    mongo.db.posts.delete_one({"_id": ObjectId(post_id)})
    flash("Post deleted successfully!", "success")
    return redirect(url_for("dashboard"))


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
    if 'user' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        # Step 1: Find user by username + email only
        user_find = mongo.db.users.find_one({'username': username, 'email': email})

        if not user_find:
            flash("User not found.", "danger")
            return render_template('login.html')

        # Step 2: Verify password with Argon2
        try:
            ph.verify(user_find['password'], password)
        except VerifyMismatchError:
            flash("Login failed. Invalid password.", "danger")
            return render_template('login.html')

        # Step 3: If success, start session
        session["user"] = user_find["username"]
        session["email"] = user_find["email"]
        flash("Login successful!", "success")
        return redirect(url_for("dashboard"))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        # Hash the password
        hashed_password = ph.hash(password)

        # Save the user to the database
        mongo.db.users.insert_one({
            'username': username,
            'email': email,
            'password': hashed_password
        })

        flash("Registration successful! You can now log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

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