from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Initialize SQLAlchemy instance outside of create_app to be imported by models
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    niches = db.relationship('Niche', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

# The user routes blueprint should be in src/routes/user.py, not here.
# The previous content was incorrect and has been replaced with the model definition.
