from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import User, AuditLog
from extensions import db, limiter
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re
from functools import wraps

auth = Blueprint('auth', __name__)

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('You need administrator privileges to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")  # Rate limiting for login attempts
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Simple input validation
        if not username or not password:
            flash('Username and password are required')
            return redirect(url_for('auth.login'))
            
        user = User.query.filter_by(username=username).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            flash('Please check your login details and try again.', 'error')
            return render_template('login.html')
        
        # Update last login time
        user.update_login_timestamp()
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('vehicles.dashboard'))
    
    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        # Update profile
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate current password
        if not current_user.check_password(current_password):
            flash('Current password is incorrect', 'error')
            return redirect(url_for('auth.profile'))
            
        # Validate new password
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('auth.profile'))
            
        # Validate password strength
        if len(new_password) < 8:
            flash('Password must be at least 8 characters', 'error')
            return redirect(url_for('auth.profile'))
            
        # Update password
        current_user.set_password(new_password)
        db.session.commit()
        flash('Password updated successfully', 'success')
        
    return render_template('profile.html', user=current_user)

# Admin only routes
@auth.route('/users')
@login_required
@admin_required
def user_list():
    users = User.query.all()
    return render_template('users.html', users=users)

@auth.route('/users/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        role = request.form.get('role')
        
        # Validate inputs
        if not username or not password or not email:
            flash('All fields are required', 'error')
            return redirect(url_for('auth.new_user'))
            
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('auth.new_user'))
            
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already in use', 'error')
            return redirect(url_for('auth.new_user'))
            
        # Validate email format
        email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_pattern, email):
            flash('Invalid email format', 'error')
            return redirect(url_for('auth.new_user'))
            
        # Create new user
        user = User(username=username, email=email, role=role)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('User created successfully', 'success')
            return redirect(url_for('auth.user_list'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating user: {str(e)}")
            flash('Error creating user', 'error')
            return redirect(url_for('auth.new_user'))
            
    return render_template('user_form.html')

@auth.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        email = request.form.get('email')
        role = request.form.get('role')
        
        # Validate email format
        email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_pattern, email):
            flash('Invalid email format', 'error')
            return redirect(url_for('auth.edit_user', user_id=user_id))
            
        # Check if new email already exists for another user
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != user_id:
            flash('Email already in use', 'error')
            return redirect(url_for('auth.edit_user', user_id=user_id))
            
        # Update user
        user.email = email
        user.role = role
        
        # Reset password if requested
        if request.form.get('reset_password'):
            new_password = request.form.get('new_password')
            if len(new_password) < 8:
                flash('Password must be at least 8 characters', 'error')
                return redirect(url_for('auth.edit_user', user_id=user_id))
                
            user.set_password(new_password)
            
        try:
            db.session.commit()
            flash('User updated successfully', 'success')
            return redirect(url_for('auth.user_list'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating user: {str(e)}")
            flash('Error updating user', 'error')
            
    return render_template('user_form.html', user=user)

@auth.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Prevent deletion of own account
    if user.id == current_user.id:
        flash('Cannot delete your own account', 'error')
        return redirect(url_for('auth.user_list'))
        
    try:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting user: {str(e)}")
        flash('Error deleting user', 'error')
        
    return redirect(url_for('auth.user_list'))

# API endpoints for user management
@auth.route('/api/users', methods=['GET'])
@login_required
@admin_required
def api_users():
    users = User.query.all()
    return jsonify({
        'users': [
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role
            } for user in users
        ]
    })

@auth.route('/api/v1/users/<int:user_id>', methods=['GET'])
@login_required
@admin_required
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'fullname': user.fullname,
            'email': user.email,
            'is_admin': user.is_admin()
        }
    })

@auth.route('/users/add', methods=['POST'])
@login_required
@admin_required
def add_user():
    username = request.form.get('username')
    password = request.form.get('password')
    fullname = request.form.get('fullname', '')
    is_admin = request.form.get('is_admin') == 'on'  # Properly check if checkbox is checked
    email = request.form.get('email', f"{username}@example.com")
    
    # Check if username already exists
    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'error')
        return redirect(url_for('auth.user_list'))
    
    # Check if email already exists
    if User.query.filter_by(email=email).first():
        flash('Email already in use.', 'error')
        return redirect(url_for('auth.user_list'))
    
    # Create new user
    new_user = User(
        username=username,
        password_hash=generate_password_hash(password, method='pbkdf2:sha256'),
        email=email,
        role='admin' if is_admin else 'operator'
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        flash('User added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding user: {str(e)}")
        flash('An error occurred while adding the user.', 'error')
    
    return redirect(url_for('auth.user_list'))

@auth.route('/users/<int:user_id>/update', methods=['POST'])
@login_required
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    
    # Update fields
    is_admin = request.form.get('is_admin') == 'on'  # Properly check if checkbox is checked
    password = request.form.get('password')
    email = request.form.get('email')
    
    # Check if new email already exists for another user
    if email != user.email and User.query.filter_by(email=email).first():
        flash('Email already in use.', 'error')
        return redirect(url_for('auth.user_list'))
    
    user.role = 'admin' if is_admin else 'operator'
    user.email = email
    
    # Update password only if provided
    if password:
        user.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    try:
        db.session.commit()
        flash('User updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating user: {str(e)}")
        flash('An error occurred while updating the user.', 'error')
    
    return redirect(url_for('auth.user_list'))

@auth.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    
    # Password change if requested
    if current_password and new_password:
        if not check_password_hash(current_user.password_hash, current_password):
            flash('Current password is incorrect.', 'error')
            return redirect(url_for('auth.profile'))
        
        current_user.password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
    
    try:
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating profile: {str(e)}")
        flash('An error occurred while updating your profile.', 'error')
    
    return redirect(url_for('auth.profile')) 