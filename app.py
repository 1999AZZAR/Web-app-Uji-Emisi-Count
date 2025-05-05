from flask import Flask, render_template, request, jsonify, current_app, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
from datetime import datetime
import logging
import csv
import io
import tempfile
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///emisi.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Kendaraan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jenis = db.Column(db.String(10), nullable=False)
    plat_nomor = db.Column(db.String(20), unique=True, nullable=False)
    merek = db.Column(db.String(50), nullable=False)
    tipe = db.Column(db.String(50), nullable=False)
    tahun = db.Column(db.Integer, nullable=False)

class HasilUji(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kendaraan_id = db.Column(db.Integer, db.ForeignKey('kendaraan.id'), nullable=False)
    co = db.Column(db.Float, nullable=False)
    co2 = db.Column(db.Float, nullable=False)
    hc = db.Column(db.Float, nullable=False)
    o2 = db.Column(db.Float, nullable=False)
    lambda_val = db.Column(db.Float, nullable=False)
    lulus = db.Column(db.Boolean, nullable=False)
    valid = db.Column(db.Boolean, nullable=False)
    tanggal = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@app.route('/')
def halaman1():
    return render_template('halaman1.html')

@app.route('/halaman2')
def halaman2():
    return render_template('halaman2.html')

@app.route('/api/kendaraan-list')
def get_kendaraan_list():
    try:
        kendaraan_list = Kendaraan.query.all()
        return jsonify([{
            'plat_nomor': k.plat_nomor,
            'merek': k.merek,
            'tipe': k.tipe,
            'tahun': k.tahun
        } for k in kendaraan_list])
    except exc.SQLAlchemyError as e:
        logger.error(f'Database error: {str(e)}')
        return jsonify({'error': 'Database error occurred'}), 500

@app.route('/api/kendaraan/<plat_nomor>')
def get_kendaraan(plat_nomor):
    try:
        kendaraan = Kendaraan.query.filter_by(plat_nomor=plat_nomor).first()
        if kendaraan:
            return jsonify({
                'plat_nomor': kendaraan.plat_nomor,
                'merek': kendaraan.merek,
                'tipe': kendaraan.tipe,
                'tahun': kendaraan.tahun
            })
        return jsonify({'error': 'Vehicle not found'}), 404
    except exc.SQLAlchemyError as e:
        logger.error(f'Database error: {str(e)}')
        return jsonify({'error': 'Database error occurred'}), 500

@app.route('/halaman3')
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
        logger.error(f'Database error: {str(e)}')
        return render_template('error.html', 
                             error='Database error occurred. Please try again later.')

@app.route('/api/kendaraan', methods=['POST'])
def tambah_kendaraan():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Check required fields
        required_fields = ['jenis', 'plat_nomor', 'merek', 'tipe', 'tahun']
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return jsonify({'error': f'Missing required fields: {", ".join(missing_fields)}'}), 400

        # Validate plat_nomor format (basic validation)
        plat_nomor = data['plat_nomor'].strip().upper()
        if not plat_nomor or len(plat_nomor) < 4:
            return jsonify({'error': 'Invalid plate number format'}), 400

        # Validate tahun
        try:
            tahun = int(data['tahun'])
            if not (1900 <= tahun <= 2100):
                return jsonify({'error': 'Invalid year (must be between 1900 and 2100)'}), 400
        except ValueError:
            return jsonify({'error': 'Year must be a valid number'}), 400

        # Validate jenis
        if data['jenis'] not in ['umum', 'dinas']:
            return jsonify({'error': 'Invalid vehicle type (must be "umum" or "dinas")'}), 400

        # Create new vehicle
        kendaraan = Kendaraan(
            jenis=data['jenis'],
            plat_nomor=plat_nomor,
            merek=data['merek'].strip(),
            tipe=data['tipe'].strip(),
            tahun=tahun
        )
        
        db.session.add(kendaraan)
        db.session.commit()
        return jsonify({
            'success': True, 
            'id': kendaraan.id,
            'message': 'Data kendaraan berhasil disimpan'
        })

    except exc.IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'Plat nomor sudah terdaftar'}), 409
    except exc.SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f'Database error: {str(e)}')
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f'Unexpected error: {str(e)}')
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/api/hasil-uji', methods=['POST'])
def tambah_hasil():
    try:
        data = request.json
        if not all(key in data for key in ['plat_nomor', 'co', 'co2', 'hc', 'o2', 'lambda_val']):
            return jsonify({'error': 'Missing required fields'}), 400

        kendaraan = Kendaraan.query.filter_by(plat_nomor=data['plat_nomor']).first()
        if not kendaraan:
            return jsonify({'error': 'Kendaraan tidak ditemukan'}), 404

        # Validasi hasil uji
        valid = True
        if (data['co'] < 0 or data['co2'] < 0 or data['hc'] < 0 or 
            data['o2'] < 0 or data['lambda_val'] < 0):
            valid = False

        # Pengecekan lulus uji
        lulus = False
        if valid:
            if data['co'] <= 4.5 and data['hc'] <= 1200:
                lulus = True

        hasil = HasilUji(
            kendaraan_id=kendaraan.id,
            co=data['co'],
            co2=data['co2'],
            hc=data['hc'],
            o2=data['o2'],
            lambda_val=data['lambda_val'],
            valid=valid,
            lulus=lulus
        )
        db.session.add(hasil)
        db.session.commit()

        return jsonify({
            'success': True,
            'valid': valid,
            'lulus': lulus
        })

    except exc.SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f'Database error: {str(e)}')
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f'Unexpected error: {str(e)}')
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/export-csv')
def export_csv():
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', newline='') as temp_file:
            writer = csv.writer(temp_file)
            
            # Write headers
            writer.writerow(['Tanggal', 'Plat Nomor', 'Jenis', 'Merek', 'Tipe', 'Tahun', 
                           'CO (%)', 'CO2 (%)', 'HC (ppm)', 'O2 (%)', 'Lambda', 
                           'Status Valid', 'Status Lulus'])
            
            # Get all data
            results = db.session.query(Kendaraan, HasilUji).join(HasilUji).all()
            
            # Write data rows
            for kendaraan, hasil in results:
                writer.writerow([
                    hasil.tanggal.strftime('%Y-%m-%d %H:%M'),
                    kendaraan.plat_nomor,
                    kendaraan.jenis,
                    kendaraan.merek,
                    kendaraan.tipe,
                    kendaraan.tahun,
                    f"{hasil.co:.2f}",
                    f"{hasil.co2:.2f}",
                    hasil.hc,
                    f"{hasil.o2:.2f}",
                    f"{hasil.lambda_val:.2f}",
                    'Valid' if hasil.valid else 'Tidak Valid',
                    'Lulus' if hasil.lulus else 'Tidak Lulus'
                ])

        # Send the file
        return send_file(
            temp_file.name,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'hasil_uji_emisi_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )

    except Exception as e:
        logger.error(f'Error exporting CSV: {str(e)}')
        return jsonify({'error': 'Failed to export data'}), 500
    finally:
        # Clean up the temporary file
        try:
            os.unlink(temp_file.name)
        except:
            pass

if __name__ == '__main__':
    app.run(debug=True)
