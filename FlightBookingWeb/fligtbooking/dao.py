from models import Airport
from fligtbooking import db, app

def get_all_airports():
    with app.app_context():  # Đảm bảo chạy trong app context
        return Airport.query.all()
