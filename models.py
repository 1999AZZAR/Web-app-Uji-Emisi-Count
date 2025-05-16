from datetime import datetime
from extensions import db
from sqlalchemy import CheckConstraint
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class Kendaraan(db.Model):
    __tablename__ = 'kendaraan'
    __table_args__ = (
        CheckConstraint("jenis IN ('umum','dinas')", name='ck_kendaraan_jenis'),
        CheckConstraint("fuel_type IN ('petrol','diesel')", name='ck_kendaraan_fuel_type'),
        CheckConstraint('tahun >= 1900 AND tahun <= 2100', name='ck_kendaraan_tahun_range'),
        CheckConstraint("load_category IN ('kendaraan_muatan', 'kendaraan_penumpang', '<3.5ton', '>=3.5ton')", name='ck_kendaraan_load_category'),
    )
    id = db.Column(db.Integer, primary_key=True)
    jenis = db.Column(db.String(10), nullable=False)
    plat_nomor = db.Column(db.String(20), unique=True, nullable=False)
    merek = db.Column(db.String(50), nullable=False)
    tipe = db.Column(db.String(50), nullable=False)
    tahun = db.Column(db.Integer, nullable=False)
    fuel_type = db.Column(db.String(10), nullable=False, default='petrol')
    nama_instansi = db.Column(db.String(100), nullable=True, default='-')
    load_category = db.Column(db.String(20), nullable=False, default='kendaraan_penumpang')

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False, default='general')

    def is_admin(self):
        return self.role == 'admin'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Config(db.Model):
    __tablename__ = 'config'
    id = db.Column(db.Integer, primary_key=True)
    
    # Gasoline parameters
    gasoline_co_max = db.Column(db.Float, nullable=False, default=0.5)
    gasoline_hc_max = db.Column(db.Float, nullable=False, default=200.0)
    gasoline_co2_max = db.Column(db.Float, nullable=False, default=12.0)
    gasoline_o2_max = db.Column(db.Float, nullable=False, default=1.0)
    gasoline_lambda_max = db.Column(db.Float, nullable=False, default=1.05)
    
    # Diesel parameters
    diesel_opacity_max = db.Column(db.Float, nullable=False, default=50.0)
    
    # Parameters for different categories and year ranges
    gasoline_parameters = db.Column(db.JSON, nullable=False, default={
        'kendaraan_muatan': {
            '<2007': {'co_max': 0.5, 'hc_max': 200.0, 'co2_max': 12.0, 'o2_max': 1.0, 'lambda_max': 1.05},
            '2007-2018': {'co_max': 0.5, 'hc_max': 200.0, 'co2_max': 12.0, 'o2_max': 1.0, 'lambda_max': 1.05},
            '>2018': {'co_max': 0.5, 'hc_max': 200.0, 'co2_max': 12.0, 'o2_max': 1.0, 'lambda_max': 1.05}
        },
        'kendaraan_penumpang': {
            '<2007': {'co_max': 0.5, 'hc_max': 200.0, 'co2_max': 12.0, 'o2_max': 1.0, 'lambda_max': 1.05},
            '2007-2018': {'co_max': 0.5, 'hc_max': 200.0, 'co2_max': 12.0, 'o2_max': 1.0, 'lambda_max': 1.05},
            '>2018': {'co_max': 0.5, 'hc_max': 200.0, 'co2_max': 12.0, 'o2_max': 1.0, 'lambda_max': 1.05}
        }
    })
    
    diesel_parameters = db.Column(db.JSON, nullable=False, default={
        '<3.5ton': {
            '<2010': {'opacity_max': 50.0},
            '2010-2021': {'opacity_max': 50.0},
            '>2021': {'opacity_max': 50.0}
        },
        '>=3.5ton': {
            '<2010': {'opacity_max': 50.0},
            '2010-2021': {'opacity_max': 50.0},
            '>2021': {'opacity_max': 50.0}
        }
    })  # For diesel vehicles
    
    @staticmethod
    def get_config():
        config = Config.query.first()
        if not config:
            config = Config()
            db.session.add(config)
            db.session.commit()
        return config

class HasilUji(db.Model):
    __tablename__ = 'hasil_uji'
    __table_args__ = (
        CheckConstraint('co >= 0', name='ck_co_nonneg'),
        CheckConstraint('co2 >= 0', name='ck_co2_nonneg'),
        CheckConstraint('hc >= 0', name='ck_hc_nonneg'),
        CheckConstraint('o2 >= 0', name='ck_o2_nonneg'),
        CheckConstraint('lambda_val >= 0', name='ck_lambda_nonneg'),
        CheckConstraint('opacity IS NULL OR opacity >= 0', name='ck_opacity_nonneg'),
    )
    id = db.Column(db.Integer, primary_key=True)
    kendaraan_id = db.Column(db.Integer, db.ForeignKey('kendaraan.id'), nullable=False)
    co = db.Column(db.Float, nullable=False)
    co2 = db.Column(db.Float, nullable=False)
    hc = db.Column(db.Float, nullable=False)
    o2 = db.Column(db.Float, nullable=False)
    lambda_val = db.Column(db.Float, nullable=False)
    opacity = db.Column(db.Float, nullable=True)  # Only required for diesel vehicles
    lulus = db.Column(db.Boolean, nullable=False)
    valid = db.Column(db.Boolean, nullable=False)
    tanggal = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    kendaraan = db.relationship('Kendaraan', backref='hasil_uji')
    user = db.relationship('User', backref='hasil_uji')
