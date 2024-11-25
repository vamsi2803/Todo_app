from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from models import db, bcrypt, User, ToDo
from forms import RegistrationForm, LoginForm

app = Flask(__name__)

# Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = 'your_secret_key'

# Initialize extensions
db.init_app(app)
bcrypt.init_app(app)

# LoginManager setup
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Create tables before the first request
with app.app_context():
    db.create_all()

# Routes
@app.route('/', methods=['GET', 'POST'])
@login_required
def read():
    if request.method == 'POST':
        title = request.form['title']
        desc = request.form['desc']
        todo = ToDo(title=title, desc=desc, user_id=current_user.id)
        db.session.add(todo)
        db.session.commit()
        return redirect('/')
    alltodos = ToDo.query.filter_by(user_id=current_user.id).all()
    return render_template('index.html', alltodos=alltodos)

@app.route('/delete/<int:sno>')
@login_required
def delete(sno):
    todo = ToDo.query.filter_by(sno=sno, user_id=current_user.id).first()
    if todo:
        db.session.delete(todo)
        db.session.commit()
    return redirect('/')

@app.route('/update/<int:sno>', methods=['GET', 'POST'])
@login_required
def update(sno):
    todo = ToDo.query.filter_by(sno=sno, user_id=current_user.id).first()
    if not todo:
        return redirect('/')
    if request.method == 'POST':
        todo.title = request.form['title']
        todo.desc = request.form['desc']
        db.session.commit()
        return redirect('/')
    return render_template('update.html', todo=todo)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('read'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('read'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=True)
            flash('Login successful!', 'success')
            return redirect(url_for('read'))
        else:
            flash('Login failed. Please check your email and password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
