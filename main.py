import os
from flask import Flask, redirect, url_for, request, jsonify
from authlib.integrations.flask_client import OAuth
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
load_dotenv()    # reads the .env file into os.environ

# Flask app setup
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///db.sqlite3")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions
db = SQLAlchemy(app)
oauth = OAuth(app)

# Register OAuth providers
oauth.register(
    name="facebook",
    client_id=os.getenv("FACEBOOK_CLIENT_ID"),
    client_secret=os.getenv("FACEBOOK_CLIENT_SECRET"),
    access_token_url="https://graph.facebook.com/v10.0/oauth/access_token",
    authorize_url="https://www.facebook.com/v10.0/dialog/oauth",
    api_base_url="https://graph.facebook.com/v10.0/",
    client_kwargs={"scope": "email"}
)

oauth.register(
    name="twitter",
    client_id=os.getenv("TWITTER_CLIENT_ID"),
    client_secret=os.getenv("TWITTER_CLIENT_SECRET"),
    request_token_url="https://api.twitter.com/oauth/request_token",
    access_token_url="https://api.twitter.com/oauth/access_token",
    authorize_url="https://api.twitter.com/oauth/authenticate",
    api_base_url="https://api.twitter.com/1.1/"
)

# Define database model
class SocialUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(20), nullable=False)
    uid = db.Column(db.String(200), unique=True, nullable=False)
    name = db.Column(db.String(200))
    email = db.Column(db.String(200))

# Create database tables
with app.app_context():
    db.create_all()

# Routes
@app.route("/")
def home():
    return "Welcome to Social Auth API"

@app.route("/login/<provider>")
def login(provider):
    redirect_uri = url_for("auth", provider=provider, _external=True)
    return oauth.create_client(provider).authorize_redirect(redirect_uri)

@app.route("/auth/<provider>")
def auth(provider):
    client = oauth.create_client(provider)
    token = client.authorize_access_token()
    if provider == "facebook":
        resp = client.get("me?fields=id,name,email")
    else:
        resp = client.get("account/verify_credentials.json?include_email=true")
    profile = resp.json()
    uid = str(profile.get("id"))

    user = SocialUser.query.filter_by(provider=provider, uid=uid).first()
    if not user:
        user = SocialUser(provider=provider, uid=uid)
    user.name = profile.get("name")
    user.email = profile.get("email")
    db.session.add(user)
    db.session.commit()

    return jsonify({
        "id": user.id,
        "provider": provider,
        "name": user.name,
        "email": user.email
    })

@app.route("/api/user/<int:id>")
def get_user(id):
    user = SocialUser.query.get_or_404(id)
    return jsonify({
        "id": user.id,
        "provider": user.provider,
        "uid": user.uid,
        "name": user.name,
        "email": user.email
    })

if __name__ == "__main__":
    app.run(debug=True)
