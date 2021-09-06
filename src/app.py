import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, 'cfb_data.db')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
