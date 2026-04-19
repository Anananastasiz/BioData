from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Study(db.Model):
    __tablename__ = 'studies'
    
    id = db.Column(db.Integer, primary_key=True)
    study_id = db.Column(db.Integer, unique=True, nullable=False, index=True)
    realm = db.Column(db.String(50))
    climate = db.Column(db.String(50))
    habitat = db.Column(db.String(100))
    protected_area = db.Column(db.Boolean, default=False)
    biome_map = db.Column(db.String(150))
    taxa = db.Column(db.String(150))
    organisms = db.Column(db.String(200))
    title = db.Column(db.String(500))
    has_plot = db.Column(db.String(1))
    data_points = db.Column(db.Integer)
    start_year = db.Column(db.Integer)
    end_year = db.Column(db.Integer)
    cent_lat = db.Column(db.Float)
    cent_long = db.Column(db.Float)
    number_of_species = db.Column(db.Integer)
    number_of_samples = db.Column(db.Integer)
    grain_sq_km = db.Column(db.Float)
    area_sq_km = db.Column(db.Float)
    abundance_type = db.Column(db.String(50))
    biomass_type = db.Column(db.String(50))
    web_link = db.Column(db.String(500))
    license = db.Column(db.String(50))
    
    # Связь с образцами (один ко многим)
    samples = db.relationship('Sample', backref='study', lazy=True, cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'study_id': self.study_id,
            'realm': self.realm,
            'climate': self.climate,
            'habitat': self.habitat,
            'title': self.title,
            'start_year': self.start_year,
            'end_year': self.end_year,
            'cent_lat': self.cent_lat,
            'cent_long': self.cent_long,
            'number_of_species': self.number_of_species
        }


class Sample(db.Model):
    __tablename__ = 'samples'
    
    id = db.Column(db.Integer, primary_key=True)
    study_id = db.Column(db.Integer, db.ForeignKey('studies.id'), nullable=False)
    sample_name = db.Column(db.String(200))
    year = db.Column(db.Integer)
    month = db.Column(db.Integer)
    day = db.Column(db.Integer)
    abundance = db.Column(db.Float)
    biomass = db.Column(db.Float)
    sample_desc = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'study_id': self.study_id,
            'sample_name': self.sample_name,
            'year': self.year,
            'month': self.month,
            'day': self.day,
            'abundance': self.abundance,
            'biomass': self.biomass
        }
