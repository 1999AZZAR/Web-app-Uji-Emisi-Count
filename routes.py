from flask import Blueprint, render_template, request, jsonify, send_file, current_app, redirect, url_for, flash
from sqlalchemy import exc, inspect
from datetime import datetime
import csv, tempfile
from io import BytesIO, StringIO
from extensions import db
from models import Kendaraan, HasilUji, Config, User
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash

routes = Blueprint('routes', __name__)

@routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('routes.halaman1'))
        flash('Invalid username or password')
        return redirect(url_for('routes.login'))
    
    return render_template('login.html')

@routes.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('routes.login'))

@routes.route('/')
@login_required
def halaman1():
    return render_template('halaman1.html')

@routes.route('/halaman2')
@login_required
def halaman2():
    return render_template('halaman2.html')

@routes.route('/halaman3')
@login_required
def halaman3():
    try:
        # Query kendaraan, hasil uji, and user in one go
        data = db.session.query(Kendaraan, HasilUji, User).join(
            HasilUji, Kendaraan.id == HasilUji.kendaraan_id
        ).join(
            User, HasilUji.user_id == User.id
        ).all()
        total_kendaraan = Kendaraan.query.count()
        total_valid = HasilUji.query.filter_by(valid=True).count()
        total_lulus = HasilUji.query.filter_by(lulus=True).count()
        
        # Format the data for the template
        formatted_data = []
        for kendaraan, hasil, user in data:
            formatted_data.append({
                'kendaraan': kendaraan,
                'hasil': hasil,
                'operator': user.username,
                'tanggal': hasil.tanggal.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return render_template('halaman3.html',
                               data=formatted_data,
                               total_kendaraan=total_kendaraan,
                               total_valid=total_valid,
                               total_lulus=total_lulus)
    except exc.SQLAlchemyError as e:
        current_app.logger.error(f'Database error: {str(e)}')
        return render_template('error.html', error='Database error occurred. Please try again later.')

# This endpoint is inspired by the Project-Album repository (https://github.com/AMALNR98/Project-Album)
# which is licensed under MIT. Modifications have been made to suit our specific needs.
@routes.route('/api/kendaraan-list')
@login_required
def get_kendaraan_list():
    try:
        # pagination params
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 10))
        total = Kendaraan.query.count()
        items = Kendaraan.query.offset(offset).limit(limit).all()
        data = [{
            'jenis': k.jenis,
            'plat_nomor': k.plat_nomor,
            'merek': k.merek,
            'tipe': k.tipe,
            'tahun': k.tahun,
            'nama_instansi': k.nama_instansi,
            'load_category': k.load_category
        } for k in items]
        return jsonify({'items': data, 'total': total})
    except exc.SQLAlchemyError as e:
        current_app.logger.error(f'Database error: {str(e)}')
        return jsonify({'items': [], 'total': 0}), 500

@routes.route('/api/kendaraan/<plat_nomor>')
@login_required
def get_kendaraan(plat_nomor):
    try:
        kendaraan = Kendaraan.query.filter_by(plat_nomor=plat_nomor).first()
        if kendaraan:
            return jsonify({
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

@routes.route('/api/kendaraan', methods=['POST'])
@login_required
def tambah_kendaraan():
    try:
        data = request.json or {}
        # required fields
        required = ['jenis','plat_nomor','merek','tipe','tahun','fuel_type','nama_instansi', 'load_category']
        missing = [f for f in required if not data.get(f)]
        if missing:
            return jsonify({'error': f'Missing required fields: {", ".join(missing)}'}), 400
        # validate
        plat = data['plat_nomor'].strip().upper()
        if len(plat)<4: return jsonify({'error':'Invalid plate number format'}),400
        try:
            tahun = int(data['tahun'])
            if tahun<1900 or tahun>2100: return jsonify({'error':'Invalid year'}),400
        except:
            return jsonify({'error':'Year must be a valid number'}),400
        if data['jenis'] not in ['umum','dinas']:
            return jsonify({'error':'Invalid vehicle type'}),400
        if data.get('fuel_type') not in ['bensin', 'solar']:
            return jsonify({'error': 'Invalid fuel type'}), 400
        
        # Get load category from data and validate it
        load_category = data.get('load_category')
        if not load_category:
            return jsonify({'error': 'Load category is required'}), 400
        
        # Validate load category based on fuel type
        valid_categories = {
            'bensin': ['kendaraan_muatan', 'kendaraan_penumpang'],
            'solar': ['<3.5ton', '>=3.5ton']
        }
        if load_category not in valid_categories[data['fuel_type']]:
            return jsonify({'error': f'Invalid load category for {data["fuel_type"]}. Valid options are: {", ".join(valid_categories[data["fuel_type"]])}'}), 400
        
        inst = data.get('nama_instansi', '').strip()
        if data['jenis'] != 'dinas' or not inst: inst = '-'
        
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
        return jsonify({'success':True,'id':kendaraan.id,'message':'Berhasil disimpan'})
    except exc.IntegrityError:
        db.session.rollback()
        return jsonify({'error':'Plat nomor sudah terdaftar'}),409
    except exc.SQLAlchemyError as e:
        db.session.rollback(); current_app.logger.error(str(e))
        return jsonify({'error':'Database error occurred'}),500
    except Exception as e:
        db.session.rollback(); current_app.logger.error(str(e))
        return jsonify({'error':'Unexpected error occurred'}),500

@routes.route('/api/hasil-uji/tested-plats')
@login_required
def tested_plats():
    try:
        # return plats with at least one test record
        results = db.session.query(Kendaraan.plat_nomor).join(HasilUji).distinct().all()
        plats = [p[0] for p in results]
        return jsonify(plats)
    except exc.SQLAlchemyError as e:
        current_app.logger.error(str(e))
        return jsonify([])

@routes.route('/api/hasil-uji/<string:plat_nomor>', methods=['GET', 'POST', 'DELETE'])
@login_required
def manage_hasil(plat_nomor):
    kendaraan = Kendaraan.query.filter_by(plat_nomor=plat_nomor).first()
    if not kendaraan:
        return jsonify({'error': 'Kendaraan tidak ditemukan'}), 404

    if request.method == 'GET':
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
        
        # Add fuel type to response
        response_data['fuel_type'] = kendaraan.fuel_type
        
        return jsonify(response_data)

    # DELETE: clear test data
    if request.method == 'DELETE':
        hasil = HasilUji.query.filter_by(kendaraan_id=kendaraan.id).first()
        if not hasil:
            return jsonify({'error': 'No test data found'}), 404
        db.session.delete(hasil)
        db.session.commit()
        return jsonify({'message': 'Test data cleared'}), 200
    
    # POST: create new test data (handled by tambah_hasil function)
    elif request.method == 'POST':
        return tambah_hasil(plat_nomor)

@routes.route('/api/kendaraan/<plat_nomor>', methods=['PUT', 'DELETE'])
@login_required
def modify_kendaraan(plat_nomor):
    if request.method=='DELETE':
        try:
            knd=Kendaraan.query.filter_by(plat_nomor=plat_nomor).first_or_404()
            HasilUji.query.filter_by(kendaraan_id=knd.id).delete()
            db.session.delete(knd); db.session.commit()
            return jsonify({'success':True})
        except Exception as e:
            db.session.rollback(); current_app.logger.error(str(e))
            return jsonify({'error':'Delete failed'}),500
    # PUT update
    try:
        data=request.json or {}
        knd=Kendaraan.query.filter_by(plat_nomor=plat_nomor).first_or_404()
        for attr in ['merek','tipe','tahun','nama_instansi','fuel_type', 'load_category']:
            if attr in data: setattr(knd,attr,data[attr])
        db.session.commit(); return jsonify({'success':True})
    except Exception as e:
        db.session.rollback(); current_app.logger.error(str(e))
        return jsonify({'error':'Update failed'}),500

@routes.route('/export-csv')
@login_required
def export_csv():
    try:
        # Query all kendaraan with their hasil uji and user
        kendaraan_list = db.session.query(Kendaraan, HasilUji, User).join(
            HasilUji, Kendaraan.id == HasilUji.kendaraan_id
        ).join(
            User, HasilUji.user_id == User.id
        ).all()
        
        # Create CSV file
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Jenis', 'Plat Nomor', 'Merek', 'Tipe', 'Tahun', 'Jenis Bahan Bakar', 'Nama Instansi', 
                        'CO', 'CO2', 'HC', 'O2', 'Lambda', 'Opasitas (%)', 'Valid', 'Lulus', 'Tanggal', 'Operator', 'Load Category'])
        
        # Write data
        for kendaraan, hasil, user in kendaraan_list:
            # Map fuel type to Indonesian
            fuel_type = 'Solar' if kendaraan.fuel_type == 'solar' else 'Bensin'
            
            # Format the row data
            row = [
                kendaraan.jenis,
                kendaraan.plat_nomor,
                kendaraan.merek,
                kendaraan.tipe,
                kendaraan.tahun,
                fuel_type,
                kendaraan.nama_instansi or '-', 
                hasil.co,
                hasil.co2,
                hasil.hc,
                hasil.o2,
                hasil.lambda_val,
                f"{hasil.opacity:.1f}" if kendaraan.fuel_type == 'solar' and hasil.opacity is not None else 'N/A',
                'Ya' if hasil.valid else 'Tidak',
                'Lulus' if hasil.lulus else 'Tidak Lulus',
                hasil.tanggal.strftime('%Y-%m-%d %H:%M:%S') if hasil.tanggal else '',
                user.username if user else 'Unknown',
                kendaraan.load_category
            ]
            writer.writerow(row)
        
        # Create response
        output.seek(0)
        return send_file(
            BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='data_uji_emisi.csv'
        )
    except Exception as e:
        current_app.logger.error(f'Error exporting CSV: {str(e)}')
        flash('Gagal mengekspor data ke CSV')
        return redirect(url_for('routes.halaman3'))

@routes.route('/api/kendaraan-mereks')
@login_required
def kendaraan_mereks():
    try:
        results = db.session.query(Kendaraan.merek).distinct().all()
        mereks = [r[0] for r in results]
        return jsonify(mereks)
    except exc.SQLAlchemyError as e:
        current_app.logger.error(str(e))
        return jsonify([])

@routes.route('/config', methods=['GET', 'POST'])
@login_required
def config():
    if not current_user.is_admin():
        flash('Anda tidak memiliki akses ke halaman ini')
        return redirect(url_for('routes.halaman1'))

    config = Config.query.first()
    if not config:
        config = Config(
            co_max=0.5,
            co2_min=8.0,
            hc_max=200.0,
            o2_min=2.0,
            lambda_min=0.95,
            lambda_max=1.05,
            opacity_max=50.0
        )
        db.session.add(config)
        db.session.commit()

    if request.method == 'POST':
        try:
            config.co_max = float(request.form.get('co_max', 0.5))
            config.co2_min = float(request.form.get('co2_min', 8.0))
            config.hc_max = float(request.form.get('hc_max', 200.0))
            config.o2_min = float(request.form.get('o2_min', 2.0))
            config.lambda_min = float(request.form.get('lambda_min', 0.95))
            config.lambda_max = float(request.form.get('lambda_max', 1.05))
            config.opacity_max = float(request.form.get('opacity_max', 50.0))
            
            db.session.commit()
            flash('Konfigurasi berhasil disimpan', 'success')
            return redirect(url_for('routes.config'))
        except Exception as e:
            db.session.rollback()
            flash('Gagal menyimpan konfigurasi: ' + str(e), 'error')

    return render_template('config.html', config=config)

@routes.route('/save-config', methods=['POST'])
@login_required
def save_config():
    if not current_user.is_admin():
        flash('Anda tidak memiliki akses ke halaman ini')
        return redirect(url_for('routes.halaman1'))
    try:
        config = Config.get_config()
        config.co_max = float(request.form['co_max'])
        config.co2_min = float(request.form['co2_min'])
        config.hc_max = float(request.form['hc_max'])
        config.o2_min = float(request.form['o2_min'])
        config.lambda_min = float(request.form['lambda_min'])
        config.lambda_max = float(request.form['lambda_max'])
        config.opacity_max = float(request.form['opacity_max'])
        
        db.session.commit()
        flash('Konfigurasi berhasil disimpan')
        return redirect(url_for('routes.config'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error saving config: {str(e)}')
        flash('Terjadi kesalahan saat menyimpan konfigurasi')
        return redirect(url_for('routes.config'))

@routes.route('/api/kendaraan-tipes')
@login_required
def kendaraan_tipes():
    try:
        results = db.session.query(Kendaraan.tipe).distinct().all()
        tipes = [r[0] for r in results]
        return jsonify(tipes)
    except exc.SQLAlchemyError as e:
        current_app.logger.error(str(e))
        return jsonify([])

@routes.route('/api/kendaraan/template', methods=['GET'])
@login_required
def download_template():
    # CSV header template for batch kendaraan input
    headers = ['jenis', 'plat_nomor', 'merek', 'tipe', 'tahun', 'fuel_type', 'nama_instansi', 'load_category']
    # Note: fuel_type should be either 'bensin' or 'solar' (without quotes)
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(headers)
    mem = BytesIO()
    mem.write(si.getvalue().encode('utf-8'))
    mem.seek(0)
    return send_file(mem,
                     as_attachment=True,
                     download_name='template_kendaraan.csv',
                     mimetype='text/csv')

@routes.route('/api/kendaraan/batch-upload', methods=['POST'])
@login_required
def batch_upload_kendaraan():
    file = request.files.get('file')
    if not file:
        return jsonify({'error':'No file uploaded'}),400
    try:
        stream = StringIO(file.stream.read().decode('utf-8'))
        reader = csv.DictReader(stream)
        successes = 0
        errors = []
        for idx, row in enumerate(reader, start=2):
            try:
                # required fields
                required = ['jenis','plat_nomor','merek','tipe','tahun','fuel_type', 'load_category']
                missing = [f for f in required if not row.get(f)]
                if missing:
                    errors.append({'row':idx,'error':f'Missing {",".join(missing)}'})
                    continue
                
                jenis = row['jenis'].strip()
                plat = row['plat_nomor'].strip().upper()
                merek = row['merek'].strip()
                tipe = row['tipe'].strip()
                
                try:
                    tahun = int(row['tahun'])
                except:
                    errors.append({'row':idx,'error':'Invalid tahun'})
                    continue
                
                inst = row.get('nama_instansi','').strip() or '-'
                
                # Normalize fuel_type
                fuel_raw = row.get('fuel_type','').strip().lower()
                if fuel_raw in ['bensin', 'solar']:
                    fuel_type = 'bensin' if fuel_raw == 'bensin' else 'solar'
                else:
                    errors.append({'row':idx,'error':f'Invalid or missing fuel_type: {row.get("fuel_type","")}'})
                    continue
                
                if jenis not in ['umum','dinas']:
                    errors.append({'row':idx,'error':'Invalid jenis'})
                    continue
                
                if jenis != 'dinas':
                    inst = '-'
                
                load_category = row['load_category'].strip()
                valid_categories = {
                    'bensin': ['kendaraan_muatan', 'kendaraan_penumpang'],
                    'solar': ['<3.5ton', '>=3.5ton']
                }
                if load_category not in valid_categories[fuel_type]:
                    errors.append({'row':idx,'error':f'Invalid load_category for {fuel_type}'})
                    continue
                
                kendaraan = Kendaraan(
                    jenis=jenis,
                    plat_nomor=plat,
                    merek=merek,
                    tipe=tipe,
                    tahun=tahun,
                    nama_instansi=inst,
                    fuel_type=fuel_type,
                    load_category=load_category
                )
                db.session.add(kendaraan)
                
                try:
                    db.session.flush()
                except exc.IntegrityError:
                    db.session.rollback()
                    errors.append({'row':idx,'error':'Duplicate plat'})
                    continue
                
                # Get parameters based on vehicle type
                if fuel_type == 'solar':
                    # Determine year range
                    year_range = '<2010' if tahun < 2010 else '2010-2021' if tahun <= 2021 else '>2021'
                    params = config.diesel_parameters[load_category][year_range]
                    
                    # Validate opacity
                    opacity = float(row.get('opacity', 0))
                    if opacity > params['opacity_max']:
                        valid = False
                        validasi = f'Tidak Valid: Opasitas melebihi batas maksimum ({params["opacity_max"]}%)'
                    
                    # Check passing criteria
                    if opacity <= params['opacity_max']:
                        lulus = True
                        kelulusan = f'Lulus: Opasitas dalam batas ({params["opacity_max"]}%)'
                    else:
                        kelulusan = f'Tidak Lulus: Opasitas melebihi batas ({params["opacity_max"]}%)'
                else:  # bensin
                    # Determine year range
                    year_range = '<2007' if tahun < 2007 else '2007-2018' if tahun <= 2018 else '>2018'
                    params = config.gasoline_parameters[load_category][year_range]
                    
                    # Validate parameters
                    co = float(row.get('co', 0))
                    hc = float(row.get('hc', 0))
                    co2 = float(row.get('co2', 0))
                    o2 = float(row.get('o2', 0))
                    lambda_value = float(row.get('lambda', 0))
                    
                    if co is None or co > params['co_max']:
                        valid = False
                        validasi = f'Tidak Valid: CO melebihi batas maksimum ({params["co_max"]}%)'
                    if hc is None or hc > params['hc_max']:
                        valid = False
                        validasi = f'Tidak Valid: HC melebihi batas maksimum ({params["hc_max"]} ppm)'
                    if co2 is None or co2 > params['co2_max']:
                        valid = False
                        validasi = f'Tidak Valid: CO2 melebihi batas maksimum ({params["co2_max"]}%)'
                    if o2 is None or o2 > params['o2_max']:
                        valid = False
                        validasi = f'Tidak Valid: O2 melebihi batas maksimum ({params["o2_max"]}%)'
                    if lambda_value is None or lambda_value > params['lambda_max']:
                        valid = False
                        validasi = f'Tidak Valid: Lambda melebihi batas maksimum ({params["lambda_max"]})'
                    
                    # Check passing criteria
                    if (co is not None and co <= params['co_max'] and
                        hc is not None and hc <= params['hc_max'] and
                        co2 is not None and co2 <= params['co2_max'] and
                        o2 is not None and o2 <= params['o2_max'] and
                        lambda_value is not None and lambda_value <= params['lambda_max']):
                        lulus = True
                        kelulusan = 'Lulus: Semua parameter dalam batas'
                    else:
                        kelulusan = 'Tidak Lulus: Ada parameter di luar batas'
                
                hasil_uji = HasilUji(
                    kendaraan=kendaraan,
                    co=co,
                    hc=hc,
                    co2=co2,
                    o2=o2,
                    lambda_val=lambda_value,
                    opacity=opacity,
                    valid=valid,
                    lulus=lulus,
                    tanggal=datetime.now(),
                    user_id=current_user.id
                )
                db.session.add(hasil_uji)
                
                successes += 1
            except Exception as e:
                errors.append({'row':idx,'error':str(e)})
                continue
        db.session.commit()
        return jsonify({'successes':successes,'errors':errors})
    except Exception as e:
        current_app.logger.error(str(e))
        return jsonify({'error':'Processing error'}),500
