from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from flask_login import UserMixin
from sqlalchemy import ForeignKeyConstraint, PrimaryKeyConstraint
from enum import Enum

db = SQLAlchemy()
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True) # Incremental ID for the user
    name = db.Column(db.String(100), nullable=False) # Name of the user
    password = db.Column(db.String(100), nullable=False) # Password of the user

    @property
    def username(self):
        return self.name

    @username.setter
    def username(self, value):
        self.name = value


class Platform(db.Model):
    __tablename__ = 'platforms'
    id = db.Column(db.Integer, primary_key=True) # Incremental ID for the platform
    name = db.Column(db.String(100), nullable=False) # Name of the platform (e.g., Facebook, WhatsApp)

    # Relationships
    pages = db.relationship('Page', backref='platform', lazy=True, cascade="all, delete-orphan")


# Composite primary key for page_id and platform_id
class Page(db.Model):
    __tablename__ = 'pages'
    __table_args__ = (
        PrimaryKeyConstraint('page_id', 'platform_id'),
    )
    page_id = db.Column(db.String(100), nullable=False) # Page ID used to identify the page (from Facebook Developer)
    token = db.Column(db.Text, nullable=False) # Access token for page permissions (from Facebook Developer)
    platform_id = db.Column(db.Integer, db.ForeignKey('platforms.id'), nullable=False) # Foreign Key linking to Platform
   

    # Relationships
    clients = db.relationship('Client', backref='page', lazy=True, cascade="all, delete-orphan")



class Lead(db.Model):
    __tablename__ = 'leads'
    __table_args__ = (
        PrimaryKeyConstraint('sender_id', 'page_id', 'platform_id'),
        ForeignKeyConstraint(
            ['page_id', 'platform_id'],
            ['pages.page_id', 'pages.platform_id']
        ),
    )
    sender_id = db.Column(db.String(100), nullable=False) # Sender ID received from Facebook or WAHA request
    page_id = db.Column(db.String(100), nullable=False) # Foreign Key linking to Page
    platform_id = db.Column(db.Integer, nullable=False) # Foreign Key linking to Platform
    summary = db.Column(db.Text, nullable=True) # Chat summary (used for agent memory)
    last_bot_reply = db.Column(db.Text, nullable=True) # Last bot reply (used for agent memory)
    chat_history = db.relationship(
        'ChatHistory',
        back_populates='lead',
        uselist=False,
        cascade='all, delete-orphan'
    )

class ChatHistory(db.Model):
    __tablename__ = 'chat_histories'

    __table_args__ = (
        PrimaryKeyConstraint('sender_id', 'page_id', 'platform_id'),
        ForeignKeyConstraint(
            ['sender_id', 'page_id', 'platform_id'],
            ['leads.sender_id', 'leads.page_id', 'leads.platform_id']
        ),
    )

    sender_id = db.Column(db.String(100), nullable=False)
    page_id = db.Column(db.String(100), nullable=False)
    platform_id = db.Column(db.Integer, nullable=False)

    chat_history = db.Column(db.JSON, nullable=False, default=list)

    lead = db.relationship(
        'Lead',
        back_populates='chat_history'
    )
    
class Maintenance(db.Model):
    __tablename__ = 'maintenance'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    project_name = db.Column(db.String(150), nullable=False)

    phone_number = db.Column(db.String(20), nullable=False)    
