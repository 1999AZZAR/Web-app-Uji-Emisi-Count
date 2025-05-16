from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for, flash, send_file
from sqlalchemy import exc
from extensions import db, csrf
from models import Kendaraan
from flask_login import login_required, current_user
import csv
import tempfile
from io import StringIO
import time

vehicles = Blueprint('vehicles', __name__)

@vehicles.route('/')
@login_required
def dashboard():
    """Main dashboard/entry page for vehicle input"""
    return render_template('halaman1.html')

@vehicles.route('/api/kendaraan-list')
@login_required
def get_kendaraan_list():
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Get filtering parameters
        plat_nomor = request.args.get('plat_nomor', '')
        merek = request.args.get('merek', '')
        tipe = request.args.get('tipe', '')
        jenis = request.args.get('jenis', '')
        fuel_type = request.args.get('fuel_type', '')
        
        # Build query with filters
        query = Kendaraan.query
        
        if plat_nomor:
            query = query.filter(Kendaraan.plat_nomor.ilike(f'%{plat_nomor}%'))
        if merek:
            query = query.filter(Kendaraan.merek.ilike(f'%{merek}%'))
        if tipe:
            query = query.filter(Kendaraan.tipe.ilike(f'%{tipe}%'))
        if jenis:
            query = query.filter(Kendaraan.jenis == jenis)
        if fuel_type:
            query = query.filter(Kendaraan.fuel_type == fuel_type)
            
        # Paginate results
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Format response
        items = [{
            'id': k.id,
            'jenis': k.jenis,
            'plat_nomor': k.plat_nomor,
            'merek': k.merek,
            'tipe': k.tipe,
            'tahun': k.tahun,
            'nama_instansi': k.nama_instansi,
            'fuel_type': k.fuel_type,
            'load_category': k.load_category
        } for k in pagination.items]
        
        return jsonify({
            'items': items,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
    except exc.SQLAlchemyError as e:
        current_app.logger.error(f'Database error: {str(e)}')
        return jsonify({'error': 'Database error occurred'}), 500

@vehicles.route('/api/kendaraan/<plat_nomor>')
@login_required
def get_kendaraan(plat_nomor):
    try:
        kendaraan = Kendaraan.query.filter_by(plat_nomor=plat_nomor).first()
        if kendaraan:
            return jsonify({
                'id': kendaraan.id,
                'jenis': kendaraan.jenis,
                'plat_nomor': kendaraan.plat_nomor,
                'merek': kendaraan.merek,
                'tipe': kendaraan.tipe,
                'tahun': kendaraan.tahun,
                'nama_instansi': kendaraan.nama_instansi,
                'fuel_type': kendaraan.fuel_type,
                'load_category': kendaraan.load_category
            })
        return jsonify({'error': 'Vehicle not found'}), 404
    except exc.SQLAlchemyError as e:
        current_app.logger.error(f'Database error: {str(e)}')
        return jsonify({'error': 'Database error occurred'}), 500

@vehicles.route('/api/kendaraan', methods=['POST'])
@login_required
@csrf.exempt
def tambah_kendaraan():
    try:
        data = request.json or {}
        # Required fields validation
        required = ['jenis', 'plat_nomor', 'merek', 'tipe', 'tahun', 'fuel_type', 'load_category']
        missing = [f for f in required if not data.get(f)]
        
        if missing:
            return jsonify({'error': f'Missing required fields: {", ".join(missing)}'}), 400
            
        # Input validation
        plat = data['plat_nomor'].strip().upper()
        if len(plat) < 4:
            return jsonify({'error': 'Invalid plate number format'}), 400
            
        try:
            tahun = int(data['tahun'])
            if tahun < 1900 or tahun > 2100:
                return jsonify({'error': 'Invalid year'}), 400
        except ValueError:
            return jsonify({'error': 'Year must be a valid number'}), 400
            
        if data['jenis'] not in ['umum', 'dinas']:
            return jsonify({'error': 'Invalid vehicle type'}), 400
            
        if data.get('fuel_type') not in ['bensin', 'solar']:
            return jsonify({'error': 'Invalid fuel type'}), 400
            
        # Validate load category based on fuel type
        load_category = data.get('load_category')
        if not load_category:
            return jsonify({'error': 'Load category is required'}), 400
            
        valid_categories = {
            'bensin': ['kendaraan_muatan', 'kendaraan_penumpang'],
            'solar': ['<3.5ton', '>=3.5ton']
        }
        
        if load_category not in valid_categories[data['fuel_type']]:
            return jsonify({
                'error': f'Invalid load category for {data["fuel_type"]}. Valid options are: {", ".join(valid_categories[data["fuel_type"]])}'
            }), 400
            
        # Handle nama_instansi
        inst = data.get('nama_instansi', '').strip()
        if data['jenis'] != 'dinas' or not inst:
            inst = '-'
            
        # Create new Kendaraan
        kendaraan = Kendaraan(
            jenis=data['jenis'],
            plat_nomor=plat,
            merek=data['merek'].strip(),
            tipe=data['tipe'].strip(),
            tahun=tahun,
            fuel_type=data['fuel_type'],
            nama_instansi=inst,
            load_category=load_category
        )
        
        db.session.add(kendaraan)
        db.session.commit()
        
        # Log the creation
        current_app.logger.info(f"Vehicle created: {plat} by user: {current_user.username}")
        
        return jsonify({
            'success': True,
            'id': kendaraan.id,
            'message': 'Berhasil disimpan'
        })
    except exc.IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Plat nomor sudah terdaftar'}), 409
    except exc.SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(str(e))
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(str(e))
        return jsonify({'error': 'Unexpected error occurred'}), 500

@vehicles.route('/api/kendaraan/<plat_nomor>', methods=['PUT', 'DELETE'])
@login_required
@csrf.exempt
def modify_kendaraan(plat_nomor):
    if request.method == 'DELETE':
        try:
            kendaraan = Kendaraan.query.filter_by(plat_nomor=plat_nomor).first_or_404()
            
            # Log the deletion
            current_app.logger.info(f"Vehicle deleted: {plat_nomor} by user: {current_user.username}")
            
            db.session.delete(kendaraan)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(str(e))
            return jsonify({'error': str(e)}), 500
    elif request.method == 'PUT':
        try:
            data = request.json or {}
            kendaraan = Kendaraan.query.filter_by(plat_nomor=plat_nomor).first_or_404()
            
            # Update fields
            if 'merek' in data:
                kendaraan.merek = data['merek'].strip()
            if 'tipe' in data:
                kendaraan.tipe = data['tipe'].strip()
            if 'tahun' in data:
                try:
                    tahun = int(data['tahun'])
                    if tahun < 1900 or tahun > 2100:
                        return jsonify({'error': 'Invalid year'}), 400
                    kendaraan.tahun = tahun
                except ValueError:
                    return jsonify({'error': 'Year must be a valid number'}), 400
            if 'jenis' in data:
                if data['jenis'] not in ['umum', 'dinas']:
                    return jsonify({'error': 'Invalid vehicle type'}), 400
                kendaraan.jenis = data['jenis']
                
                # Update nama_instansi based on jenis
                if data['jenis'] == 'dinas' and 'nama_instansi' in data:
                    kendaraan.nama_instansi = data['nama_instansi'].strip()
                elif data['jenis'] == 'umum':
                    kendaraan.nama_instansi = '-'
                    
            if 'fuel_type' in data:
                if data['fuel_type'] not in ['bensin', 'solar']:
                    return jsonify({'error': 'Invalid fuel type'}), 400
                    
                # Validate load_category if fuel_type changes
                old_fuel_type = kendaraan.fuel_type
                new_fuel_type = data['fuel_type']
                
                if old_fuel_type != new_fuel_type:
                    valid_categories = {
                        'bensin': ['kendaraan_muatan', 'kendaraan_penumpang'],
                        'solar': ['<3.5ton', '>=3.5ton']
                    }
                    
                    # If load_category is provided, validate it
                    if 'load_category' in data:
                        if data['load_category'] not in valid_categories[new_fuel_type]:
                            return jsonify({
                                'error': f'Invalid load category for {new_fuel_type}. Valid options are: {", ".join(valid_categories[new_fuel_type])}'
                            }), 400
                    # If not provided, set a default valid category
                    else:
                        data['load_category'] = valid_categories[new_fuel_type][0]
                
                kendaraan.fuel_type = new_fuel_type
                
            if 'load_category' in data:
                valid_categories = {
                    'bensin': ['kendaraan_muatan', 'kendaraan_penumpang'],
                    'solar': ['<3.5ton', '>=3.5ton']
                }
                
                if data['load_category'] not in valid_categories[kendaraan.fuel_type]:
                    return jsonify({
                        'error': f'Invalid load category for {kendaraan.fuel_type}. Valid options are: {", ".join(valid_categories[kendaraan.fuel_type])}'
                    }), 400
                    
                kendaraan.load_category = data['load_category']
                
            db.session.commit()
            
            # Log the update
            current_app.logger.info(f"Vehicle updated: {plat_nomor} by user: {current_user.username}")
            
            return jsonify({
                'success': True,
                'message': 'Successfully updated'
            })
        except exc.SQLAlchemyError as e:
            db.session.rollback()
            current_app.logger.error(str(e))
            return jsonify({'error': 'Database error occurred'}), 500
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(str(e))
            return jsonify({'error': 'Unexpected error occurred'}), 500

@vehicles.route('/api/kendaraan-mereks')
@login_required
def kendaraan_mereks():
    try:
        mereks = db.session.query(Kendaraan.merek).distinct().all()
        return jsonify([merek[0] for merek in mereks])
    except Exception as e:
        current_app.logger.error(str(e))
        return jsonify([])

@vehicles.route('/api/kendaraan-tipes')
@login_required
def kendaraan_tipes():
    try:
        tipes = db.session.query(Kendaraan.tipe).distinct().all()
        return jsonify([tipe[0] for tipe in tipes])
    except Exception as e:
        current_app.logger.error(str(e))
        return jsonify([])

@vehicles.route('/api/kendaraan/template', methods=['GET'])
@login_required
def download_template():
    # Create a CSV file in memory
    csv_data = StringIO()
    writer = csv.writer(csv_data)
    writer.writerow(['jenis', 'plat_nomor', 'merek', 'tipe', 'tahun', 'fuel_type', 'nama_instansi', 'load_category'])
    writer.writerow(['umum', 'B 1234 CD', 'Toyota', 'Avanza', '2020', 'bensin', '-', 'kendaraan_penumpang'])
    writer.writerow(['dinas', 'A 3456 EF', 'Honda', 'HR-V', '2021', 'bensin', 'Dinas Perhubungan', 'kendaraan_penumpang'])
    writer.writerow(['umum', 'D 5678 GH', 'Hino', 'Dutro', '2019', 'solar', '-', '<3.5ton'])
    
    # Reset the pointer to the beginning of the file
    csv_data.seek(0)
    
    # Create a temporary file to serve
    tmp = tempfile.NamedTemporaryFile(delete=False)
    with open(tmp.name, 'w') as f:
        f.write(csv_data.getvalue())
    
    return send_file(
        tmp.name,
        as_attachment=True,
        download_name='template_kendaraan.csv',
        mimetype='text/csv'
    )

@vehicles.route('/api/kendaraan/batch-upload', methods=['POST'])
@login_required
@csrf.exempt
def batch_upload_kendaraan():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
        
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'File must be CSV format'}), 400
        
    try:
        # Read CSV
        csv_content = file.read().decode('utf-8')
        csv_reader = csv.DictReader(StringIO(csv_content))
        
        # Tracking variables
        successes = 0
        errors = []
        row_num = 1  # Starting after header row
        
        for row in csv_reader:
            row_num += 1
            try:
                # Validate row data
                required_fields = ['jenis', 'plat_nomor', 'merek', 'tipe', 'tahun', 'fuel_type', 'load_category']
                missing = [f for f in required_fields if f not in row or not row.get(f)]
                
                if missing:
                    errors.append({
                        'row': row_num,
                        'error': f'Missing required fields: {", ".join(missing)}'
                    })
                    continue
                    
                # Clean and validate data
                plat = row['plat_nomor'].strip().upper()
                if len(plat) < 4:
                    errors.append({
                        'row': row_num,
                        'error': 'Invalid plate number format'
                    })
                    continue
                    
                try:
                    tahun = int(row['tahun'])
                    if tahun < 1900 or tahun > 2100:
                        errors.append({
                            'row': row_num,
                            'error': 'Invalid year (must be between 1900-2100)'
                        })
                        continue
                except ValueError:
                    errors.append({
                        'row': row_num,
                        'error': 'Year must be a valid number'
                    })
                    continue
                    
                jenis = row['jenis'].strip().lower()
                if jenis not in ['umum', 'dinas']:
                    errors.append({
                        'row': row_num,
                        'error': "Invalid vehicle type (must be 'umum' or 'dinas')"
                    })
                    continue
                    
                fuel_type = row['fuel_type'].strip().lower()
                if fuel_type not in ['bensin', 'solar']:
                    errors.append({
                        'row': row_num,
                        'error': "Invalid fuel type (must be 'bensin' or 'solar')"
                    })
                    continue
                    
                load_category = row['load_category'].strip()
                valid_categories = {
                    'bensin': ['kendaraan_muatan', 'kendaraan_penumpang'],
                    'solar': ['<3.5ton', '>=3.5ton']
                }
                
                if load_category not in valid_categories[fuel_type]:
                    errors.append({
                        'row': row_num,
                        'error': f'Invalid load category for {fuel_type}. Valid options are: {", ".join(valid_categories[fuel_type])}'
                    })
                    continue
                    
                # Handle nama_instansi
                nama_instansi = row.get('nama_instansi', '').strip()
                if jenis != 'dinas' or not nama_instansi:
                    nama_instansi = '-'
                    
                # Check if vehicle with this plate already exists
                existing = Kendaraan.query.filter_by(plat_nomor=plat).first()
                if existing:
                    errors.append({
                        'row': row_num,
                        'error': f'Plat nomor {plat} already exists'
                    })
                    continue
                    
                # Create new vehicle
                new_vehicle = Kendaraan(
                    jenis=jenis,
                    plat_nomor=plat,
                    merek=row['merek'].strip(),
                    tipe=row['tipe'].strip(),
                    tahun=tahun,
                    fuel_type=fuel_type,
                    nama_instansi=nama_instansi,
                    load_category=load_category
                )
                
                db.session.add(new_vehicle)
                db.session.flush()  # Flush but don't commit yet
                
                successes += 1
                
            except Exception as e:
                errors.append({
                    'row': row_num,
                    'error': str(e)
                })
                
        # Commit all successful additions if no errors
        if errors:
            db.session.rollback()
        else:
            db.session.commit()
            
        return jsonify({
            'successes': successes,
            'errors': errors,
            'total_rows': row_num - 1  # Subtract header row
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(str(e))
        return jsonify({'error': str(e)}), 500

@vehicles.route('/export-csv')
@login_required
def export_csv():
    try:
        # Get filter parameters
        plat_nomor = request.args.get('plat_nomor', '')
        merek = request.args.get('merek', '')
        tipe = request.args.get('tipe', '')
        jenis = request.args.get('jenis', '')
        fuel_type = request.args.get('fuel_type', '')
        
        # Build query with filters
        query = Kendaraan.query
        
        if plat_nomor:
            query = query.filter(Kendaraan.plat_nomor.ilike(f'%{plat_nomor}%'))
        if merek:
            query = query.filter(Kendaraan.merek.ilike(f'%{merek}%'))
        if tipe:
            query = query.filter(Kendaraan.tipe.ilike(f'%{tipe}%'))
        if jenis:
            query = query.filter(Kendaraan.jenis == jenis)
        if fuel_type:
            query = query.filter(Kendaraan.fuel_type == fuel_type)
            
        # Get all vehicles
        vehicles = query.all()
        
        # Create CSV file
        csv_data = StringIO()
        writer = csv.writer(csv_data)
        
        # Write header
        writer.writerow(['jenis', 'plat_nomor', 'merek', 'tipe', 'tahun', 'fuel_type', 'nama_instansi', 'load_category'])
        
        # Write data
        for vehicle in vehicles:
            writer.writerow([
                vehicle.jenis,
                vehicle.plat_nomor,
                vehicle.merek,
                vehicle.tipe,
                vehicle.tahun,
                vehicle.fuel_type,
                vehicle.nama_instansi,
                vehicle.load_category
            ])
            
        # Reset pointer to beginning of file
        csv_data.seek(0)
        
        # Create temporary file to serve
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        tmp = tempfile.NamedTemporaryFile(delete=False)
        with open(tmp.name, 'w') as f:
            f.write(csv_data.getvalue())
        
        return send_file(
            tmp.name,
            as_attachment=True,
            download_name=f'kendaraan_export_{timestamp}.csv',
            mimetype='text/csv'
        )
    except Exception as e:
        current_app.logger.error(str(e))
        flash('Error exporting data', 'error')
        return redirect(url_for('vehicles.dashboard')) 