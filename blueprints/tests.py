from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for, flash
from sqlalchemy import exc
from extensions import db, csrf
from models import Kendaraan, HasilUji, Config
from flask_login import login_required, current_user
import time
from datetime import datetime
import json

tests = Blueprint('tests', __name__)

@tests.route('/test')
@login_required
def test_page():
    """Main emissions testing page"""
    return render_template('halaman2.html')

@tests.route('/api/hasil-uji/tested-plats')
@login_required
def tested_plats():
    try:
        # Get all plate numbers that have test results
        results = db.session.query(Kendaraan.plat_nomor).join(HasilUji).distinct().all()
        plats = [p[0] for p in results]
        return jsonify(plats)
    except exc.SQLAlchemyError as e:
        current_app.logger.error(str(e))
        return jsonify([])

@tests.route('/api/hasil-uji/<string:plat_nomor>', methods=['GET', 'POST', 'DELETE'])
@login_required
@csrf.exempt
def manage_hasil(plat_nomor):
    kendaraan = Kendaraan.query.filter_by(plat_nomor=plat_nomor).first()
    if not kendaraan:
        return jsonify({'error': 'Kendaraan tidak ditemukan'}), 404

    if request.method == 'GET':
        try:
            hasil = HasilUji.query.filter_by(kendaraan_id=kendaraan.id).first()
            if not hasil:
                return jsonify({'error': 'Data uji tidak ditemukan'}), 404
                
            response_data = {
                'co': hasil.co,
                'co2': hasil.co2,
                'hc': hasil.hc,
                'o2': hasil.o2,
                'lambda_val': hasil.lambda_val,
                'opacity': hasil.opacity,
                'lulus': hasil.lulus,
                'valid': hasil.valid,
                'user_id': hasil.user_id,
                'tanggal': hasil.tanggal.isoformat() if hasil.tanggal else None,
                'operator': hasil.user.username if hasil.user else None
            }
            
            # Add vehicle details
            response_data['fuel_type'] = kendaraan.fuel_type
            response_data['load_category'] = kendaraan.load_category
            response_data['plat_nomor'] = kendaraan.plat_nomor
            response_data['merek'] = kendaraan.merek
            response_data['tipe'] = kendaraan.tipe
            response_data['tahun'] = kendaraan.tahun
            
            return jsonify(response_data)
        except Exception as e:
            current_app.logger.error(str(e))
            return jsonify({'error': 'Error retrieving test data'}), 500

    # DELETE: clear test data
    if request.method == 'DELETE':
        try:
            hasil = HasilUji.query.filter_by(kendaraan_id=kendaraan.id).first()
            if not hasil:
                return jsonify({'error': 'No test data found'}), 404
                
            db.session.delete(hasil)
            db.session.commit()
            
            # Log the deletion
            current_app.logger.info(f"Test result deleted for {plat_nomor} by user: {current_user.username}")
            
            return jsonify({'message': 'Test data cleared'}), 200
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(str(e))
            return jsonify({'error': 'Error deleting test data'}), 500
    
    # POST: create new test data
    elif request.method == 'POST':
        try:
            data = request.json
            
            # Validate input based on fuel type
            if kendaraan.fuel_type == 'bensin':
                required = ['co', 'co2', 'hc', 'o2', 'lambda_val']
                missing = [f for f in required if not data.get(f)]
                if missing:
                    return jsonify({'error': f'Missing required fields for bensin: {", ".join(missing)}'}), 400
                    
                # Convert values to float
                try:
                    co = float(data.get('co', 0))
                    co2 = float(data.get('co2', 0))
                    hc = float(data.get('hc', 0))
                    o2 = float(data.get('o2', 0))
                    lambda_val = float(data.get('lambda_val', 0))
                    opacity = None  # Not applicable for bensin
                except ValueError:
                    return jsonify({'error': 'All values must be valid numbers'}), 400
                    
                # Get config to determine pass/fail
                config = Config.get_config()
                
                # Determine vehicle age category
                current_year = datetime.now().year
                vehicle_age = current_year - kendaraan.tahun
                
                age_category = None
                if kendaraan.tahun < 2007:
                    age_category = '<2007'
                elif 2007 <= kendaraan.tahun <= 2018:
                    age_category = '2007-2018'
                else:
                    age_category = '>2018'
                    
                # Get parameters for this vehicle type
                load_category = kendaraan.load_category
                vehicle_params = config.bensin_parameters.get(load_category, {}).get(age_category, {})
                
                if not vehicle_params:
                    # Fallback to default values if category not found
                    vehicle_params = {
                        'co_max': config.bensin_co_max,
                        'hc_max': config.bensin_hc_max,
                        'co2_min': config.co2_min,
                        'lambda_min': config.lambda_min,
                        'lambda_max': config.lambda_max
                    }
                
                # Determine if the vehicle passes the test
                lulus = (
                    co <= vehicle_params.get('co_max', config.bensin_co_max) and
                    hc <= vehicle_params.get('hc_max', config.bensin_hc_max) and
                    co2 >= vehicle_params.get('co2_min', config.co2_min) and
                    o2 <= config.o2_max and
                    lambda_val >= vehicle_params.get('lambda_min', config.lambda_min) and
                    lambda_val <= vehicle_params.get('lambda_max', config.lambda_max)
                )
                
            else:  # Solar/diesel
                if 'opacity' not in data:
                    return jsonify({'error': 'Opacity value is required for solar vehicles'}), 400
                    
                try:
                    opacity = float(data.get('opacity', 0))
                    # Default values for other fields (not used for solar)
                    co = 0
                    co2 = 0
                    hc = 0
                    o2 = 0
                    lambda_val = 0
                except ValueError:
                    return jsonify({'error': 'Opacity must be a valid number'}), 400
                    
                # Get config to determine pass/fail
                config = Config.get_config()
                
                # Determine vehicle age category
                current_year = datetime.now().year
                vehicle_age = current_year - kendaraan.tahun
                
                age_category = None
                if kendaraan.tahun < 2010:
                    age_category = '<2010'
                elif 2010 <= kendaraan.tahun <= 2021:
                    age_category = '2010-2021'
                else:
                    age_category = '>2021'
                    
                # Get parameters for this vehicle type
                load_category = kendaraan.load_category
                vehicle_params = config.solar_parameters.get(load_category, {}).get(age_category, {})
                
                if not vehicle_params:
                    # Fallback to default values if category not found
                    vehicle_params = {
                        'opacity_max': config.solar_opacity_max
                    }
                
                # Determine if the vehicle passes the test
                lulus = opacity <= vehicle_params.get('opacity_max', config.solar_opacity_max)
            
            # Create or update HasilUji record
            existing = HasilUji.query.filter_by(kendaraan_id=kendaraan.id).first()
            
            if existing:
                existing.co = co
                existing.co2 = co2
                existing.hc = hc
                existing.o2 = o2
                existing.lambda_val = lambda_val
                existing.opacity = opacity
                existing.lulus = lulus
                existing.valid = True
                existing.user_id = current_user.id
                existing.tanggal = datetime.now()
            else:
                hasil_uji = HasilUji(
                    kendaraan_id=kendaraan.id,
                    co=co,
                    co2=co2,
                    hc=hc,
                    o2=o2,
                    lambda_val=lambda_val,
                    opacity=opacity,
                    lulus=lulus,
                    valid=True,
                    user_id=current_user.id,
                    tanggal=datetime.now()
                )
                db.session.add(hasil_uji)
                
            db.session.commit()
            
            # Log the test
            current_app.logger.info(f"Test result recorded for {plat_nomor} by user: {current_user.username}. Result: {'PASS' if lulus else 'FAIL'}")
            
            # Include limit values in response to display to user
            limits = {}
            if kendaraan.fuel_type == 'bensin':
                limits = {
                    'co_max': vehicle_params.get('co_max', config.bensin_co_max),
                    'hc_max': vehicle_params.get('hc_max', config.bensin_hc_max),
                    'co2_min': vehicle_params.get('co2_min', config.co2_min),
                    'o2_max': config.o2_max,
                    'lambda_min': vehicle_params.get('lambda_min', config.lambda_min),
                    'lambda_max': vehicle_params.get('lambda_max', config.lambda_max)
                }
            else:
                limits = {
                    'opacity_max': vehicle_params.get('opacity_max', config.solar_opacity_max)
                }
            
            return jsonify({
                'success': True,
                'lulus': lulus,
                'limits': limits,
                'vehicle_info': {
                    'fuel_type': kendaraan.fuel_type,
                    'load_category': kendaraan.load_category,
                    'tahun': kendaraan.tahun,
                    'age_category': age_category
                }
            })
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(str(e))
            return jsonify({'error': str(e)}), 500

@tests.route('/testing-history')
@login_required
def testing_history():
    """View testing history for all vehicles"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Optional filters
        plat_nomor = request.args.get('plat_nomor', '')
        merek = request.args.get('merek', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        result = request.args.get('result', '')  # 'pass', 'fail', or ''
        
        # Base query joining all tables
        query = db.session.query(HasilUji, Kendaraan).join(
            Kendaraan, HasilUji.kendaraan_id == Kendaraan.id
        )
        
        # Apply filters
        if plat_nomor:
            query = query.filter(Kendaraan.plat_nomor.ilike(f'%{plat_nomor}%'))
        if merek:
            query = query.filter(Kendaraan.merek.ilike(f'%{merek}%'))
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(HasilUji.tanggal >= start_date_obj)
            except ValueError:
                flash('Invalid start date format. Use YYYY-MM-DD.', 'error')
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
                # Add a day to include the end date
                end_date_obj = datetime(end_date_obj.year, end_date_obj.month, end_date_obj.day, 23, 59, 59)
                query = query.filter(HasilUji.tanggal <= end_date_obj)
            except ValueError:
                flash('Invalid end date format. Use YYYY-MM-DD.', 'error')
        if result == 'pass':
            query = query.filter(HasilUji.lulus == True)
        elif result == 'fail':
            query = query.filter(HasilUji.lulus == False)
            
        # Order by most recent tests
        query = query.order_by(HasilUji.tanggal.desc())
        
        # Paginate results
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return render_template(
            'testing_history.html',
            pagination=pagination,
            filters={
                'plat_nomor': plat_nomor,
                'merek': merek,
                'start_date': start_date,
                'end_date': end_date,
                'result': result
            }
        )
    except Exception as e:
        current_app.logger.error(str(e))
        flash('Error loading testing history', 'error')
        return redirect(url_for('vehicles.dashboard'))

@tests.route('/test-certificate/<int:hasil_id>')
@login_required
def test_certificate(hasil_id):
    """Generate and display a test certificate for printing"""
    try:
        hasil = HasilUji.query.get_or_404(hasil_id)
        kendaraan = Kendaraan.query.get_or_404(hasil.kendaraan_id)
        
        return render_template(
            'test_certificate.html',
            hasil=hasil,
            kendaraan=kendaraan,
            operator=hasil.user.username if hasil.user else 'Unknown',
            timestamp=datetime.now().strftime('%Y%m%d%H%M%S')
        )
    except Exception as e:
        current_app.logger.error(str(e))
        flash('Error generating certificate', 'error')
        return redirect(url_for('tests.testing_history')) 