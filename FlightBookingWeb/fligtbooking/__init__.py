from urllib.parse import quote

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import cloudinary

app = Flask(__name__)

app.secret_key = "^&$$%$$FGGFAHGA"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:%s@localhost/flightbooking?charset=utf8mb4" % quote('Admin@123')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["PAGE_SIZE"] = 8


cloudinary.config(cloud_name='ddskv3qix',
                  api_key='237429289958929',
                  api_secret='72Fe5rWNVv0_3E8fAHa9lvZ2zGk')
login_manager = LoginManager(app=app)
# Khởi tạo SQLAlchemy
db = SQLAlchemy(app)
