import os
from flask import Flask, redirect, url_for, jsonify
from authlib.integrations.flask_client import OAuth
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from helpers import fetch_facebook_profile

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///db.sqlite3")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
oauth = OAuth(app)

# Register Facebook OAuth2
oauth.register(
    name="facebook",
    client_id=os.getenv("FACEBOOK_CLIENT_ID"),
    client_secret=os.getenv("FACEBOOK_CLIENT_SECRET"),
    access_token_url="https://graph.facebook.com/v10.0/oauth/access_token",
    authorize_url="https://www.facebook.com/v10.0/dialog/oauth",
    api_base_url="https://graph.facebook.com/v10.0/",
    client_kwargs={"scope": "email"}
)

class SocialUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(20), nullable=False)
    uid = db.Column(db.String(200), unique=True, nullable=False)
    name = db.Column(db.String(200))
    email = db.Column(db.String(200))

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return "Welcome to Social Auth API"

@app.route("/login/facebook")
def login_facebook():
    redirect_uri = url_for("auth_facebook", _external=True)
    return oauth.facebook.authorize_redirect(redirect_uri)

@app.route("/auth/facebook")
def auth_facebook():
    # 1) Exchange code for tokens
    token = oauth.facebook.authorize_access_token()
    access_token = token["access_token"]

    # 2) Fetch profile via Graph API helper
    profile = fetch_facebook_profile(access_token)

    # 3) Upsert into our DB
    uid = profile["id"]
    user = SocialUser.query.filter_by(provider="facebook", uid=uid).first()
    if not user:
        user = SocialUser(provider="facebook", uid=uid)
    user.name = profile.get("name")
    user.email = profile.get("email")
    db.session.add(user)
    db.session.commit()

    # 4) Return JSON
    return jsonify({
        "id": user.id,
        "provider": user.provider,
        "uid": user.uid,
        "name": user.name,
        "email": user.email
    })

if __name__ == "__main__":
    app.run(debug=True)
