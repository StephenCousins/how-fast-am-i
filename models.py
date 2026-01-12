"""
Database models for storing athlete data.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class ParkrunAthlete(db.Model):
    """Stores parkrun athlete data."""
    __tablename__ = 'parkrun_athletes'

    id = db.Column(db.Integer, primary_key=True)
    athlete_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200))
    total_runs = db.Column(db.Integer)

    # Time stats (in seconds)
    best_time_seconds = db.Column(db.Integer)
    average_time_seconds = db.Column(db.Integer)
    typical_avg_seconds = db.Column(db.Integer)
    recent_avg_seconds = db.Column(db.Integer)

    # Formatted times
    best_time = db.Column(db.String(20))
    average_time = db.Column(db.String(20))
    typical_avg_time = db.Column(db.String(20))
    recent_avg_time = db.Column(db.String(20))

    # Age grades
    avg_age_grade = db.Column(db.Float)
    recent_avg_age_grade = db.Column(db.Float)

    # PB info
    pb_date = db.Column(db.String(50))
    pb_event = db.Column(db.String(100))
    pb_age = db.Column(db.String(50))

    # Trend
    trend = db.Column(db.String(20))
    trend_message = db.Column(db.String(200))

    # Outlier info
    outlier_count = db.Column(db.Integer, default=0)
    normal_run_count = db.Column(db.Integer, default=0)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Track lookups
    lookup_count = db.Column(db.Integer, default=1)
    last_lookup_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ParkrunAthlete {self.athlete_id}: {self.name}>'


class PowerOf10Athlete(db.Model):
    """Stores Power of 10 athlete data."""
    __tablename__ = 'po10_athletes'

    id = db.Column(db.Integer, primary_key=True)
    athlete_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200))
    club = db.Column(db.String(200))
    gender = db.Column(db.String(10))
    age_group = db.Column(db.String(20))

    # PBs stored as JSON string
    pbs_json = db.Column(db.Text)

    # Overall stats
    overall_percentile = db.Column(db.Float)
    overall_age_grade = db.Column(db.Float)
    overall_ability_level = db.Column(db.String(20))

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Track lookups
    lookup_count = db.Column(db.Integer, default=1)
    last_lookup_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PowerOf10Athlete {self.athlete_id}: {self.name}>'


class Lookup(db.Model):
    """Tracks all lookups for analytics."""
    __tablename__ = 'lookups'

    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(20), nullable=False)  # 'parkrun' or 'po10'
    athlete_id = db.Column(db.String(20), nullable=False, index=True)
    athlete_name = db.Column(db.String(200))
    lookup_at = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(50))  # Optional, for rate limiting

    def __repr__(self):
        return f'<Lookup {self.source}:{self.athlete_id} at {self.lookup_at}>'
