from datetime import datetime
from extensions import db
from sqlalchemy import CheckConstraint
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class Kendaraan(db.Model):
    __tablename__ = 'kendaraan'
    __table_args__ = (
        CheckConstraint("jenis IN ('umum','dinas')", name='ck_kendaraan_jenis'),
        CheckConstraint("fuel_type IN ('bensin','solar')", name='ck_kendaraan_fuel_type'),
        CheckConstraint('tahun >= 1900 AND tahun <= 2100', name='ck_kendaraan_tahun_range'),
        CheckConstraint("load_category IN ('kendaraan_muatan', 'kendaraan_penumpang', '<3.5ton', '>=3.5ton')", name='ck_kendaraan_load_category'),
    )
    id = db.Column(db.Integer, primary_key=True)
    jenis = db.Column(db.String(10), nullable=False)
    plat_nomor = db.Column(db.String(20), unique=True, nullable=False)
    merek = db.Column(db.String(50), nullable=False)
    tipe = db.Column(db.String(50), nullable=False)
    tahun = db.Column(db.Integer, nullable=False)
    fuel_type = db.Column(db.String(10), nullable=False, default='bensin')
    nama_instansi = db.Column(db.String(100), nullable=True, default='-')
    load_category = db.Column(db.String(20), nullable=False, default='kendaraan_penumpang')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Kendaraan {self.plat_nomor}>'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'operator', 'viewer')", name='ck_users_role'),
    )
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False, default='operator')
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Properties to handle fullname functionality without database column
    @property
    def fullname(self):
        return self.username  # Fall back to username if no fullname exists
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
        
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def is_admin(self):
        return self.role == 'admin'
        
    def is_operator(self):
        return self.role == 'operator' or self.role == 'admin'
        
    def is_viewer(self):
        return self.role == 'viewer' or self.role == 'operator' or self.role == 'admin'
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def is_active(self):
        return self.active
        
    def update_login_timestamp(self):
        self.last_login = datetime.utcnow()

    def __repr__(self):
        return f'<User {self.username}>'

class Config(db.Model):
    __tablename__ = 'config'
    id = db.Column(db.Integer, primary_key=True)
    
    # Bensin parameters with aliases for backward compatibility
    bensin_co_max = db.Column('gasoline_co_max', db.Float, nullable=False, default=0.5)
    bensin_hc_max = db.Column('gasoline_hc_max', db.Float, nullable=False, default=200.0)
    bensin_co2_max = db.Column('gasoline_co2_max', db.Float, nullable=False, default=12.0)
    bensin_o2_max = db.Column('gasoline_o2_max', db.Float, nullable=False, default=1.0)
    bensin_lambda_max = db.Column('gasoline_lambda_max', db.Float, nullable=False, default=1.05)
    
    # Basic parameters
    co_max = db.Column(db.Float, nullable=False, default=0.5)
    co2_min = db.Column(db.Float, nullable=False, default=8.0)
    co2_max = db.Column(db.Float, nullable=False, default=12.0)
    hc_max = db.Column(db.Float, nullable=False, default=200.0)
    o2_min = db.Column(db.Float, nullable=False, default=0.1)
    o2_max = db.Column(db.Float, nullable=False, default=2.0)
    lambda_min = db.Column(db.Float, nullable=False, default=0.95)
    lambda_max = db.Column(db.Float, nullable=False, default=1.05)
    
    # Solar parameters with alias for backward compatibility
    solar_opacity_max = db.Column('diesel_opacity_max', db.Float, nullable=False, default=50.0)
    
    # Parameter lookup storage - using column names to match database
    bensin_parameters = db.Column('gasoline_parameters', db.JSON, nullable=False, default={
        'kendaraan_muatan': {
            '<2007': {'co_max': 4.5, 'hc_max': 1200, 'co2_min': 5.5, 'lambda_min': 0.8, 'lambda_max': 1.2},
            '2007-2018': {'co_max': 1.5, 'hc_max': 300, 'co2_min': 7.5, 'lambda_min': 0.9, 'lambda_max': 1.1},
            '>2018': {'co_max': 0.5, 'hc_max': 100, 'co2_min': 9.0, 'lambda_min': 0.97, 'lambda_max': 1.03}
        },
        'kendaraan_penumpang': {
            '<2007': {'co_max': 3.5, 'hc_max': 800, 'co2_min': 6.5, 'lambda_min': 0.85, 'lambda_max': 1.15},
            '2007-2018': {'co_max': 1.0, 'hc_max': 200, 'co2_min': 8.0, 'lambda_min': 0.93, 'lambda_max': 1.07},
            '>2018': {'co_max': 0.3, 'hc_max': 70, 'co2_min': 10.0, 'lambda_min': 0.98, 'lambda_max': 1.02}
        }
    })
    
    # Solar parameters using column name to match database
    solar_parameters = db.Column('diesel_parameters', db.JSON, nullable=False, default={
        '<3.5ton': {
            '<2010': {'opacity_max': 70.0},
            '2010-2021': {'opacity_max': 40.0},
            '>2021': {'opacity_max': 25.0}
        },
        '>=3.5ton': {
            '<2010': {'opacity_max': 80.0},
            '2010-2021': {'opacity_max': 50.0},
            '>2021': {'opacity_max': 30.0}
        }
    })
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @staticmethod
    def get_config():
        config = Config.query.first()
        if not config:
            config = Config()
            db.session.add(config)
            db.session.commit()
        return config
        
    def __repr__(self):
        return f'<Config {self.id}>'

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
    kendaraan_id = db.Column(db.Integer, db.ForeignKey('kendaraan.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    tanggal = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Emission values
    co = db.Column(db.Float, nullable=False, default=0) 
    co2 = db.Column(db.Float, nullable=False, default=0)
    hc = db.Column(db.Float, nullable=False, default=0)  
    o2 = db.Column(db.Float, nullable=False, default=0)
    lambda_val = db.Column(db.Float, nullable=False, default=0)  # Lambda value
    opacity = db.Column(db.Float, nullable=True)  # Only required for solar vehicles
    
    # Results
    valid = db.Column(db.Boolean, nullable=False, default=False)
    lulus = db.Column(db.Boolean, nullable=False, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    kendaraan = db.relationship('Kendaraan', backref=db.backref('hasil_uji', lazy=True, cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('hasil_uji', lazy=True))
    
    def __repr__(self):
        return f'<HasilUji id={self.id} kendaraan_id={self.kendaraan_id}>'

class AuditLog(db.Model):
    """Model for tracking important changes to the database"""
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('audit_logs', lazy=True))
    
    def __repr__(self):
        return f'<AuditLog id={self.id} action={self.action}>'
