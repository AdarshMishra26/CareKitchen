from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///communitycarekitchen.db'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # FoodDonor, NGO, BudgetEater
    bio = db.Column(db.Text, nullable=True)
    address = db.Column(db.String(200), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)

# Food Item Model
class FoodItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    food_type = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    image_filename = db.Column(db.String(200), nullable=True)
    expiry_date = db.Column(db.DateTime, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('food_category.id'), nullable=False)

# Rating and Review Model
class RatingReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rated_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rated_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_item.id'))
    rating = db.Column(db.Integer, nullable=False)
    review = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Donation History Model
class DonationHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_item.id'), nullable=False)
    donated_at = db.Column(db.DateTime, default=datetime.utcnow)

# Request History Model
class RequestHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_item.id'), nullable=False)
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)

# Notification Model
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Food Category Model
class FoodCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

# Feedback Model
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# User Activity Log
class UserActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize Flask-Mail for sending email notifications
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
mail = Mail(app)

# Routes
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        user_type = request.form['user_type']

        new_user = User(username=username, email=email, password=password, user_type=user_type)
        db.session.add(new_user)
        db.session.commit()

        flash('User registered successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/')
@app.route('/index')
def index():
    food_items = FoodItem.query.filter_by(available=True).all()
    return render_template('index.html', food_items=food_items)

@app.route('/add_food_item', methods=['GET', 'POST'])
@login_required
def add_food_item():
    if request.method == 'POST':
        food_type = request.form['food_type']
        quantity = int(request.form['quantity'])
        price = float(request.form['price'])
        location = request.form['location']

        new_food_item = FoodItem(user_id=current_user.id, food_type=food_type, quantity=quantity, price=price, location=location)
        db.session.add(new_food_item)
        db.session.commit()

        flash('Food item added successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('add_food_item.html')

@app.route('/edit_food_item/<int:food_item_id>', methods=['GET', 'POST'])
@login_required
def edit_food_item(food_item_id):
    food_item = FoodItem.query.get_or_404(food_item_id)
    if food_item.user_id != current_user.id:
        flash('You do not have permission to edit this food item.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        food_item.food_type = request.form['food_type']
        food_item.quantity = int(request.form['quantity'])
        food_item.price = float(request.form['price'])
        food_item.location = request.form['location']
        db.session.commit()

        flash('Food item updated successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('edit_food_item.html', food_item=food_item)

@app.route('/delete_food_item/<int:food_item_id>', methods=['POST'])
@login_required
def delete_food_item(food_item_id):
    food_item = FoodItem.query.get_or_404(food_item_id)
    if food_item.user_id != current_user.id:
        flash('You do not have permission to delete this food item.', 'danger')
        return redirect(url_for('index'))

    db.session.delete(food_item)
    db.session.commit()
    flash('Food item deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/search_food_items', methods=['GET', 'POST'])
@login_required
def search_food_items():
    if request.method == 'POST':
        food_type = request.form['food_type']
        location = request.form['location']

        food_items = FoodItem.query.filter_by(food_type=food_type, location=location, available=True).all()
        return render_template('search_results.html', food_items=food_items)
    return render_template('search_food_items.html')

@app.route('/request_food_item/<int:food_item_id>', methods=['GET', 'POST'])
@login_required
def request_food_item(food_item_id):
    food_item = FoodItem.query.get_or_404(food_item_id)
    if request.method == 'POST':
        # Code to request a food item and arrange pickup
        pass
    return render_template('request_food_item.html', food_item=food_item)

@app.route('/rate_review/<int:user_id>/<int:food_item_id>', methods=['GET', 'POST'])
@login_required
def rate_review(user_id, food_item_id):
    if request.method == 'POST':
        rating = int(request.form['rating'])
        review = request.form['review']

        # Save rating and review to the database
        new_rating_review = RatingReview(rated_user_id=user_id, rated_by_user_id=current_user.id, food_item_id=food_item_id, rating=rating, review=review)
        db.session.add(new_rating_review)
        db.session.commit()

        flash('Rating and review submitted successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('rate_review.html', user_id=user_id, food_item_id=food_item_id)

@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('profile.html', user=user)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = current_user
    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        user.bio = request.form['bio']
        user.address = request.form['address']
        user.phone_number = request.form['phone_number']
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile', user_id=user.id))
    return render_template('edit_profile.html', user=user)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    user = current_user
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_new_password = request.form['confirm_new_password']

        if not check_password_hash(user.password, current_password):
            flash('Current password is incorrect', 'danger')
        elif new_password != confirm_new_password:
            flash('New password and confirm password do not match', 'danger')
        else:
            user.password = generate_password_hash(new_password)
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('profile', user_id=user.id))
    return render_template('change_password.html')

@app.route('/verify_account/<int:user_id>')
@login_required
def verify_account(user_id):
    if current_user.user_type != 'NGO':
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('index'))

    user = User.query.get_or_404(user_id)
    user.is_verified = True
    db.session.commit()
    flash(f'{user.username}\'s account has been verified successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/donation_history')
@login_required
def donation_history():
    donations = DonationHistory.query.filter_by(user_id=current_user.id).all()
    return render_template('donation_history.html', donations=donations)

@app.route('/request_history')
@login_required
def request_history():
    requests = RequestHistory.query.filter_by(user_id=current_user.id).all()
    return render_template('request_history.html', requests=requests)

@app.route('/notifications')
@login_required
def notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id).all()
    return render_template('notifications.html', notifications=notifications)

@app.route('/analytics')
@login_required
def analytics():
    total_food_donated = FoodItem.query.filter_by(available=False).count()
    users_helped = User.query.filter_by(user_type='BudgetEater').count()
    return render_template('analytics.html', total_food_donated=total_food_donated, users_helped=users_helped)

@app.route('/upload_image/<int:food_item_id>', methods=['POST'])
@login_required
def upload_image(food_item_id):
    food_item = FoodItem.query.get_or_404(food_item_id)
    if food_item.user_id != current_user.id:
        flash('You do not have permission to upload an image for this food item.', 'danger')
        return redirect(url_for('index'))

    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        food_item.image_filename = filename
        db.session.commit()
        flash('Image successfully uploaded', 'success')
        return redirect(url_for('index'))
    else:
        flash('Invalid file type')
        return redirect(request.url)

@app.route('/send_feedback', methods=['POST'])
@login_required
def send_feedback():
    message = request.form['message']
    new_feedback = Feedback(user_id=current_user.id, message=message)
    db.session.add(new_feedback)
    db.session.commit()
    flash('Thank you for your feedback!', 'success')
    return redirect(url_for('index'))

@app.route('/activity_log')
@login_required
def activity_log():
    activities = UserActivity.query.filter_by(user_id=current_user.id).all()
    return render_template('activity_log.html', activities=activities)

@app.route('/ngo_dashboard')
@login_required
def ngo_dashboard():
    if current_user.user_type != 'NGO':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('index'))

    # Logic to fetch data for the dashboard

    return render_template('ngo_dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)
