from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.after_request
def add_header(response):
    response.cache_control.no_store = True
    return response

app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Ani%401112@localhost/calorie_tracker'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ---------- MODELS ----------

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Food(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    calories_per_100g = db.Column(db.Integer, nullable=False)

class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    grams = db.Column(db.Integer, nullable=False)
    calories = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey('food.id'), nullable=False)

    food = db.relationship("Food", backref="meals")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------- ROUTES ----------

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash("Account created! Please log in.", "success")
        return redirect(url_for('login'))
    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            # redirect admin to admin dashboard
            if user.is_admin:
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        else:
            flash("Login failed! Check email and password", "danger")
    return render_template("login.html")

@app.route('/dashboard')
@login_required
def dashboard():
    meals = Meal.query.filter_by(user_id=current_user.id).all()
    total_calories = sum(meal.calories for meal in meals)
    return render_template('dashboard.html', meals=meals, total_calories=total_calories)

@app.route('/add_meal', methods=['GET', 'POST'])
@login_required
def add_meal():
    foods = Food.query.all()
    if request.method == 'POST':
        food_id = int(request.form['food_id'])
        grams = int(request.form['grams'])
        food = Food.query.get(food_id)
        calories = int((food.calories_per_100g * grams) / 100)
        meal = Meal(food_id=food_id, grams=grams, calories=calories, user_id=current_user.id)
        db.session.add(meal)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template("add_meal.html", foods=foods)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# ---------- ADMIN ROUTES ----------

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash("⚠️ Access denied! Only admin can access this page.", "danger")
        return redirect(url_for('dashboard'))
    foods = Food.query.all()
    return render_template('admin_dashboard.html', foods=foods)

@app.route('/admin/add_food', methods=['GET', 'POST'])
@login_required
def admin_add_food():
    if not current_user.is_admin:
        flash("⚠️ Access denied! Only admin can add foods.", "danger")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form['name']
        calories = int(request.form['calories'])
        existing = Food.query.filter_by(name=name).first()
        if existing:
            flash("⚠️ Food already exists!", "warning")
        else:
            new_food = Food(name=name, calories_per_100g=calories)
            db.session.add(new_food)
            db.session.commit()
            flash("✅ Food added successfully!", "success")
        return redirect(url_for('admin_add_food'))

    return render_template('admin_add_food.html')

# ---------- APP INIT ----------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Create default admin user
        if not User.query.filter_by(email="admin@example.com").first():
            admin_password = bcrypt.generate_password_hash("Ani@1112").decode('utf-8')
            admin_user = User(username="Admin", email="admin@example.com", password=admin_password, is_admin=True)
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Admin user created!")

        # Insert default foods if table is empty
        if not Food.query.first():
            db.session.add_all([
                Food(name="Rice", calories_per_100g=130),
                Food(name="Chicken", calories_per_100g=239),
                Food(name="Apple", calories_per_100g=52),
                Food(name="Milk", calories_per_100g=42),
                Food(name="Bread", calories_per_100g=265),
                Food(name="Egg", calories_per_100g=155),
                Food(name="Banana", calories_per_100g=89),
                Food(name="Potato", calories_per_100g=77),
                Food(name="Cheese", calories_per_100g=402),
                Food(name="Fish", calories_per_100g=206),
                Food(name="Oats", calories_per_100g=389),
                Food(name="Yogurt", calories_per_100g=59),
                Food(name="Tomato", calories_per_100g=18),
                Food(name="Cucumber", calories_per_100g=16),
                Food(name="Carrot", calories_per_100g=41),
                Food(name="Spinach", calories_per_100g=23),
                Food(name="Pasta", calories_per_100g=131),
                Food(name="Beef", calories_per_100g=250),
                Food(name="Pork", calories_per_100g=242),
                Food(name="Lentils", calories_per_100g=116),
                Food(name="Almonds", calories_per_100g=579),
                Food(name="Peanuts", calories_per_100g=567),
                Food(name="Walnuts", calories_per_100g=654),
                Food(name="Avocado", calories_per_100g=160),
                Food(name="Mango", calories_per_100g=60)
            ])
            db.session.commit()
            print("✅ Default foods inserted!")

    app.run(debug=True)



