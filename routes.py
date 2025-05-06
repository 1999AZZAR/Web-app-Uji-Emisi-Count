from flask import Blueprint, render_template, request, jsonify, send_file, current_app
from sqlalchemy import exc, inspect
from datetime import datetime
import csv, tempfile
from io import BytesIO, StringIO
from extensions import db
from models import Kendaraan, HasilUji
from flask import Blueprint, render_template, request, jsonify, current_app, send_file

routes = Blueprint('routes', __name__)

@routes.route('/')
def halaman1():
    return render_template('halaman1.html')

@routes.route('/halaman2')
def halaman2():
    return render_template('halaman2.html')

@routes.route('/halaman3')
def halaman3():
    try:
        kendaraan_list = db.session.query(Kendaraan, HasilUji).join(HasilUji).all()
        total_kendaraan = Kendaraan.query.count()
        total_valid = HasilUji.query.filter_by(valid=True).count()
        total_lulus = HasilUji.query.filter_by(lulus=True).count()
        return render_template('halaman3.html',
                               data=kendaraan_list,
                               total_kendaraan=total_kendaraan,
                               total_valid=total_valid,
                               total_lulus=total_lulus)
    except exc.SQLAlchemyError as e:
        current_app.logger.error(f'Database error: {str(e)}')
        return render_template('error.html', error='Database error occurred. Please try again later.')

@routes.route('/api/kendaraan-list')
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
def tambah_hasil():
    try:
        data = request.json or {}
        needed=['plat_nomor','co','co2','hc','o2','lambda_val']
        if any(k not in data for k in needed):
            return jsonify({'error':'Missing required fields'}),400
        knd = Kendaraan.query.filter_by(plat_nomor=data['plat_nomor']).first()
        if not knd: return jsonify({'error':'Kendaraan tidak ditemukan'}),404
        valid=True
        if any(data[f]<0 for f in ['co','co2','hc','o2','lambda_val']): valid=False
        lulus=False
        if valid and data['co']<=4.5 and data['hc']<=1200: lulus=True
        hasil=HasilUji(kendaraan_id=knd.id,co=data['co'],co2=data['co2'],hc=data['hc'],o2=data['o2'],lambda_val=data['lambda_val'],valid=valid,lulus=lulus)
        db.session.add(hasil); db.session.commit()
        return jsonify({'success':True,'valid':valid,'lulus':lulus})
    except exc.SQLAlchemyError as e:
        db.session.rollback(); current_app.logger.error(str(e))
        return jsonify({'error':'Database error occurred'}),500
    except Exception as e:
        db.session.rollback(); current_app.logger.error(str(e))
        return jsonify({'error':'Unexpected error occurred'}),500

@routes.route('/api/hasil-uji/<plat_nomor>', methods=['GET', 'PUT', 'DELETE'])
def manage_hasil(plat_nomor):
    knd = Kendaraan.query.filter_by(plat_nomor=plat_nomor).first_or_404()
    # DELETE: clear test data
    if request.method == 'DELETE':
        hasil = HasilUji.query.filter_by(kendaraan_id=knd.id).first()
        if not hasil:
            return jsonify({'error': 'No test data to clear'}), 404
        db.session.delete(hasil)
        db.session.commit()
        return jsonify({'success': True})
    hasil = HasilUji.query.filter_by(kendaraan_id=knd.id).first()
    if request.method == 'GET':
        if not hasil:
            return jsonify({'error': 'Data not found'}), 404
        return jsonify({
            'plat_nomor': plat_nomor,
            'co': hasil.co,
            'co2': hasil.co2,
            'hc': hasil.hc,
            'o2': hasil.o2,
            'lambda_val': hasil.lambda_val,
            'valid': hasil.valid,
            'lulus': hasil.lulus
        })
    # PUT update
    data = request.json or {}
    if any(k not in data for k in ['co','co2','hc','o2','lambda_val']):
        return jsonify({'error': 'Missing required fields'}), 400
    # calculate valid and lulus
    valid = all(data[f] >= 0 for f in ['co','co2','hc','o2','lambda_val'])
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

@routes.route('/api/kendaraan/<plat_nomor>', methods=['PUT','DELETE'])
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
def export_csv():
    try:
        results = db.session.query(Kendaraan, HasilUji).join(HasilUji).all()
        # use StringIO to build CSV text then encode
        si = StringIO()
        writer = csv.writer(si)
        writer.writerow(['Tanggal','Plat Nomor','Jenis','Merek','Tipe','Tahun','CO','CO2','HC','O2','Lambda','Valid','Lulus'])
        for knd, hasil in results:
            writer.writerow([
                hasil.tanggal.strftime('%Y-%m-%d %H:%M'),
                knd.plat_nomor, knd.jenis, knd.merek, knd.tipe, knd.tahun,
                hasil.co, hasil.co2, hasil.hc, hasil.o2, hasil.lambda_val,
                hasil.valid, hasil.lulus
            ])
        mem = BytesIO()
        mem.write(si.getvalue().encode('utf-8'))
        mem.seek(0)
        return send_file(
            mem,
            mimetype='text/csv',
            as_attachment=True,
            download_name='emisi.csv'
        )
    except Exception as e:
        current_app.logger.error(str(e))
        return jsonify({'error':'CSV export failed'}),500

@routes.route('/api/kendaraan-mereks')
def kendaraan_mereks():
    try:
        results = db.session.query(Kendaraan.merek).distinct().all()
        mereks = [r[0] for r in results]
        return jsonify(mereks)
    except exc.SQLAlchemyError as e:
        current_app.logger.error(str(e))
        return jsonify([])

@routes.route('/api/kendaraan-tipes')
def kendaraan_tipes():
    try:
        results = db.session.query(Kendaraan.tipe).distinct().all()
        tipes = [r[0] for r in results]
        return jsonify(tipes)
    except exc.SQLAlchemyError as e:
        current_app.logger.error(str(e))
        return jsonify([])

@routes.route('/api/kendaraan/template', methods=['GET'])
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
