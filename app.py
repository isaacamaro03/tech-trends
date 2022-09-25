import sqlite3
import logging

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

logging.basicConfig(filename='app.log',level=logging.DEBUG, force=True)
stderrLogger=logging.StreamHandler()
stderrLogger.setFormatter(logging.Formatter('[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s'))
logging.getLogger().addHandler(stderrLogger)

## stream logs to app.log file

db_connections = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global db_connections
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    db_connections += 1
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      logging.info(f"Failed to find article with id \"{post_id}\"")
      return render_template('404.html'), 404
    else:
      logging.info(f"Article with title \"{post['title']}\" retrieved")
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    logging.info("The \"About Us\" page was retrieved")
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()

            logging.info(f"A new article was created with title \"{title}\"")

            return redirect(url_for('index'))

    return render_template('create.html')

# Health status endpoint
@app.route('/healthz')
def healthz():
    isDatabaseUp = True

    try:
        connection = get_db_connection()
        connection.execute('SELECT * FROM posts ORDER BY ROWID ASC LIMIT 1').fetchone()
        connection.close()
    except:
        isDatabaseUp = False

    if (isDatabaseUp):
        response = app.response_class(
            response=json.dumps({"result":"OK - healthy"}),
            status=200,
            mimetype='application/json'
        )
    else:
        response = app.response_class(
            response=json.dumps({"result":"ERROR - unhealthy"}),
            status=500,
            mimetype='application/json'
        )
    return response

# Metrics endpoint
@app.route('/metrics')
def metrics():
    responseData = {
        "db_connection_count": db_connections,
        "post_count": 0
    }

    connection = get_db_connection()
    responseData["post_count"] = connection.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
    connection.close()

    response = app.response_class(
        response=json.dumps(responseData),
        status=200,
        mimetype='application/json'
    )
    return response

# start the application on port 3111
if __name__ == "__main__":
   app.run(host='0.0.0.0', port='3111')
