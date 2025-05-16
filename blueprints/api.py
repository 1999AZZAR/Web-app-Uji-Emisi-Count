from flask import Blueprint, jsonify, request, current_app, render_template
from flask_login import login_required, current_user
from extensions import db, csrf
from models import Config
import json
import datetime

api = Blueprint('api', __name__, url_prefix='/api/v1')

@api.route('/config', methods=['GET'])
@login_required
def get_config():
    """Get application configuration"""
    try:
        config = Config.get_config()
        return render_template('config.html', config=config, now=datetime.datetime.now())
    except Exception as e:
        current_app.logger.error(str(e))
        return jsonify({
            'success': False,
            'error': 'Error retrieving configuration'
        }), 500

@api.route('/config', methods=['POST'])
@login_required
def update_config():
    """Update application configuration"""
    # Only admin users can update configuration
    if not current_user.is_admin():
        from flask import flash, redirect, url_for
        flash('Admin privileges required', 'error')
        return redirect(url_for('api.get_config'))
        
    try:
        # Get form data instead of JSON
        form_data = request.form
        
        if not form_data:
            from flask import flash, redirect, url_for
            flash('No data provided', 'error')
            return redirect(url_for('api.get_config'))
            
        config = Config.get_config()
        
        # Update basic parameters
        if 'co_max' in form_data:
            config.co_max = float(form_data['co_max'])
        if 'hc_max' in form_data:
            config.hc_max = float(form_data['hc_max'])
        if 'co2_min' in form_data:
            config.co2_min = float(form_data['co2_min'])
        if 'co2_max' in form_data:
            config.co2_max = float(form_data['co2_max'])
        if 'o2_min' in form_data:
            config.o2_min = float(form_data['o2_min'])
        if 'o2_max' in form_data:
            config.o2_max = float(form_data['o2_max'])
        if 'lambda_min' in form_data:
            config.lambda_min = float(form_data['lambda_min'])
        if 'lambda_max' in form_data:
            config.lambda_max = float(form_data['lambda_max'])
        
        # Update bensin parameters
        if 'bensin_co_max' in form_data:
            config.bensin_co_max = float(form_data['bensin_co_max'])
        if 'bensin_hc_max' in form_data:
            config.bensin_hc_max = float(form_data['bensin_hc_max'])
        if 'bensin_co2_max' in form_data:
            config.bensin_co2_max = float(form_data['bensin_co2_max'])
        if 'bensin_o2_max' in form_data:
            config.bensin_o2_max = float(form_data['bensin_o2_max'])
        if 'bensin_lambda_max' in form_data:
            config.bensin_lambda_max = float(form_data['bensin_lambda_max'])
        
        # Update load categories and year ranges
        if 'bensin_load_category' in form_data:
            config.bensin_load_category = form_data['bensin_load_category']
        if 'bensin_year_range' in form_data:
            config.bensin_year_range = form_data['bensin_year_range']
        
        # Update solar parameters
        if 'solar_opacity_max' in form_data:
            config.solar_opacity_max = float(form_data['solar_opacity_max'])
        if 'solar_load_category' in form_data:
            config.solar_load_category = form_data['solar_load_category']
        if 'solar_year_range' in form_data:
            config.solar_year_range = form_data['solar_year_range']
        
        db.session.commit()
        
        # Log the update
        current_app.logger.info(f"Configuration updated by user: {current_user.username}")
        
        from flask import flash, redirect, url_for
        flash('Konfigurasi berhasil diperbarui', 'success')
        return redirect(url_for('api.get_config'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(str(e))
        
        from flask import flash, redirect, url_for
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('api.get_config'))

@api.route('/health')
def health_check():
    """API health check endpoint"""
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        
        return jsonify({
            'status': 'ok',
            'database': 'connected'
        })
    except Exception as e:
        current_app.logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'database': 'disconnected',
            'error': str(e)
        }), 500

@api.route('/version')
def version():
    """Get API version information"""
    return jsonify({
        'api_version': 'v1',
        'app_name': 'Web-app-Uji-Emisi-Count',
        'description': 'API for vehicle emissions testing web application'
    }) 