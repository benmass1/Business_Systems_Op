
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'funguo-ya-siri-ya-masanja'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///../data/business.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
