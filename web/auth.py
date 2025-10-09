from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin
from passlib.hash import bcrypt
from db.models import db, User

bp_auth = Blueprint("auth", __name__)

class UserLogin(User, UserMixin):
    pass

def init_login(app):
    lm = LoginManager(app)
    lm.login_view = "auth.login"

    @lm.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    return lm

@bp_auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        pw = bcrypt.hash(request.form["password"])
        if User.query.filter_by(email=email).first():
            flash("Ese correo ya está registrado.")
            return redirect(url_for("auth.register"))
        u = User(email=email, password_hash=pw)
        db.session.add(u); db.session.commit()
        flash("Registro exitoso. Inicia sesión.")
        return redirect(url_for("auth.login"))
    return render_template("register.html")

@bp_auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        pw = request.form["password"]
        u = User.query.filter_by(email=email).first()
        if not u or not bcrypt.verify(pw, u.password_hash):
            flash("Credenciales inválidas.")
            return redirect(url_for("auth.login"))
        login_user(u)
        return redirect(url_for("web.inbox"))
    return render_template("login.html")

@bp_auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
