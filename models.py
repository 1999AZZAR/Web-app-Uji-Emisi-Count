from datetime import datetime
from extensions import db
from sqlalchemy import CheckConstraint
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class Kendaraan(db.Model):
    __tablename__ = 'kendaraan'
    __table_args__ = (
        CheckConstraint("jenis IN ('umum','dinas')", name='ck_kendaraan_jenis'),
        CheckConstraint('tahun >= 1900 AND tahun <= 2100', name='ck_kendaraan_tahun_range'),
    )
    id = db.Column(db.Integer, primary_key=True)
    jenis = db.Column(db.String(10), nullable=False)
    plat_nomor = db.Column(db.String(20), unique=True, nullable=False)
    merek = db.Column(db.String(50), nullable=False)
    tipe = db.Column(db.String(50), nullable=False)
    tahun = db.Column(db.Integer, nullable=False)
    nama_instansi = db.Column(db.String(100), nullable=True, default='-')

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
    co_max = db.Column(db.Float, nullable=False, default=0.5)
    co2_min = db.Column(db.Float, nullable=False, default=8.0)
    hc_max = db.Column(db.Float, nullable=False, default=200.0)
    o2_min = db.Column(db.Float, nullable=False, default=2.0)
    lambda_min = db.Column(db.Float, nullable=False, default=0.95)
    lambda_max = db.Column(db.Float, nullable=False, default=1.05)
    
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
    )
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    kendaraan = db.relationship('Kendaraan', backref='hasil_uji')
    user = db.relationship('User', backref='hasil_uji')
