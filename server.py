from flask import Flask, send_from_directory
from flask_cors import CORS, cross_origin
from flask_swagger_ui import get_swaggerui_blueprint
import os, json
from db import db
from config import Config
from models import signup, users, products, orders, wishlists, reviews, cart, billing, payment_details


app = Flask(__name__, static_folder="static")
CORS(app)
# CORS(app, origins=["https://yourdomain.com"])

app.config["SQLALCHEMY_DATABASE_URI"] = Config.SQLALCHEMY_DATABASE_URI
db.init_app(app)


SWAGGER_URL = Config.SWAGGER_PATH
API_URL = Config.SWAGGER_FILE

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL, API_URL, config={"app_name": "API"}
)
app.register_blueprint(swagger_ui_blueprint, url_prefix=SWAGGER_URL)

with app.app_context():
    db.create_all()
    db.session.commit()
    from routes import main, carts, wishlist, payments_routes


root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


@app.route("/<path:path>", methods=["GET"])
def static_files(path):
    return send_from_directory(root, path)


@app.route("/", methods=["GET"])
def index():
    return send_from_directory(root, "index.html")

@app.route("/home", methods=["GET"])
def index1():
    return send_from_directory(root, "index.html")


@app.after_request
def adding_header_content(head):
    head.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    head.headers["Pragma"] = "no-cache"
    head.headers["Expires"] = "0"
    head.headers["Cache-Control"] = "public, max-age=0"
    return head


if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT, debug=True, threaded=True)


