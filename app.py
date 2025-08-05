from flask import Flask, render_template

app = Flask(__name__)

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


@app.route('/contact')
def contact():
    """
    Renders the contact page.
    """
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True)