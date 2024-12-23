import hashlib
import json

from fligtbooking.models import TuyenBay, SanBay, ChuyenBay, User
from fligtbooking import db, app

#Code lấy sân bay để hiển thị
def get_all_airports():
    with app.app_context():  # Đảm bảo chạy trong app context
        return SanBay.query.all()

#Code lấy tên sân bay từ id
class SanBayNameDAO:
    @staticmethod
    def get_airport_name_by_id(airport_id):
        return db.session.query(SanBay.tenSanBay).filter(SanBay.id == airport_id).scalar()

def get_flight(flight_id):
    flight = ChuyenBay.query.filter_by(id=flight_id).first()
    if flight:
        return flight
    else:
        return None


#Code thêm chuyến bay , tuyến bay vào database ở Lập lịch
def add_flight_schedule(flight_id, departure_airport_id, arrival_airport_id,
                        flight_time, flight_duration, first_class_seats, second_class_seats, price):
    # Tạo đối tượng TuyenBay mới
    tuyen_bay = TuyenBay(
        maTuyenBay=flight_id,
        sanBayDi_id=departure_airport_id,
        sanBayDen_id=arrival_airport_id,
        soChuyenBay=1  # Giả sử số chuyến bay ban đầu là 1
    )
    db.session.add(tuyen_bay)
    db.session.commit()
    # Tạo đối tượng ChuyenBay (Chuyến bay)
    chuyen_bay = ChuyenBay(
        maChuyenBay=flight_id,
        thoiGianKhoiHanh=flight_time,
        thoiGianDen=flight_time+flight_duration,
        thoiGianBay=flight_duration,
        soGheHang1=first_class_seats,
        soGheHang2=second_class_seats,
        giaTien=price,
        tuyenBay_id=tuyen_bay.id
    )
    db.session.add(chuyen_bay)
    db.session.commit()


#Code tìm kiêm chuyeens bay
def search_flights(from_location=None, to_location=None, departure_date=None, return_date=None, passengers=None):
    query = db.session.query(ChuyenBay).join(TuyenBay)
    # Lọc theo sân bay đi
    if from_location:
        query = query.filter(TuyenBay.sanBayDi_id == from_location)
    # Lọc theo sân bay đến
    if to_location:
        query = query.filter(TuyenBay.sanBayDen_id == to_location)
    # Lọc theo ngày khởi hành
    if departure_date:
        query = query.filter(db.func.date(ChuyenBay.thoiGianKhoiHanh) == departure_date)
    # Lọc theo ngày trở về (nếu có)
    if return_date:
        query = query.filter(db.func.date(ChuyenBay.thoiGianDen) <= return_date)
    # Lọc theo số lượng hành khách (nếu có)
    if passengers:
        query = query.filter(
            (ChuyenBay.soGheHang1 + ChuyenBay.soGheHang2) >= passengers
        )
    # Sắp xếp theo thời gian khởi hành
    return query.order_by(ChuyenBay.thoiGianKhoiHanh).all()

def auth_user(email, password):
    with app.app_context():  # Đảm bảo chạy trong app context
        password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
        user = User.query.filter(User.email == email.strip(), User.password == password).first()
        return user

def get_user_by_id(user_id):
    return User.query.get(user_id)

def add_user(name, email, password, avatar):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    u = User(name=name, email=email, password=password, avatar=avatar)
    db.session.add(u)
    db.session.commit()


#ZALO PAY
import hashlib
import hmac
import time
import requests

class ZaloPayDAO:
    def __init__(self):
        self.app_id = '2553'  # ID của ứng dụng ZaloPay
        self.key1 = 'PcY4iZIKFCIdgZvA6ueMcMHHUbRLYjPL'  # Khóa bí mật của ứng dụng
        self.callback_url = 'http://127.0.0.1:5000/callback'  # URL callback
        self.bank_code = 'zalopayapp'  # Mã ngân hàng (ZaloPay App)

    def create_order(self, amount, redirect_url):
        # Dữ liệu đơn hàng
        app_user = 'ZaloPayDemo'  # Tên người dùng ứng dụng
        app_time = str(int(time.time() * 1000))  # Thời gian hiện tại
        app_trans_id = f'220817_{app_time}'  # ID giao dịch duy nhất
        embed_data = json.dumps({'redirecturl': redirect_url})
        item = '[]'  # Danh sách các sản phẩm (ở đây là chuỗi rỗng)
        description = f'ZaloPayDemo - Thanh toán cho đơn hàng #{app_trans_id}'

        # Cấu trúc dữ liệu gửi đến ZaloPay
        data = f"{self.app_id}|{app_trans_id}|{app_user}|{amount}|{app_time}|{embed_data}|{item}"
        mac = hmac.new(self.key1.encode(), data.encode(), hashlib.sha256).hexdigest()  # Tính toán mã xác thực

        # Thông tin yêu cầu gửi đến API ZaloPay
        params = {
            "app_id": self.app_id,
            "app_user": app_user,
            "app_time": app_time,
            "amount": amount,
            "app_trans_id": app_trans_id,
            "bank_code": self.bank_code,
            "embed_data": embed_data,
            "item": item,
            "callback_url": self.callback_url,
            "description": description,
            "mac": mac  # Mã xác thực
        }

        # Gửi yêu cầu đến API ZaloPay
        try:
            response = requests.post("https://sb-openapi.zalopay.vn/v2/create", data=params)
            response.raise_for_status()  # Kiểm tra mã trạng thái HTTP

            result = response.json()

            # In ra toàn bộ phản hồi để xem chi tiết
            print("ZaloPay Response:", result)

            # Kiểm tra nếu trả về thành công và có khóa order_url
            if result.get("return_code") == 1 and "order_url" in result:
                return result["order_url"]  # Trả về URL thanh toán
            else:
                return f"Error: {result.get('return_message', 'No return message')}"
        except requests.exceptions.RequestException as e:
            return f"Error in request to ZaloPay API: {str(e)}"
        except ValueError:
            return "Error: Invalid JSON response from ZaloPay"
