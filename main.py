import os
import shutil
from functools import wraps

import stripe
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    render_template_string,
    request,
    url_for,
)
from flask.helpers import send_from_directory
from replit import db, web
from werkzeug.utils import secure_filename

from forms import ContentCreateForm, name_to_id

app = Flask(__name__, static_folder='static', static_url_path='')
# Secret key
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]


# Database setup
def db_init():
  if "content" not in db:
    db["content"] = {}

  if "orders" not in db:
    db["orders"] = {}

  # Create directories
  if not os.path.exists("static"):
    os.mkdir("static")

  if not os.path.exists("content"):
    os.mkdir("content")


db_init()

users = web.UserStore()
ADMINS = ["KevinIsom"]


# Helper functions
def is_admin(username):
  return username in ADMINS


# Auth decorators
def admin_only(f):

  @wraps(f)
  def decorated_function(*args, **kwargs):

    if not is_admin(web.auth.name):
      flash("Permission denied.", "warning")
      return redirect(url_for("index"))

    return f(*args, **kwargs)

  return decorated_function


def owns_content(username, content_id):
  if "content_library" in users[username] and users[username]["content_library"] is not None:
    return content_id in users[username]["content_library"]


def context():
  if "content_library" in users.current.keys() and users.current["content_library"] is not None:
      my_library = users.current["content_library"]
  else:
      my_library = []
  
  return {
      "username": web.auth.name,
      "my_library": my_library,
      "admin": is_admin(web.auth.name),
      "content": db["content"]
  }

# Main app
@app.route("/")
@web.authenticated
@admin_only
def index():
  return render_template("index.html", **context())


@app.route("/content/<content_id>")
@web.authenticated
def content(content_id):
  return render_template("content.html", content_id=content_id, **context())


@app.route("/content-file/<content_id>")
@web.authenticated
def content_file(content_id):

  content = db["content"][content_id]

  if not content["paywalled"] or owns_content(web.auth.name, content_id):
    return send_from_directory("content", path=content["filename"])
  else:
    return "Access denied."


# Admin functionality
@app.route('/admin/content-create', methods=["GET", "POST"])
@web.authenticated
@admin_only
def content_create():
  form = ContentCreateForm()

  if request.method == "POST" and form.validate():
    content_name = form.name.data
    content_id - name_to_id(content_name)
    content_price = form.price.data

    content_file = form.file.data
    content_filename = secure_filename(content_file.filename)
    content_file.save(os.path.join("content", content_filename))

    image_file = form.image.data
    image_filename = secure_filename(image_file.filename)
    image_file.save(os.path.join("static", image_filename))

    content_paywalled = content_price > 0

    # Construct content dictionary
    db["content"][content_id] = {
        "name": content_name,
        "price": content_price,
        "filename": content_filename,
        "image": image_filename,
        "description": form.description.data,
        "preview_image": image_filename,
        "paywalled": content_paywalled
    }

    flash("Content created")
    return redirect(url_for("index", content_id=content_id))

  return render_template("admin/content-create.html", form=form, **context())


@app.route('/admin/db-flush')
@web.authenticated
@admin_only
def flush_db():
  # clear db
  del db["content"]
  del db["orders"]

  # clear users
  for _, user in users.items():
    users["content_library"] = []

  #delete content and images
  shutil.rmtree("content")
  shutil.rmtree("static")

  # reinit
  db_init()

  return redirect(url_for("index"))


# Run the app
web.run(app)

# if __name__ == "__main__":
#     app.run(debug=True, host="0.0.0.0", port=8080)
