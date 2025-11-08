from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from flask_mail import Mail, Message
import os
import uuid
import requests
import json
import random
import string
from dotenv import load_dotenv


try:
    from PIL import Image
except Exception:
    Image = None

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv("SECRET_KEY")
app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER")
app.config['MAIL_PORT'] = int(os.getenv("MAIL_PORT", 587))
app.config['MAIL_USE_TLS'] = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_DEFAULT_SENDER'] = ( 'TrekMate', os.getenv("MAIL_DEFAULT_SENDER") )
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD') 


# Database Configuration
load_dotenv()
basedir = os.path.abspath(os.path.dirname(__file__))
db_url = os.getenv('INTERNAL_DATABASE_URL') or os.getenv('DATABASE_URL')
if not db_url:
    db_url = f"sqlite:///{os.path.join(basedir, 'trekmate.db')}"

# Normalize postgres scheme for SQLAlchemy/psycopg2
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql+psycopg2://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

mail = Mail(app)

# File Upload Configuration
UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads', 'comments')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# OpenWeatherMap API Configuration
OPENWEATHER_BASE_URL = os.getenv('OPENWEATHER_BASE_URL', 'https://api.openweathermap.org/data/2.5/weather')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, file_type='trek'):
    """Save uploaded file with unique filename
    
    Args:
        file: The file to save
        file_type: 'trek' or 'comment' to determine the save location
    """
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{uuid.uuid4().hex}_{name}{ext}"
        
        if file_type == 'trek':
            # Use the existing trekimages folder
            upload_folder = os.path.join(basedir, 'static', 'trekimages')
        elif file_type == 'comment':
            # Use the comments upload folder
            upload_folder = os.path.join(basedir, 'static', 'uploads', 'comments')
        elif file_type == 'post':
            # Use the posts upload folder
            upload_folder = os.path.join(basedir, 'static', 'uploads', 'posts')
        else:
            upload_folder = os.path.join(basedir, 'static', 'uploads')
            
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)

        # Attempt to compress/resize images for posts/comments
        if file_type in ('post', 'comment') and Image is not None:
            try:
                ext = ext.lower()
                # Open image
                with Image.open(file_path) as im:
                    im_format = im.format
                    # Convert mode for JPEG if needed
                    if im.mode in ("P", "RGBA") and (ext in ['.jpg', '.jpeg'] or (im_format and im_format.upper() == 'JPEG')):
                        im = im.convert('RGB')
                    # Resize if larger than 1600x1600 preserving aspect ratio
                    max_size = (1600, 1600)
                    im.thumbnail(max_size, Image.LANCZOS)
                    save_kwargs = {}
                    if ext in ['.jpg', '.jpeg'] or (im_format and im_format.upper() == 'JPEG'):
                        save_kwargs.update({'quality': 80, 'optimize': True, 'progressive': True})
                        im.save(file_path, format='JPEG', **save_kwargs)
                    elif ext in ['.png'] or (im_format and im_format.upper() == 'PNG'):
                        save_kwargs.update({'optimize': True})
                        im.save(file_path, format='PNG', **save_kwargs)
                    else:
                        # For other formats, try to save with optimize when possible
                        im.save(file_path)
            except Exception:
                # If optimization fails, keep original file
                pass

        return unique_filename
    return None

def get_trek_image_filename(trek_name):
    """Map trek names to their corresponding image filenames"""
    # Comprehensive mapping of trek names to image filenames
    image_mapping = {
        'Rajgad Fort': 'rajgad.jpg',
        'Andharban Jungle Trek': 'andharban.jpg',
        'Lohagad-Visapur Fort': 'lohagad-visapur.jpg',
        'Tikona Fort': 'tikona.jpg',
        'Torna Fort': 'torna.webp',
        'Rajmachi Fort': 'rajmachi.jpg',
        'Duke\'s Nose': 'dukes-nose.jpg',
        'Devkund Waterfall': 'devkund.jpg',
        'Prabalgad–Kalavantin Durg': 'Prabalgad-kalavanti.jpg',
        'Irshalgad Fort': 'irshalgad.webp',
        'Peb–Matheran One Tree Hill': 'one tree hill.jpg',
        'Karnala Fort': 'karnala.jpg',
        'Sondai Fort': 'sondai.jpg',
        'Kalsubai Peak': 'kalsubai.png',
        'Harihar Fort': 'harihar.png',
        'Ratangad Fort': 'ratangad.jpg',
        'Anjaneri–Brahmagiri Hills': 'Anjaneri–Brahmagiri.jpg',
        'Alang–Madan–Kulang (AMK) Forts': 'Alang–Madan–Kulang.jpg',
        'Randha Falls': 'randha-falls.jpg',
        'Ajinkyatara–Sajjangad Forts': 'Ajinkyatara–Sajjangad.jpg',
        'Kaas Plateau': 'Kaas-Plateau.jpg',
        'Arthur\'s Seat Trail': 'Arthur_ Seat.jpg',
        'Thoseghar Waterfalls': 'thoseghar.jpg',
        'Savlya Ghat': 'savlyaghat.png',
        'Harishchandragad Fort': 'harishchandragad.png',
        'Kalu Waterfall': 'kaluwaterfall.png',
        'Adrai Jungle Trek': 'Aadrai_Jungle_Trek.jpg',
        'Nanemachi Waterfall': 'nanemachi.webp'
    }
    
    # Return the mapped filename or a default image
    return image_mapping.get(trek_name, 'img1.png')

def get_weather_data(city_name, region_name=None):
    """Fetch weather data from OpenWeatherMap API with smart fallbacks"""
    try:
        # If no API key is set or it's the default one, return mock data
        if not OPENWEATHER_API_KEY or OPENWEATHER_API_KEY == 'your_api_key_here' or OPENWEATHER_API_KEY == '6d9f243af7323969201f39ff6032e487':
            return {
                'temperature': 22,
                'description': 'Clear sky',
                'main': 'Clear',
                'icon': '01d',
                'humidity': 65,
                'wind_speed': 3.2,
                'location': city_name or 'Trek Location'
            }
        
        # Location mapping for problematic base villages to nearby major cities
        location_fallbacks = {
            'Torna Peth': 'Pune',
            'Udhewadi / Kondhane': 'Lonavala', 
            'Kondhane': 'Lonavala',
            'Udhewadi': 'Lonavala',
            'Bhira / Tamhini': 'Mulshi',
            'Bhira': 'Mulshi',
            'Tamhini': 'Mulshi', 
            'Thakurwadi / Prabalmachi': 'Karjat',
            'Thakurwadi': 'Karjat',
            'Prabalmachi': 'Karjat',
            'Malshej': 'Junnar',
            'Rajur': 'Akole'
        }
        
        # List of locations to try in order
        locations_to_try = []
        
        if city_name:
            # Clean up city name (handle multiple names)
            clean_city = city_name.split(' / ')[0].strip() if ' / ' in city_name else city_name.strip()
            locations_to_try.append(clean_city)
            
            # Add fallback if available
            if city_name in location_fallbacks:
                locations_to_try.append(location_fallbacks[city_name])
            if clean_city in location_fallbacks:
                locations_to_try.append(location_fallbacks[clean_city])
        
        # Add region-based fallbacks
        region_fallbacks = {
            'Pune – Lonavala – Mulshi Belt': 'Pune',
            'Mumbai – Panvel – Karjat – Matheran Belt': 'Karjat',
            'Nashik – Bhandardara Belt': 'Nashik',
            'Satara – Mahabaleshwar – Kaas Belt': 'Mahabaleshwar',
            'Malshej Ghat Belt': 'Junnar',
            'Konkan Belt': 'Ratnagiri'
        }
        
        if region_name and region_name in region_fallbacks:
            fallback_city = region_fallbacks[region_name]
            if fallback_city not in locations_to_try:
                locations_to_try.append(fallback_city)
        
        # If no specific locations, use default fallback
        if not locations_to_try:
            locations_to_try = ['Pune']
        
        # Try each location until we get a successful response
        for location in locations_to_try:
            try:
                query = f"{location},Maharashtra,IN" if region_name and 'Maharashtra' in region_name else f"{location},IN"
                
                params = {
                    'q': query,
                    'appid': OPENWEATHER_API_KEY,
                    'units': 'metric'
                }
                
                response = requests.get(OPENWEATHER_BASE_URL, params=params, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        'temperature': round(data['main']['temp']),
                        'description': data['weather'][0]['description'].title(),
                        'main': data['weather'][0]['main'],
                        'icon': data['weather'][0]['icon'],
                        'humidity': data['main']['humidity'],
                        'wind_speed': data.get('wind', {}).get('speed', 0),
                        'location': f"{data['name']} (near {city_name or 'trek area'})" if location != (city_name or '').split(' / ')[0] else data['name']
                    }
            except Exception:
                continue
        
        # If all locations fail, return fallback data
        return {
            'temperature': 25,
            'description': 'Cloudy',
            'main': 'Unknown',
            'icon': '01d',
            'humidity': 60,
            'wind_speed': 2.5,
            'location': city_name or 'Trek Location'
        }
        
    except Exception as e:
        # Return fallback data on any error
        return {
            'temperature': 24,
            'description': 'Weather data unavailable',
            'main': 'Unknown',
            'icon': '01d',
            'humidity': 55,
            'wind_speed': 2.0,
            'location': city_name or 'Trek Location'
        }

# Initialize extensions
db = SQLAlchemy(app)
csrf = CSRFProtect(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Make trek image function available in templates
app.jinja_env.globals['get_trek_image_filename'] = get_trek_image_filename

# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'user' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'

# Trek Models
class TrekRegion(db.Model):
    __tablename__ = 'trek_regions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    treks = db.relationship('Trek', backref='region', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Trek(db.Model):
    __tablename__ = 'treks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.Text)  # Full name with alternate names
    gen_z_intro = db.Column(db.Text)  # Gen Z style introduction
    height_ft = db.Column(db.Integer)  # Height in feet
    height_m = db.Column(db.Integer)   # Height in meters
    distance_km = db.Column(db.Float)  # Distance in kilometers
    duration = db.Column(db.String(200))  # Duration description
    difficulty = db.Column(db.String(50))  # Easy, Moderate, Hard
    difficulty_color = db.Column(db.String(20))  # Color code for difficulty
    best_season = db.Column(db.String(100))  # Best season to visit
    base_village = db.Column(db.String(200))  # Base village name
    region_id = db.Column(db.Integer, db.ForeignKey('trek_regions.id'))
    image_filename = db.Column(db.String(255))  # Image filename for trek
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    private_routes = db.relationship('PrivateRoute', backref='trek', lazy=True, cascade='all, delete-orphan')
    public_routes = db.relationship('PublicRoute', backref='trek', lazy=True, cascade='all, delete-orphan')
    highlights = db.relationship('TrekHighlight', backref='trek', lazy=True, cascade='all, delete-orphan')

class PrivateRoute(db.Model):
    __tablename__ = 'private_routes'
    id = db.Column(db.Integer, primary_key=True)
    trek_id = db.Column(db.Integer, db.ForeignKey('treks.id'), nullable=False)
    from_city = db.Column(db.String(100), nullable=False)  # Pune, Mumbai, etc.
    route_description = db.Column(db.Text)  # Full route description
    distance_km = db.Column(db.Integer)  # Distance in km
    duration = db.Column(db.String(50))  # Duration like "2 hrs", "3.5 hrs"
    road_condition = db.Column(db.Text)  # Road condition details
    parking_info = db.Column(db.Text)  # Parking availability and cost
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class PublicRoute(db.Model):
    __tablename__ = 'public_routes'
    id = db.Column(db.Integer, primary_key=True)
    trek_id = db.Column(db.Integer, db.ForeignKey('treks.id'), nullable=False)
    from_city = db.Column(db.String(100), nullable=False)  # Pune, Mumbai, etc.
    route_steps = db.Column(db.Text)  # Step-by-step route instructions
    total_time = db.Column(db.String(50))  # Total travel time
    frequency = db.Column(db.String(200))  # Frequency of transport
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TrekHighlight(db.Model):
    __tablename__ = 'trek_highlights'
    id = db.Column(db.Integer, primary_key=True)
    trek_id = db.Column(db.Integer, db.ForeignKey('treks.id'), nullable=False)
    highlight = db.Column(db.Text)  # Special features or highlights
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Comment Model for Trek Reviews
class TrekComment(db.Model):
    __tablename__ = 'trek_comments'
    id = db.Column(db.Integer, primary_key=True)
    trek_id = db.Column(db.Integer, db.ForeignKey('treks.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer)  # 1-5 star rating
    image_filename = db.Column(db.String(255))  # Uploaded image filename
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    trek = db.relationship('Trek', backref='comments')
    user = db.relationship('User', backref='comments')

# Admin Notification Model
class AdminNotification(db.Model):
    __tablename__ = 'admin_notifications'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # 'new_comment', 'new_user', etc.
    message = db.Column(db.Text, nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey('treks.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('trek_comments.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # User who triggered notification
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    trek = db.relationship('Trek')
    comment = db.relationship('TrekComment')
    user = db.relationship('User')

# Saved Trek Model
class SavedTrek(db.Model):
    __tablename__ = 'saved_treks'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey('treks.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('saved_treks', lazy=True, cascade='all, delete-orphan'))
    trek = db.relationship('Trek', backref='saved_by_users')
    
    # Unique constraint to prevent duplicate saves
    __table_args__ = (db.UniqueConstraint('user_id', 'trek_id', name='unique_user_trek'),)

# Trek Feed Models
class TrekPost(db.Model):
    __tablename__ = 'trek_posts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trek_name = db.Column(db.String(255), nullable=False)
    trek_date = db.Column(db.Date, nullable=True)
    trek_location = db.Column(db.String(255), nullable=True)
    user_location = db.Column(db.String(255), nullable=True)
    caption = db.Column(db.Text, nullable=True)
    looking_for_buddies = db.Column(db.Boolean, default=False)
    trek_status = db.Column(db.String(20), nullable=True)  # 'going' or 'completed'
    image_filename = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('trek_posts', lazy=True))
    reactions = db.relationship('TrekPostReaction', backref='post', cascade='all, delete-orphan')
    comments = db.relationship('TrekPostComment', backref='post', cascade='all, delete-orphan')

class TrekPostReaction(db.Model):
    __tablename__ = 'trek_post_reactions'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('trek_posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('trek_post_reactions', lazy=True, cascade='all, delete-orphan'))
    __table_args__ = (db.UniqueConstraint('post_id', 'user_id', name='unique_post_user_reaction'),)

class TrekPostComment(db.Model):
    __tablename__ = 'trek_post_comments'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('trek_posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('trek_post_comments.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('trek_post_comments', lazy=True, cascade='all, delete-orphan'))
    replies = db.relationship('TrekPostComment', backref=db.backref('parent', remote_side=[id]), cascade='all, delete-orphan')

class UserNotification(db.Model):
    __tablename__ = 'user_notifications'
    id = db.Column(db.Integer, primary_key=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'reaction', 'comment', 'reply'
    message = db.Column(db.Text, nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('trek_posts.id'), nullable=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('trek_post_comments.id'), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    recipient = db.relationship('User', backref=db.backref('notifications', lazy=True, cascade='all, delete-orphan'))
    post = db.relationship('TrekPost')
    comment = db.relationship('TrekPostComment')

def create_notification(recipient_id, notif_type, message, post_id=None, comment_id=None):
    try:
        if recipient_id and current_user.is_authenticated and recipient_id != current_user.id:
            n = UserNotification(
                recipient_id=recipient_id,
                type=notif_type,
                message=message,
                post_id=post_id,
                comment_id=comment_id
            )
            db.session.add(n)
            db.session.commit()
    except Exception:
        db.session.rollback()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    """Home page route"""
    return render_template('index.html')

# Health check endpoints for Render
@app.route('/health')
def health():
    return 'ok', 200

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page route"""
    # If user is already logged in, redirect to home
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please fill in all fields.', 'error')
            return render_template('login.html')
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash(f'Welcome back, {user.name}!', 'success')
            
            # Redirect to next page or home, tagging first page load after login
            next_page = request.args.get('next')
            if next_page:
                dest = next_page + ('&' if '?' in next_page else '?') + 'just_logged_in=1'
                return redirect(dest)
            else:
                return redirect(url_for('home', just_logged_in=1))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html')

# Generate a random 6-digit OTP
def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

# Send OTP email
def send_otp_email(email, otp):
    try:
        msg = Message('TrekMate Password Reset Code', recipients=[email])
        msg.body = f'''Your password reset code is: {otp}

This code will expire in 10 minutes.

Password yaad rakha karna!!

If you did not request a password reset, please ignore this email.

-Adil Shaikh
'''
        mail.send(msg)
        return True
    except Exception as e:
        app.logger.error(f"Failed to send email: {str(e)}")
        return False

# Generic helper to send user emails (used for comment notifications)
def send_user_email(to_email, subject, body):
    try:
        if not to_email:
            return False
        msg = Message(subject, recipients=[to_email])
        msg.body = body
        mail.send(msg)
        return True
    except Exception as e:
        app.logger.error(f"Failed to send user email: {str(e)}")
        return False

# Send Registration OTP email
def send_registration_otp_email(email, otp):
    try:
        subject = 'TrekMate Registration Code'
        body = f'''Your registration verification code is: {otp}

This code will expire in 10 minutes.

If you did not attempt to register, you can ignore this email.'''
        return send_user_email(email, subject, body)
    except Exception as e:
        app.logger.error(f"Failed to send registration OTP email: {str(e)}")
        return False

# Forgot password route
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        
        # Always show the same message regardless of whether the email exists
        # This prevents email enumeration attacks
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate OTP and store in session with timestamp
            otp = generate_otp()
            session['reset_email'] = email
            session['reset_otp'] = otp
            session['reset_otp_time'] = datetime.utcnow().timestamp()
            
            # Try to send the email
            email_sent = send_otp_email(email, otp)
            
            if not email_sent:
                # If email fails, log it but don't tell the user
                app.logger.error(f"Failed to send OTP email to {email}")
        
        # Always show the same message
        flash('If this email is registered, an OTP has been sent.', 'info')
        return redirect(url_for('verify_otp'))
    
    return render_template('forgot_password.html')

# Verify OTP route
@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    # Check if reset process was initiated
    if 'reset_email' not in session or 'reset_otp' not in session or 'reset_otp_time' not in session:
        flash('Please start the password reset process again.', 'warning')
        return redirect(url_for('forgot_password'))
    
    # Check if OTP has expired (10 minutes)
    otp_time = session.get('reset_otp_time')
    current_time = datetime.utcnow().timestamp()
    
    if current_time - otp_time > 600:  # 10 minutes in seconds
        # Clear session data
        session.pop('reset_email', None)
        session.pop('reset_otp', None)
        session.pop('reset_otp_time', None)
        
        flash('Your verification code has expired. Please request a new one.', 'warning')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        stored_otp = session.get('reset_otp')
        
        if entered_otp == stored_otp:
            # OTP is correct, allow password reset
            session['otp_verified'] = True
            return redirect(url_for('reset_password'))
        else:
            flash('Invalid verification code. Please try again.', 'danger')
    
    return render_template('verify_otp.html')

# Reset password route
@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
        
    # Check if user has verified OTP
    if 'otp_verified' not in session or not session.get('otp_verified') or 'reset_email' not in session:
        flash('Please complete the verification process first.', 'warning')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('reset_password.html')
        
        # Update the user's password
        email = session.get('reset_email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            user.password_hash = generate_password_hash(password)
            db.session.commit()
            
            # Clear all session data related to password reset
            session.pop('reset_email', None)
            session.pop('reset_otp', None)
            session.pop('reset_otp_time', None)
            session.pop('otp_verified', None)
            
            flash('Your password has been reset successfully. You can now log in with your new password.', 'success')
            return redirect(url_for('login'))
        else:
            flash('An error occurred. Please try again.', 'danger')
            return redirect(url_for('forgot_password'))
    
    return render_template('reset_password.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register page route"""
    # If user is already logged in, redirect to home
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        action = request.form.get('action')

        # Step 1: Send OTP to provided email
        if action == 'send_otp':
            name = request.form.get('name')
            email = request.form.get('email')

            if not name or not email:
                flash('Please provide your name and a valid email.', 'error')
                return render_template('register.html')

            # Prevent registering existing email
            if User.query.filter_by(email=email).first():
                flash('Email address already registered. Please use a different email or log in.', 'error')
                return render_template('register.html')

            otp = generate_otp()
            session['reg_name'] = name
            session['reg_email'] = email
            session['reg_otp'] = otp
            session['reg_otp_time'] = datetime.utcnow().timestamp()
            session['reg_verified'] = False

            email_sent = send_registration_otp_email(email, otp)
            if not email_sent:
                app.logger.error(f"Failed to send registration OTP to {email}")
            flash('If the email is valid, a verification code has been sent.', 'info')
            return render_template('register.html')

        # Step 2: Verify the OTP
        if action == 'verify_otp':
            entered_otp = request.form.get('otp')
            stored_otp = session.get('reg_otp')
            otp_time = session.get('reg_otp_time')

            if not stored_otp or not otp_time:
                flash('Please request a new verification code.', 'warning')
                return render_template('register.html')

            # Expiry 10 minutes
            if datetime.utcnow().timestamp() - otp_time > 600:
                session.pop('reg_otp', None)
                session.pop('reg_otp_time', None)
                session['reg_verified'] = False
                flash('Your verification code has expired. Please request a new one.', 'warning')
                return render_template('register.html')

            if entered_otp and entered_otp == stored_otp:
                session['reg_verified'] = True
                flash('Email verified. Please create your password.', 'success')
            else:
                flash('Invalid verification code. Please try again.', 'danger')
            return render_template('register.html')

        # Step 3: Complete registration after verification
        if action == 'complete_registration':
            if not session.get('reg_verified') or not session.get('reg_email') or not session.get('reg_name'):
                flash('Please verify your email before creating a password.', 'warning')
                return render_template('register.html')

            password = request.form.get('password')
            confirm_password = request.form.get('confirm')

            if not password or not confirm_password:
                flash('Please enter and confirm your password.', 'error')
                return render_template('register.html')

            if password != confirm_password:
                flash('Passwords do not match!', 'error')
                return render_template('register.html')

            if len(password) < 6:
                flash('Password must be at least 6 characters long.', 'error')
                return render_template('register.html')

            # Double-check email still not used
            email = session.get('reg_email')
            name = session.get('reg_name')
            if User.query.filter_by(email=email).first():
                flash('Email address already registered. Please login.', 'error')
                return redirect(url_for('login'))

            try:
                new_user = User(name=name, email=email, role='user')
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()

                # Clear registration session
                session.pop('reg_name', None)
                session.pop('reg_email', None)
                session.pop('reg_otp', None)
                session.pop('reg_otp_time', None)
                session.pop('reg_verified', None)

                flash(f'Registration successful! Welcome, {name}!', 'success')
                login_user(new_user)
                return redirect(url_for('home'))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred during registration. Please try again.', 'error')
                return render_template('register.html')

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """Logout route"""
    user_name = current_user.name
    logout_user()
    flash(f'Goodbye, {user_name}! You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    # Get user's saved treks
    saved_treks = db.session.query(SavedTrek, Trek).join(Trek).filter(SavedTrek.user_id == current_user.id).order_by(SavedTrek.created_at.desc()).all()
    
    # Get user's comments count
    comments_count = TrekComment.query.filter_by(user_id=current_user.id).count()
    
    return render_template('profile.html', user=current_user, saved_treks=saved_treks, comments_count=comments_count)

@app.route('/delete_trek/<int:trek_id>', methods=['POST'])
@login_required
def delete_trek(trek_id):
    """Delete a trek from the database"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('profile'))
    
    try:
        # Get the trek
        trek = Trek.query.get_or_404(trek_id)
        
        # Delete associated private routes
        PrivateRoute.query.filter_by(trek_id=trek_id).delete()
        
        # Delete associated public routes
        PublicRoute.query.filter_by(trek_id=trek_id).delete()
        
        # Delete associated saved treks
        SavedTrek.query.filter_by(trek_id=trek_id).delete()
        
        # Delete associated comments
        TrekComment.query.filter_by(trek_id=trek_id).delete()
        
        # Delete the trek
        db.session.delete(trek)
        db.session.commit()
        
        flash(f'Trek "{trek.name}" has been deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting trek: {str(e)}', 'danger')
    
    return redirect(url_for('trek_management'))

@app.route('/trek_management', methods=['GET', 'POST'])
@login_required
def trek_management():
    """Trek management page for admins"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('profile'))
        
    # Get all treks for the list
    treks = Trek.query.order_by(Trek.name).all()
        
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name')
            location = request.form.get('location')
            region_name = request.form.get('region')
            difficulty = request.form.get('difficulty')
            duration = request.form.get('duration')
            distance = request.form.get('distance')
            elevation = request.form.get('elevation')
            description = request.form.get('description')
            best_season = request.form.get('best_season')
            
            # Private route data - Pune
            private_pune_distance = request.form.get('private_pune_distance')
            private_pune_duration = request.form.get('private_pune_duration')
            private_pune_route_description = request.form.get('private_pune_route_description')
            private_pune_road_condition = request.form.get('private_pune_road_condition')
            private_pune_parking_info = request.form.get('private_pune_parking_info')
            
            # Private route data - Mumbai
            private_mumbai_distance = request.form.get('private_mumbai_distance')
            private_mumbai_duration = request.form.get('private_mumbai_duration')
            private_mumbai_route_description = request.form.get('private_mumbai_route_description')
            private_mumbai_road_condition = request.form.get('private_mumbai_road_condition')
            private_mumbai_parking_info = request.form.get('private_mumbai_parking_info')
            
            # Public route data - Pune
            public_pune_route_steps = request.form.get('public_pune_route_steps')
            public_pune_total_time = request.form.get('public_pune_total_time')
            public_pune_frequency = request.form.get('public_pune_frequency')
            
            # Public route data - Mumbai
            public_mumbai_route_steps = request.form.get('public_mumbai_route_steps')
            public_mumbai_total_time = request.form.get('public_mumbai_total_time')
            public_mumbai_frequency = request.form.get('public_mumbai_frequency')
            
            # Handle image upload
            image = request.files.get('image')
            image_filename = None
            if image and allowed_file(image.filename):
                image_filename = save_uploaded_file(image, file_type='trek')
                
            # Find or create region
            region = TrekRegion.query.filter_by(name=region_name).first()
            if not region:
                region = TrekRegion(name=region_name)
                db.session.add(region)
                db.session.flush()
                
            # Create new trek
            new_trek = Trek(
                name=name,
                full_name=name,
                gen_z_intro=description + "..." if description else "",
                height_ft=int(float(elevation) * 3.28084) if elevation else 0,  # Convert meters to feet
                height_m=int(float(elevation)) if elevation else 0,
                distance_km=float(distance) if distance else 0,
                duration=f"{duration} hours" if duration else "",
                difficulty=difficulty,
                difficulty_color="green" if difficulty == "Easy" else 
                              "teal" if difficulty == "Easy-Moderate" else 
                              "blue" if difficulty == "Moderate" else "orange",
                best_season=best_season,
                base_village=location,
                region_id=region.id,
                image_filename=image_filename
            )
            db.session.add(new_trek)
            db.session.flush()
            

            
            
            # Add private route information - Pune
            if private_pune_route_description:
                private_pune_route = PrivateRoute(
                    trek_id=new_trek.id,
                    from_city="Pune",
                    distance_km=int(private_pune_distance) if private_pune_distance else 0,
                    duration=f"{private_pune_duration} hrs" if private_pune_duration else "",
                    route_description=private_pune_route_description,
                    road_condition=private_pune_road_condition,
                    parking_info=private_pune_parking_info
                )
                db.session.add(private_pune_route)
            
            # Add private route information - Mumbai
            if private_mumbai_route_description:
                private_mumbai_route = PrivateRoute(
                    trek_id=new_trek.id,
                    from_city="Mumbai",
                    distance_km=int(private_mumbai_distance) if private_mumbai_distance else 0,
                    duration=f"{private_mumbai_duration} hrs" if private_mumbai_duration else "",
                    route_description=private_mumbai_route_description,
                    road_condition=private_mumbai_road_condition,
                    parking_info=private_mumbai_parking_info
                )
                db.session.add(private_mumbai_route)
            
            # Add public route information - Pune
            if public_pune_route_steps:
                public_pune_route = PublicRoute(
                    trek_id=new_trek.id,
                    from_city="Pune",
                    route_steps=public_pune_route_steps,
                    total_time=public_pune_total_time,
                    frequency=public_pune_frequency
                )
                db.session.add(public_pune_route)
                
            # Add public route information - Mumbai
            if public_mumbai_route_steps:
                public_mumbai_route = PublicRoute(
                    trek_id=new_trek.id,
                    from_city="Mumbai",
                    route_steps=public_mumbai_route_steps,
                    total_time=public_mumbai_total_time,
                    frequency=public_mumbai_frequency
                )
                db.session.add(public_mumbai_route)
                
            db.session.commit()
            flash('Trek added successfully!', 'success')
            return redirect(url_for('trek_management'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding trek: {str(e)}', 'danger')
    
    # Create a simple form context for the template
    from flask_wtf.csrf import generate_csrf
    form = {'csrf_token': generate_csrf()}
    
    # Get all treks for the admin view
    treks = Trek.query.all()
    return render_template('trek_management.html', form=form, treks=treks)

@app.route('/trek/<int:trek_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_trek(trek_id):
    """Edit an existing trek and its routes (admin only)"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('profile'))

    trek = Trek.query.get_or_404(trek_id)

    if request.method == 'POST':
        try:
            name = request.form.get('name')
            location = request.form.get('location')
            region_name = request.form.get('region')
            difficulty = request.form.get('difficulty')
            duration = request.form.get('duration')
            distance = request.form.get('distance')
            elevation = request.form.get('elevation')
            description = request.form.get('description')
            best_season = request.form.get('best_season')

            # Private route data - Pune
            private_pune_distance = request.form.get('private_pune_distance')
            private_pune_duration = request.form.get('private_pune_duration')
            private_pune_route_description = request.form.get('private_pune_route_description')
            private_pune_road_condition = request.form.get('private_pune_road_condition')
            private_pune_parking_info = request.form.get('private_pune_parking_info')

            # Private route data - Mumbai
            private_mumbai_distance = request.form.get('private_mumbai_distance')
            private_mumbai_duration = request.form.get('private_mumbai_duration')
            private_mumbai_route_description = request.form.get('private_mumbai_route_description')
            private_mumbai_road_condition = request.form.get('private_mumbai_road_condition')
            private_mumbai_parking_info = request.form.get('private_mumbai_parking_info')

            # Public route data - Pune
            public_pune_route_steps = request.form.get('public_pune_route_steps')
            public_pune_total_time = request.form.get('public_pune_total_time')
            public_pune_frequency = request.form.get('public_pune_frequency')

            # Public route data - Mumbai
            public_mumbai_route_steps = request.form.get('public_mumbai_route_steps')
            public_mumbai_total_time = request.form.get('public_mumbai_total_time')
            public_mumbai_frequency = request.form.get('public_mumbai_frequency')

            # Handle optional image upload (keep old if none)
            image = request.files.get('image')
            if image and allowed_file(image.filename):
                image_filename = save_uploaded_file(image, file_type='trek')
                trek.image_filename = image_filename or trek.image_filename

            # Find or create region
            if region_name:
                region = TrekRegion.query.filter_by(name=region_name).first()
                if not region:
                    region = TrekRegion(name=region_name)
                    db.session.add(region)
                    db.session.flush()
                trek.region_id = region.id

            # Update trek fields
            trek.name = name
            trek.full_name = name
            trek.gen_z_intro = (description + "...") if description else ""
            trek.height_ft = int(float(elevation) * 3.28084) if elevation else 0
            trek.height_m = int(float(elevation)) if elevation else 0
            trek.distance_km = float(distance) if distance else 0
            trek.duration = f"{duration} hours" if duration else ""
            trek.difficulty = difficulty
            trek.difficulty_color = (
                "green" if difficulty == "Easy" else
                "teal" if difficulty == "Easy-Moderate" else
                "blue" if difficulty == "Moderate" else "orange"
            )
            trek.best_season = best_season
            trek.base_village = location

            # Upsert PrivateRoute - Pune
            pune_private = PrivateRoute.query.filter_by(trek_id=trek.id, from_city="Pune").first()
            provided_pune = any([
                private_pune_route_description, private_pune_distance, private_pune_duration,
                private_pune_road_condition, private_pune_parking_info
            ])
            if provided_pune:
                if not pune_private:
                    pune_private = PrivateRoute(trek_id=trek.id, from_city="Pune")
                    db.session.add(pune_private)
                pune_private.distance_km = int(private_pune_distance) if private_pune_distance else 0
                pune_private.duration = f"{private_pune_duration} hrs" if private_pune_duration else ""
                pune_private.route_description = private_pune_route_description
                pune_private.road_condition = private_pune_road_condition
                pune_private.parking_info = private_pune_parking_info
            else:
                if pune_private:
                    db.session.delete(pune_private)

            # Upsert PrivateRoute - Mumbai
            mumbai_private = PrivateRoute.query.filter_by(trek_id=trek.id, from_city="Mumbai").first()
            provided_mumbai = any([
                private_mumbai_route_description, private_mumbai_distance, private_mumbai_duration,
                private_mumbai_road_condition, private_mumbai_parking_info
            ])
            if provided_mumbai:
                if not mumbai_private:
                    mumbai_private = PrivateRoute(trek_id=trek.id, from_city="Mumbai")
                    db.session.add(mumbai_private)
                mumbai_private.distance_km = int(private_mumbai_distance) if private_mumbai_distance else 0
                mumbai_private.duration = f"{private_mumbai_duration} hrs" if private_mumbai_duration else ""
                mumbai_private.route_description = private_mumbai_route_description
                mumbai_private.road_condition = private_mumbai_road_condition
                mumbai_private.parking_info = private_mumbai_parking_info
            else:
                if mumbai_private:
                    db.session.delete(mumbai_private)

            # Upsert PublicRoute - Pune
            pune_public = PublicRoute.query.filter_by(trek_id=trek.id, from_city="Pune").first()
            if public_pune_route_steps or public_pune_total_time or public_pune_frequency:
                if not pune_public:
                    pune_public = PublicRoute(trek_id=trek.id, from_city="Pune")
                    db.session.add(pune_public)
                pune_public.route_steps = public_pune_route_steps
                pune_public.total_time = public_pune_total_time
                pune_public.frequency = public_pune_frequency
            else:
                if pune_public:
                    db.session.delete(pune_public)

            # Upsert PublicRoute - Mumbai
            mumbai_public = PublicRoute.query.filter_by(trek_id=trek.id, from_city="Mumbai").first()
            if public_mumbai_route_steps or public_mumbai_total_time or public_mumbai_frequency:
                if not mumbai_public:
                    mumbai_public = PublicRoute(trek_id=trek.id, from_city="Mumbai")
                    db.session.add(mumbai_public)
                mumbai_public.route_steps = public_mumbai_route_steps
                mumbai_public.total_time = public_mumbai_total_time
                mumbai_public.frequency = public_mumbai_frequency
            else:
                if mumbai_public:
                    db.session.delete(mumbai_public)

            db.session.commit()
            flash('Trek updated successfully!', 'success')
            return redirect(url_for('trek_management'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating trek: {str(e)}', 'danger')

    # GET - render edit form with existing data
    from flask_wtf.csrf import generate_csrf
    form = {'csrf_token': generate_csrf()}
    pune_private = PrivateRoute.query.filter_by(trek_id=trek.id, from_city="Pune").first()
    mumbai_private = PrivateRoute.query.filter_by(trek_id=trek.id, from_city="Mumbai").first()
    pune_public = PublicRoute.query.filter_by(trek_id=trek.id, from_city="Pune").first()
    mumbai_public = PublicRoute.query.filter_by(trek_id=trek.id, from_city="Mumbai").first()

    return render_template(
        'trek_edit.html',
        form=form,
        trek=trek,
        pune_private=pune_private,
        mumbai_private=mumbai_private,
        pune_public=pune_public,
        mumbai_public=mumbai_public
    )

@app.route('/aboutus')
def aboutus():
    """About Us page route"""
    return render_template('aboutus.html')

@app.route('/guide')
def guide():
    """Guide page route"""
    return render_template('guide.html')

@app.route('/explore')
def explore():
    """Explore treks page"""
    search = request.args.get('search', '')
    difficulty_filter = request.args.get('difficulty', '')
    region_filter = request.args.get('region', '')
    
    # Base query
    query = Trek.query
    
    # Apply search filter
    if search:
        query = query.filter(Trek.name.contains(search))
    
    # Apply difficulty filter
    if difficulty_filter:
        query = query.filter(Trek.difficulty == difficulty_filter)
    
    # Apply region filter
    if region_filter:
        query = query.filter(Trek.region_id == region_filter)
    
    treks = query.all()
    regions = TrekRegion.query.all()
    
    return render_template('explore.html', treks=treks, regions=regions, 
                         search=search, difficulty_filter=difficulty_filter,
                         region_filter=region_filter)

@app.route('/trek/<int:trek_id>')
def trek_detail(trek_id):
    """Trek detail page"""
    trek = Trek.query.get_or_404(trek_id)
    comments = TrekComment.query.filter_by(trek_id=trek_id).order_by(TrekComment.created_at.desc()).all()
    
    # Get weather data for the trek location
    weather_data = None
    if trek.base_village:
        weather_data = get_weather_data(trek.base_village, trek.region.name if trek.region else None)
    elif trek.region:
        # Extract a major city from region name for weather data
        region_cities = {
            'Pune – Lonavala – Mulshi Belt': 'Lonavala',
            'Mumbai – Panvel – Karjat – Matheran Belt': 'Karjat',
            'Nashik – Bhandardara Belt': 'Nashik',
            'Satara – Mahabaleshwar – Kaas Belt': 'Mahabaleshwar',
            'Malshej Ghat Belt': 'Malshej',
            'Konkan Belt': 'Ratnagiri'
        }
        city = region_cities.get(trek.region.name, 'Mumbai')
        weather_data = get_weather_data(city, trek.region.name)
    
    # Check if trek is saved by current user
    is_saved = False
    if current_user.is_authenticated:
        saved_trek = SavedTrek.query.filter_by(user_id=current_user.id, trek_id=trek_id).first()
        is_saved = saved_trek is not None
    
    return render_template('trek_detail.html', trek=trek, comments=comments, weather=weather_data, is_saved=is_saved)

@app.route('/trek/<int:trek_id>/comment', methods=['POST'])
@login_required
def add_comment(trek_id):
    """Add comment to trek"""
    trek = Trek.query.get_or_404(trek_id)
    comment_text = request.form.get('comment')
    rating = request.form.get('rating', type=int)
    
    if not comment_text:
        flash('Comment required!', 'error')
        return redirect(url_for('trek_detail', trek_id=trek_id))
    
    # Handle image upload
    image_filename = None
    if 'image' in request.files:
        file = request.files['image']
        if file.filename != '':
            image_filename = save_uploaded_file(file, file_type='comment')
            if not image_filename:
                flash('Invalid image format. Please upload PNG, JPG, JPEG, GIF, or WebP files.', 'error')
                return redirect(url_for('trek_detail', trek_id=trek_id))
    
    comment = TrekComment(
        trek_id=trek_id,
        user_id=current_user.id,
        comment=comment_text,
        rating=rating,
        image_filename=image_filename
    )
    
    db.session.add(comment)
    db.session.commit()
    
    # Create admin notification for new comment
    if not current_user.is_admin():  # Don't notify for admin's own comments
        preview = comment_text[:100] + '...' if len(comment_text) > 100 else comment_text
        notification_message = f"{current_user.name} commented on {trek.name}: '{preview}'"
        
        notification = AdminNotification(
            type='new_comment',
            message=notification_message,
            trek_id=trek_id,
            comment_id=comment.id,
            user_id=current_user.id
        )
        
        db.session.add(notification)
        db.session.commit()
    
    flash('Your comment has been added!', 'success')
    return redirect(url_for('trek_detail', trek_id=trek_id))

@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    """Delete comment - only by admin or comment author"""
    comment = TrekComment.query.get_or_404(comment_id)
    trek_id = comment.trek_id
    
    # Check permissions: only admin or comment author can delete
    if not (current_user.is_admin() or comment.user_id == current_user.id):
        flash('You do not have permission to delete this comment.', 'error')
        return redirect(url_for('trek_detail', trek_id=trek_id))
    
    # Delete associated image file if exists
    if comment.image_filename:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], comment.image_filename)
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except OSError:
                pass  # File deletion failed, but continue with comment deletion
    
    db.session.delete(comment)
    db.session.commit()
    
    flash('Comment deleted successfully.', 'success')
    return redirect(url_for('trek_detail', trek_id=trek_id))

def calculate_trek_match(trek, age_group, health_issues_list, fitness_level, experience, trek_types_list):
    """Calculate match percentage for a trek based on user preferences with multiple selections support"""
    score = 0
    reasons = []
    
    # Trek categorization
    easy_treks = ['Karnala Fort', 'Arthur\'s Seat Trail', 'Peb–Matheran One Tree Hill']
    waterfall_treks = ['Devkund Waterfall', 'Randha Falls', 'Thoseghar Waterfalls', 'Kalu Waterfall', 'Nanemachi Waterfall']
    fort_treks = ['Rajgad Fort', 'Lohagad-Visapur Fort', 'Tikona Fort', 'Torna Fort', 'Rajmachi Fort', 'Irshalgad Fort', 'Sondai Fort', 'Harihar Fort', 'Ratangad Fort', 'Ajinkyatara–Sajjangad Forts', 'Harishchandragad Fort', 'Prabalgad–Kalavantin Durg']
    adventure_treks = ['Kalsubai Peak', 'Alang–Madan–Kulang (AMK) Forts', 'Harishchandragad Fort', 'Anjaneri–Brahmagiri Hills', 'Andharban Jungle Trek', 'Adrai Jungle Trek']
    scenic_treks = ['Kaas Plateau', 'Savlya Ghat', 'Duke\'s Nose'] + waterfall_treks
    
    # Difficulty levels
    easy_difficulty = ['Easy', 'Easy–Moderate']
    moderate_difficulty = ['Moderate']
    hard_difficulty = ['Hard', 'Challenging']
    
    trek_difficulty = trek.difficulty or 'Moderate'
    
    # Age Group Scoring
    if age_group == 'under_18':
        if trek.name in easy_treks or trek_difficulty in easy_difficulty:
            score += 25
            reasons.append("Perfect for young adventurers!")
        elif trek_difficulty in moderate_difficulty:
            score += 15
    elif age_group == '18_40':
        score += 20  # Most treks suitable
        if trek.name in adventure_treks:
            score += 10
            reasons.append("Great adventure for your age group!")
    elif age_group == '41_60':
        if trek_difficulty in easy_difficulty + moderate_difficulty:
            score += 20
            reasons.append("Well-suited for your experience level!")
        elif trek_difficulty in hard_difficulty:
            score += 5
    else:  # over_60
        if trek.name in easy_treks or trek_difficulty in easy_difficulty:
            score += 25
            reasons.append("Gentle trek with beautiful views!")
        else:
            score += 5
    
    # Health Issues Scoring (Multiple conditions support)
    health_penalty = 0
    health_reasons = []
    
    if 'none' in health_issues_list:
        score += 20
    else:
        # Handle multiple health conditions
        critical_conditions = ['asthma_breathing', 'heart_bp', 'surgery_injury']
        moderate_conditions = ['diabetes', 'joint_knee']
        
        has_critical = any(condition in health_issues_list for condition in critical_conditions)
        has_moderate = any(condition in health_issues_list for condition in moderate_conditions)
        
        if has_critical:
            # More restrictive scoring for critical conditions
            if trek_difficulty in easy_difficulty or trek.name in easy_treks:
                score += 15
                if 'asthma_breathing' in health_issues_list:
                    health_reasons.append("Easy trek suitable for breathing conditions")
                if 'heart_bp' in health_issues_list:
                    health_reasons.append("Low-intensity trek for heart health")
                if 'surgery_injury' in health_issues_list:
                    health_reasons.append("Gentle trek for recovery phase")
            elif trek_difficulty in moderate_difficulty:
                score += 8
                health_reasons.append("Moderate trek - medical clearance recommended")
            else:
                score += 0
                health_penalty += 10
        elif has_moderate:
            # Less restrictive for moderate conditions
            if trek_difficulty in easy_difficulty or trek.name in easy_treks:
                score += 18
                if 'diabetes' in health_issues_list:
                    health_reasons.append("Manageable trek for diabetes management")
                if 'joint_knee' in health_issues_list:
                    health_reasons.append("Easy on joints with minimal climbing")
            elif trek_difficulty in moderate_difficulty:
                score += 12
                if 'diabetes' in health_issues_list:
                    health_reasons.append("Carry glucose supplies for monitoring")
                if 'joint_knee' in health_issues_list and trek.name in waterfall_treks:
                    health_reasons.append("Rewarding destination worth the moderate effort")
            else:
                score += 5
        
        # Multiple conditions penalty
        if len(health_issues_list) > 1:
            health_penalty += (len(health_issues_list) - 1) * 3
            health_reasons.append(f"Multiple health considerations addressed")
    
    # Apply health penalty
    score = max(0, score - health_penalty)
    reasons.extend(health_reasons)
    
    # Fitness Level Scoring
    if fitness_level == 'low':
        if trek_difficulty in easy_difficulty or trek.name in easy_treks:
            score += 25
            reasons.append("Perfect for building your trekking confidence!")
        elif trek_difficulty in moderate_difficulty:
            score += 10
        else:
            score += 0
    elif fitness_level == 'medium':
        if trek_difficulty in easy_difficulty + moderate_difficulty:
            score += 20
        elif trek_difficulty in hard_difficulty:
            score += 10
    else:  # high
        score += 15
        if trek.name in adventure_treks or trek_difficulty in hard_difficulty:
            score += 10
            reasons.append("Challenging trek to test your limits!")
    
    # Experience Scoring
    if experience == 'first_time':
        if trek.name in easy_treks or trek_difficulty in easy_difficulty:
            score += 25
            reasons.append("Ideal first trek with great memories!")
        elif trek_difficulty in moderate_difficulty:
            score += 15
        else:
            score += 0
    elif experience == 'few_treks':
        if trek_difficulty in easy_difficulty + moderate_difficulty:
            score += 20
        elif trek_difficulty in hard_difficulty:
            score += 15
    else:  # experienced
        score += 15
        if trek.name in adventure_treks:
            score += 10
            reasons.append("Advanced trek for seasoned trekkers!")
    
    # Trek Type Scoring (Multiple preferences support)
    trek_type_score = 0
    trek_type_reasons = []
    max_type_score = 0
    
    for trek_type in trek_types_list:
        type_score = 0
        if trek_type == 'easy_short':
            if trek.name in easy_treks or trek_difficulty in easy_difficulty:
                type_score = 25
                trek_type_reasons.append("Short and sweet adventure!")
        elif trek_type == 'scenic_waterfall':
            if trek.name in scenic_treks:
                type_score = 25
                trek_type_reasons.append("Stunning scenery and natural beauty!")
        elif trek_type == 'fort_history':
            if trek.name in fort_treks:
                type_score = 25
                trek_type_reasons.append("Rich history and heritage site!")
        elif trek_type == 'adventure_long':
            if trek.name in adventure_treks or trek_difficulty in hard_difficulty:
                type_score = 25
                trek_type_reasons.append("Epic adventure and challenge!")
        
        max_type_score = max(max_type_score, type_score)
    
    # Use the highest matching type score + bonus for multiple matches
    score += max_type_score
    if max_type_score > 0:
        # Bonus for multiple type preferences that match
        matching_types = sum(1 for trek_type in trek_types_list 
                           if (trek_type == 'easy_short' and (trek.name in easy_treks or trek_difficulty in easy_difficulty)) or
                              (trek_type == 'scenic_waterfall' and trek.name in scenic_treks) or
                              (trek_type == 'fort_history' and trek.name in fort_treks) or
                              (trek_type == 'adventure_long' and (trek.name in adventure_treks or trek_difficulty in hard_difficulty)))
        
        if matching_types > 1:
            score += (matching_types - 1) * 5  # 5 points per additional matching type
            trek_type_reasons.append(f"Matches {matching_types} of your preferences!")
    
    reasons.extend(trek_type_reasons)
    
    # Cap the score at 100
    final_score = min(100, score)
    
    # Generate primary reason if none added
    if not reasons:
        if final_score >= 70:
            reasons.append("Great match for your preferences!")
        elif final_score >= 50:
            reasons.append("Good option to consider!")
        else:
            reasons.append("Moderate match for your profile.")
    
    return final_score, reasons[0]

@app.route('/trek-match', methods=['GET', 'POST'])
def trek_match():
    """Trek recommendation page"""
    recommendations = None
    
    if request.method == 'POST':
        # Get user inputs (now supporting multiple selections)
        age_group = request.form.get('age_group')
        health_issues = request.form.getlist('health_issues')  # Multiple selections
        fitness_level = request.form.get('fitness_level')
        experience = request.form.get('experience')
        trek_type = request.form.getlist('trek_type')  # Multiple selections
        
        # Get all treks and calculate matches
        treks = Trek.query.all()
        trek_matches = []
        
        for trek in treks:
            match_score, reason = calculate_trek_match(
                trek, age_group, health_issues, fitness_level, experience, trek_type
            )
            
            if match_score >= 40:  # Only include decent matches
                trek_matches.append({
                    'trek': trek,
                    'match_score': match_score,
                    'reason': reason
                })
        
        # Sort by match score (highest first) and limit to top 6
        trek_matches.sort(key=lambda x: x['match_score'], reverse=True)
        recommendations = trek_matches[:6]
    
    return render_template('trek_match.html', recommendations=recommendations)

# Trek Feed Routes
@app.route('/trek-feed', methods=['GET', 'POST'])
def trek_feed():
    """Public Trek Feed page: list posts; create post requires login"""
    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash('Please log in to create a post.', 'error')
            return redirect(url_for('login', next=url_for('trek_feed')))

        trek_name = request.form.get('trek_name', '').strip()
        trek_date_str = request.form.get('trek_date')
        trek_location = request.form.get('trek_location', '').strip()
        user_location = request.form.get('user_location', '').strip()
        caption = request.form.get('caption', '').strip()
        looking = request.form.get('looking_for_buddies', 'No') == 'Yes'
        trek_status = request.form.get('trek_status')
        image_file = request.files.get('image')

        if not trek_name:
            flash('Trek name is required.', 'error')
            return redirect(url_for('trek_feed'))

        trek_date = None
        if trek_date_str:
            try:
                trek_date = datetime.strptime(trek_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid trek date format.', 'error')

        image_filename = None
        if image_file and image_file.filename:
            saved = save_uploaded_file(image_file, file_type='post')
            if saved:
                image_filename = saved

        # Normalize trek_status
        if trek_status not in ('going', 'completed'):
            trek_status = None

        post = TrekPost(
            user_id=current_user.id,
            trek_name=trek_name,
            trek_date=trek_date,
            trek_location=trek_location,
            user_location=user_location,
            caption=caption,
            looking_for_buddies=looking,
            trek_status=trek_status,
            image_filename=image_filename
        )
        db.session.add(post)
        db.session.commit()
        flash('Post created!', 'success')
        return redirect(url_for('trek_feed'))

    # GET: list posts newest first
    posts = (TrekPost.query
             .order_by(TrekPost.created_at.desc())
             .all())

    # Precompute counts and whether current_user reacted
    post_data = []
    reacted_post_ids = set()
    if current_user.is_authenticated:
        user_reacts = TrekPostReaction.query.filter_by(user_id=current_user.id).all()
        reacted_post_ids = {r.post_id for r in user_reacts}

    for p in posts:
        reactions_count = TrekPostReaction.query.filter_by(post_id=p.id).count()
        comments_count = TrekPostComment.query.filter_by(post_id=p.id).count()
        post_data.append({
            'post': p,
            'reactions_count': reactions_count,
            'comments_count': comments_count,
            'reacted': p.id in reacted_post_ids
        })

    return render_template('trek_feed.html', posts=post_data)

@app.route('/trek-feed/<int:post_id>/react', methods=['POST'])
@login_required
def react_post(post_id):
    post = TrekPost.query.get_or_404(post_id)
    existing = TrekPostReaction.query.filter_by(post_id=post_id, user_id=current_user.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash('Reaction removed.', 'info')
    else:
        reaction = TrekPostReaction(post_id=post_id, user_id=current_user.id)
        db.session.add(reaction)
        db.session.commit()
        # Notify post owner
        create_notification(post.user_id, 'reaction', f"{current_user.name} reacted to your post.", post_id=post_id)
        flash('Reacted to post.', 'success')
    return redirect(url_for('trek_feed') + f"#post-{post_id}")

@app.route('/trek-feed/<int:post_id>/comment', methods=['POST'])
@login_required
def comment_post(post_id):
    post = TrekPost.query.get_or_404(post_id)
    content = request.form.get('content', '').strip()
    parent_id = request.form.get('parent_id')
    if not content:
        flash('Comment cannot be empty.', 'error')
        return redirect(url_for('trek_feed') + f"#post-{post_id}")
    parent = None
    if parent_id:
        parent = TrekPostComment.query.filter_by(id=int(parent_id), post_id=post_id).first()
    c = TrekPostComment(post_id=post_id, user_id=current_user.id, content=content, parent=parent)
    db.session.add(c)
    db.session.commit()
    # Notifications
    if parent:
        create_notification(parent.user_id, 'reply', f"{current_user.name} replied to your comment.", post_id=post_id, comment_id=c.id)
        # Email the comment owner for a reply
        try:
            if parent.user and parent.user.email and parent.user.id != current_user.id:
                subject = f"{current_user.name} replied to your comment on {post.trek_name}"
                body = f"Hello {parent.user.name},\n\n{current_user.name} replied to your comment on the post '{post.trek_name}'.\n\nReply content:\n{content}\n\nView it here: {url_for('trek_feed', _external=True)}#post-{post_id}\n\n— TrekMate"
                send_user_email(parent.user.email, subject, body)
        except Exception as e:
            app.logger.error(f"Failed to send reply email: {str(e)}")
    else:
        create_notification(post.user_id, 'comment', f"{current_user.name} commented on your post.", post_id=post_id, comment_id=c.id)
        # Email the post owner for a new top-level comment
        try:
            if post.user and post.user.email and post.user.id != current_user.id:
                subject = f"New comment on your trek post: {post.trek_name}"
                body = f"Hello {post.user.name},\n\n{current_user.name} commented on your post '{post.trek_name}'.\n\nComment:\n{content}\n\nView it here: {url_for('trek_feed', _external=True)}#post-{post_id}\n\n— TrekMate"
                send_user_email(post.user.email, subject, body)
        except Exception as e:
            app.logger.error(f"Failed to send comment email: {str(e)}")
    flash('Comment added.', 'success')
    return redirect(url_for('trek_feed') + f"#post-{post_id}")

@app.route('/trek-feed/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = TrekPost.query.get_or_404(post_id)
    if post.user_id != current_user.id and not current_user.is_admin():
        flash('You do not have permission to delete this post.', 'error')
        return redirect(url_for('trek_feed') + f"#post-{post_id}")
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted.', 'success')
    return redirect(url_for('trek_feed'))

@app.route('/trek-feed/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_post_comment(comment_id):
    comment = TrekPostComment.query.get_or_404(comment_id)
    post = TrekPost.query.get_or_404(comment.post_id)
    if comment.user_id != current_user.id and not current_user.is_admin():
        flash('You do not have permission to delete this comment.', 'error')
        return redirect(url_for('trek_feed') + f"#post-{post.id}")
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted.', 'success')
    return redirect(url_for('trek_feed') + f"#post-{post.id}")

# Admin Notification Routes
@app.route('/admin/notifications')
@login_required
def admin_notifications():
    """View all notifications page for admins"""
    if not current_user.is_admin():
        return redirect(url_for('home'))
    
    # Get all notifications (paginated)
    page = request.args.get('page', 1, type=int)
    notifications = AdminNotification.query\
                                   .order_by(AdminNotification.created_at.desc())\
                                   .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('admin_notifications.html', notifications=notifications)

@app.route('/admin/notifications/check')
@login_required
def check_notifications():
    """AJAX endpoint to check for new notifications"""
    if not current_user.is_admin():
        return {'error': 'Unauthorized'}, 403
    
    # Get unread notifications
    notifications = AdminNotification.query.filter_by(is_read=False)\
                                         .order_by(AdminNotification.created_at.desc())\
                                         .limit(10)\
                                         .all()
    
    notification_data = []
    for notification in notifications:
        notification_data.append({
            'id': notification.id,
            'type': notification.type,
            'title': f"New comment on {notification.trek.name if notification.trek else 'Unknown Trek'}",
            'message': notification.message,
            'trek_id': notification.trek_id,
            'comment_id': notification.comment_id,
            'user_name': notification.user.name if notification.user else 'Unknown',
            'trek_name': notification.trek.name if notification.trek else 'Unknown Trek',
            'created_at': notification.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'read': notification.is_read
        })
    
    unread_count = len([n for n in notification_data if not n['read']])
    
    return {
        'success': True,
        'notifications': notification_data, 
        'unread_count': unread_count
    }

@app.route('/admin/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark notification as read"""
    if not current_user.is_admin():
        return {'error': 'Unauthorized'}, 403
    
    notification = AdminNotification.query.get_or_404(notification_id)
    notification.is_read = True
    db.session.commit()
    
    return {'success': True}

@app.route('/admin/notifications/mark-read', methods=['POST'])
@login_required
def mark_notifications_read():
    """Mark all unread notifications as read"""
    if not current_user.is_admin():
        return {'error': 'Unauthorized'}, 403
    
    AdminNotification.query.filter_by(is_read=False).update({'is_read': True})
    db.session.commit()
    
    return {'success': True}

@app.route('/admin/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read"""
    if not current_user.is_admin():
        return {'error': 'Unauthorized'}, 403
    
    AdminNotification.query.filter_by(is_read=False).update({'is_read': True})
    db.session.commit()
    
    return {'success': True}

# Saved Trek Routes
@app.route('/trek/<int:trek_id>/save', methods=['POST'])
@login_required
def save_trek(trek_id):
    """Save a trek to user's saved list"""
    from flask import jsonify
    
    # Check if trek exists
    trek = Trek.query.get_or_404(trek_id)
    
    # Check if already saved
    existing_save = SavedTrek.query.filter_by(user_id=current_user.id, trek_id=trek_id).first()
    if existing_save:
        return jsonify({'success': False, 'message': 'Trek already saved'}), 400

    # Save the trek
    try:
        saved_trek = SavedTrek(user_id=current_user.id, trek_id=trek_id)
        db.session.add(saved_trek)
        db.session.commit()
        flash(f'{trek.name} has been saved to your profile!', 'success')
        return jsonify({'success': True, 'message': f'{trek.name} saved successfully!'})
    except Exception as e:
        db.session.rollback()
        flash('Error saving trek. Please try again.', 'error')
        return jsonify({'success': False, 'message': 'Error saving trek'}), 500

@app.route('/trek/<int:trek_id>/unsave', methods=['POST'])
@login_required
def unsave_trek(trek_id):
    """Remove a trek from user's saved list"""
    from flask import jsonify
    
    # Find the saved trek
    saved_trek = SavedTrek.query.filter_by(user_id=current_user.id, trek_id=trek_id).first()
    if not saved_trek:
        return jsonify({'success': False, 'message': 'Trek not in saved list'}), 400
    
    # Get trek name for flash message
    trek_name = saved_trek.trek.name
    
    # Remove the saved trek
    try:
        db.session.delete(saved_trek)
        db.session.commit()
        flash(f'{trek_name} has been removed from your saved treks.', 'info')
        return jsonify({'success': True, 'message': f'{trek_name} removed from saved list'})
    except Exception as e:
        db.session.rollback()
        flash('Error removing saved trek. Please try again.', 'error')
        return jsonify({'success': False, 'message': 'Error removing saved trek'}), 500

@app.route('/api/trek/<int:trek_id>/is_saved')
@login_required
def check_trek_saved(trek_id):
    """Check if a trek is saved by current user"""
    from flask import jsonify
    
    saved_trek = SavedTrek.query.filter_by(user_id=current_user.id, trek_id=trek_id).first()
    return jsonify({'is_saved': saved_trek is not None})

@app.route('/saved-trek/<int:saved_trek_id>/remove', methods=['POST'])
@login_required
def remove_saved_trek(saved_trek_id):
    """Remove a saved trek by saved_trek_id"""
    from flask import jsonify
    
    saved_trek = SavedTrek.query.get_or_404(saved_trek_id)
    
    # Check if the saved trek belongs to current user
    if saved_trek.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    # Get trek name for flash message
    trek_name = saved_trek.trek.name
    
    try:
        db.session.delete(saved_trek)
        db.session.commit()
        flash(f'{trek_name} has been removed from your saved treks.', 'info')
        return jsonify({'success': True, 'message': f'{trek_name} removed from saved list'})
    except Exception as e:
        db.session.rollback()
        flash('Error removing saved trek. Please try again.', 'error')
        return jsonify({'success': False, 'message': 'Error removing saved trek'}), 500

def get_time_ago(created_at):
    """Helper function to get human readable time ago"""
    from datetime import datetime, timedelta
    
    now = datetime.utcnow()
    diff = now - created_at
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('404.html'), 404

def create_admin_user():
    """Create default admin user from environment variables if it doesn't exist"""
    admin_email = ADMIN_EMAIL
    admin_password = ADMIN_PASSWORD
    if not admin_email or not admin_password:
        print('ADMIN_EMAIL or ADMIN_PASSWORD not set; skipping admin user creation.')
        return
    admin = User.query.filter_by(email=admin_email).first()
    if not admin:
        admin = User(
            name='Admin - Adilb0t',
            email=admin_email,
            role='admin'
        )
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        print(f'Default admin user created for {admin_email}')

if __name__ == '__main__':
    with app.app_context():
        # Create all database tables
        db.create_all()
        # Create default admin user
        create_admin_user()
    
    app.run(debug=False, host='0.0.0.0', port=5000)
