from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from sqlalchemy import exc, inspect
from datetime import datetime
import csv, tempfile
from io import BytesIO, StringIO
from extensions import db
from models import Kendaraan, HasilUji, Config, User
from flask import Blueprint, render_template, request, jsonify, current_app, send_file, redirect, url_for, flash
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
            'nama_instansi': k.nama_instansi
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
                'nama_instansi': kendaraan.nama_instansi
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
        required = ['jenis','plat_nomor','merek','tipe','tahun']
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
        inst = data.get('nama_instansi','').strip()
        if data['jenis']!='dinas' or not inst: inst='-'
        kendaraan = Kendaraan(jenis=data['jenis'],plat_nomor=plat,merek=data['merek'].strip(),tipe=data['tipe'].strip(),tahun=tahun,nama_instansi=inst)
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

@routes.route('/api/hasil-uji', methods=['POST'])
@login_required
def tambah_hasil():
    try:
        data = request.get_json()
        kendaraan = Kendaraan.query.filter_by(plat_nomor=data['plat_nomor']).first()
        
        if not kendaraan:
            return jsonify({'error': 'Kendaraan tidak ditemukan'}), 404

        hasil = HasilUji(
            kendaraan_id=kendaraan.id,
            co=float(data['co']),
            co2=float(data['co2']),
            hc=float(data['hc']),
            o2=float(data['o2']),
            lambda_val=float(data['lambda_val']),
            lulus=data['lulus'],
            valid=data['valid'],
            user_id=current_user.id
        )
        db.session.add(hasil)
        db.session.commit()
        return jsonify({'message': 'Hasil uji berhasil ditambahkan'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@routes.route('/api/hasil-uji/<plat_nomor>', methods=['GET', 'POST', 'DELETE'])
@login_required
def manage_hasil(plat_nomor):
    knd = Kendaraan.query.filter_by(plat_nomor=plat_nomor).first_or_404()
    
    # DELETE: clear test data
    if request.method == 'DELETE':
        hasil = HasilUji.query.filter_by(kendaraan_id=knd.id).first()
        if not hasil:
            return jsonify({'error': 'No test data found'}), 404
        db.session.delete(hasil)
        db.session.commit()
        return jsonify({'message': 'Test data cleared'}), 200
    
    # POST: create new test data
    elif request.method == 'POST':
        try:
            data = request.get_json()
            hasil = HasilUji(
                kendaraan_id=knd.id,
                co=float(data['co']),
                co2=float(data['co2']),
                hc=float(data['hc']),
                o2=float(data['o2']),
                lambda_val=float(data['lambda_val']),
                valid=True,  # Always valid for now
                lulus=True,  # Always pass for now
                user_id=data['user_id']
            )
            db.session.add(hasil)
            db.session.commit()
            return jsonify({
                'valid': hasil.valid,
                'lulus': hasil.lulus,
                'operator': hasil.user.username
            }), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    # GET: get test data
    else:
        hasil = HasilUji.query.filter_by(kendaraan_id=knd.id).first()
        if not hasil:
            return jsonify({}), 404
        return jsonify({
            'co': hasil.co,
            'co2': hasil.co2,
            'hc': hasil.hc,
            'o2': hasil.o2,
            'lambda_val': hasil.lambda_val,
            'valid': hasil.valid,
            'lulus': hasil.lulus,
            'operator': hasil.user.username
        }), 200
    lulus = valid and data['co'] <= 4.5 and data['hc'] <= 1200
    if not hasil:
        hasil = HasilUji(kendaraan_id=knd.id)
        db.session.add(hasil)
    # assign
    hasil.co = data['co']
    hasil.co2 = data['co2']
    hasil.hc = data['hc']
    hasil.o2 = data['o2']
    hasil.lambda_val = data['lambda_val']
    hasil.valid = valid
    hasil.lulus = lulus
    db.session.commit()
    return jsonify({'success': True, 'valid': valid, 'lulus': lulus})

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
        for attr in ['merek','tipe','tahun','nama_instansi']:
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
        writer.writerow(['Jenis', 'Plat Nomor', 'Merek', 'Tipe', 'Tahun', 'Nama Instansi', 
                        'CO', 'CO2', 'HC', 'O2', 'Lambda', 'Valid', 'Lulus', 'Tanggal', 'Operator'])
        
        # Write data
        for kendaraan, hasil, user in kendaraan_list:
            writer.writerow([
                kendaraan.jenis,
                kendaraan.plat_nomor,
                kendaraan.merek,
                kendaraan.tipe,
                kendaraan.tahun,
                kendaraan.nama_instansi,
                hasil.co,
                hasil.co2,
                hasil.hc,
                hasil.o2,
                hasil.lambda_val,
                'Ya' if hasil.valid else 'Tidak',
                'Ya' if hasil.lulus else 'Tidak',
                hasil.tanggal.strftime('%Y-%m-%d %H:%M:%S'),
                user.username
            ])
        
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
            lambda_max=1.05
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
    header = ['jenis','plat_nomor','merek','tipe','tahun','nama_instansi']
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(header)
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
            # required fields
            required = ['jenis','plat_nomor','merek','tipe','tahun']
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
            if jenis not in ['umum','dinas']:
                errors.append({'row':idx,'error':'Invalid jenis'})
                continue
            if jenis != 'dinas':
                inst = '-'
            kendaraan = Kendaraan(jenis=jenis,plat_nomor=plat,merek=merek,tipe=tipe,tahun=tahun,nama_instansi=inst)
            db.session.add(kendaraan)
            try:
                db.session.flush()
            except exc.IntegrityError:
                db.session.rollback()
                errors.append({'row':idx,'error':'Duplicate plat'})
                continue
            successes += 1
        db.session.commit()
        return jsonify({'successes':successes,'errors':errors})
    except Exception as e:
        current_app.logger.error(str(e))
        return jsonify({'error':'Processing error'}),500
