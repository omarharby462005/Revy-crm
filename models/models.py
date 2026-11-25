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

    page_id = db.Column(db.String(100), nullable=False)
    token = db.Column(db.Text, nullable=False)

    platform_id = db.Column(
        db.Integer,
        db.ForeignKey('platforms.id'),
        nullable=False
    )

    # Relationships
    clients = db.relationship(
        'Client',
        backref='page',
        lazy=True,
        cascade="all, delete-orphan"
    )




class Client(db.Model):
    __tablename__ = 'clients'

    __table_args__ = (
        PrimaryKeyConstraint(
            'sender_id', 'page_id', 'platform_id'
        ),
        ForeignKeyConstraint(
            ['page_id', 'platform_id'],
            ['pages.page_id', 'pages.platform_id']
        ),
    )

    sender_id = db.Column(db.String(100), nullable=False)
    page_id = db.Column(db.String(100), nullable=False)
    platform_id = db.Column(db.Integer, nullable=False)

    summary = db.Column(db.Text, nullable=True)
    last_bot_reply = db.Column(db.Text, nullable=True)

    # Relationships
    chat_history = db.relationship(
        'ChatHistory',
        back_populates='client',
        uselist=False,
        cascade='all, delete-orphan'
    )


class ChatHistory(db.Model):
    __tablename__ = 'chat_histories'

    __table_args__ = (
        PrimaryKeyConstraint(
            'sender_id', 'page_id', 'platform_id'
        ),
        ForeignKeyConstraint(
            ['sender_id', 'page_id', 'platform_id'],
            ['clients.sender_id',
             'clients.page_id',
             'clients.platform_id']
        ),
    )

    sender_id = db.Column(db.String(100), nullable=False)
    page_id = db.Column(db.String(100), nullable=False)
    platform_id = db.Column(db.Integer, nullable=False)

    chat_history = db.Column(
        db.JSON,
        nullable=False,
        default=list
    )

    # Relationships
    client = db.relationship(
        'Client',
        back_populates='chat_history'
    )

    
class Maintenance(db.Model):
    __tablename__ = 'maintenance'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    project_name = db.Column(db.String(150), nullable=False)

    phone_number = db.Column(db.String(20), nullable=False)    
