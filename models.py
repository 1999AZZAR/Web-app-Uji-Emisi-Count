from datetime import datetime
from extensions import db
from sqlalchemy import CheckConstraint

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
