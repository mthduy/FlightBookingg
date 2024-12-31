import hashlib
import json
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy.orm import aliased

from fligtbooking.models import TuyenBay, SanBay, ChuyenBay, User, Seat, HangGhe, TicketType, HanhKhach, VeMayBay, \
    Regulation, SanBayTrungGian
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

# Convert flight_time (hh:mm:ss) to total minutes
def get_flight_duration_in_minutes(flight_time):
    try:
        flight_time_obj = datetime.strptime(flight_time, "%H:%M:%S")
        total_minutes = flight_time_obj.hour * 60 + flight_time_obj.minute
        return total_minutes
    except Exception as e:
        return 0

def show_all_flights():
    # Truy vấn lấy thông tin chuyến bay và chỉ lấy ID sân bay đi, sân bay đến
    flights = db.session.query(
        ChuyenBay.id,
        ChuyenBay.maChuyenBay,  # Mã chuyến bay
        ChuyenBay.thoiGianKhoiHanh,  # Thời gian khởi hành
        ChuyenBay.thoiGianDen,  # Thời gian đến
        TuyenBay.maTuyenBay,  # Mã tuyến bay
        TuyenBay.sanBayDi_id,  # ID sân bay đi
        TuyenBay.sanBayDen_id  # ID sân bay đến
    ).join(
        TuyenBay, ChuyenBay.tuyenBay_id == TuyenBay.id
    ).all()

    return flights



def add_flight_schedule(flight_id, departure_airport_id, arrival_airport_id, flight_time, flight_duration, intermediate_airports, seats_info):
    # Create the flight route
    tuyen_bay = TuyenBay(
        maTuyenBay=flight_id,
        sanBayDi_id=departure_airport_id,
        sanBayDen_id=arrival_airport_id,
    )
    db.session.add(tuyen_bay)
    db.session.commit()

    # Create the flight instance
    chuyen_bay = ChuyenBay(
        maChuyenBay=flight_id,
        thoiGianKhoiHanh=flight_time,
        thoiGianDen=flight_time + flight_duration,
        thoiGianBay=flight_duration,
        tuyenBay_id=tuyen_bay.id
    )
    db.session.add(chuyen_bay)
    db.session.commit()

    # Add intermediate airports (if any)
    for intermediate_airport in intermediate_airports:
        intermediate_stop = SanBayTrungGian(
            chuyenBay_id=chuyen_bay.id,
            sanBay_id=intermediate_airport["airport_id"],
            thoiGianDung=intermediate_airport["stop_time"]
        )
        db.session.add(intermediate_stop)
    db.session.commit()

    # Initialize row counter for all classes
    current_row = 1

    # Create ticket types and seats for each class
    for seat in seats_info:
        ticket_type = TicketType(
            name=seat["class_name"],
            giaTien=seat["price"],
            chuyenbay_id=chuyen_bay.id
        )
        db.session.add(ticket_type)
        db.session.commit()

        seat_letters = ["A", "B", "C", "D", "E", "F"]
        seats_remaining = seat["seats"]

        class_name_mapping = {
            "1": HangGhe.HANG_1,
            "2": HangGhe.HANG_2,
            "3": HangGhe.HANG_3,
            "4": HangGhe.HANG_4,
        }

        # Dynamically determine the hang_ghe based on the class_name
        hang_ghe = class_name_mapping.get(seat["class_name"], None)

        if hang_ghe is None:
            raise ValueError(f"Invalid ticket class: {seat['class_name']}")

        while seats_remaining > 0:
            for letter in seat_letters:
                if seats_remaining == 0:
                    break
                seat_number = f"{current_row}{letter}"
                seat_instance = Seat(
                    seat_number=seat_number,
                    status="available",  # Default status
                    hang_ghe=hang_ghe.value,  # Store the actual value (e.g., 'Hạng 1')
                    chuyenbay_id=chuyen_bay.id,
                    ticket_type_id=ticket_type.id
                )
                db.session.add(seat_instance)
                seats_remaining -= 1
            current_row += 1  # Move to the next row

        db.session.commit()



from sqlalchemy import func

def customter_search_flights(from_location=None, to_location=None, departure_date=None, return_date=None, passengers=None):
    query = db.session.query(
        ChuyenBay,
        func.min(TicketType.giaTien).label('min_price'),  # Giá vé thấp nhất cho chuyến bay
        func.max(TicketType.giaTien).label('max_price')   # Giá vé cao nhất (nếu cần)
    ).join(TuyenBay).join(TicketType)

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
        # Đếm số ghế khả dụng theo chuyến bay
        available_seats = db.session.query(
            Seat.chuyenbay_id,
            func.count(Seat.id).label('available_seat_count')
        ).filter(
            Seat.status == 'available'  # Lọc ghế còn trống
        ).group_by(
            Seat.chuyenbay_id
        ).subquery()  # Tạo truy vấn phụ

        # Tham chiếu truy vấn phụ trong truy vấn chính
        query = query.join(
            available_seats, ChuyenBay.id == available_seats.c.chuyenbay_id
        ).filter(
            available_seats.c.available_seat_count >= passengers  # Kiểm tra số ghế đủ yêu cầu
        )

    # Nhóm theo chuyến bay để tổng hợp giá tiền
    query = query.group_by(ChuyenBay.id).order_by(ChuyenBay.thoiGianKhoiHanh)

    return query.all()


def employee_search_flights_by_maChuyenBay_thoiGianBay(maChuyenBay=None, thoiGianKhoiHanh=None):
    query = db.session.query(ChuyenBay)
    if maChuyenBay:
        query = query.filter(ChuyenBay.maChuyenBay == maChuyenBay)
    if thoiGianKhoiHanh:
        query = query.filter(ChuyenBay.thoiGianKhoiHanh==thoiGianKhoiHanh)
    return query.all()


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

# def get_tmp_customer_info(apptransid):
#     return TmpCustomerInfo.query.filter_by(apptransid=apptransid).first()
#
# def save_tmp_customer_info(apptransid, name, email,soDienThoai,soCMND,selected_seat, maChuyenBay):
#     tmp_customer_info = TmpCustomerInfo(
#         apptransid=apptransid,
#         name=name,
#         email=email,
#         soDienThoai=soDienThoai,
#         soCMND=soCMND,
#         selected_seat=selected_seat,
#         maChuyenBay=maChuyenBay,
#     )
#     db.session.add(tmp_customer_info)
#     db.session.commit()

def  generate_apptransid():
    app_time = str(int(time.time() * 1000))
    app_trans_id = f'220817_{app_time}'
    return app_trans_id

class ZaloPayDAO:
    def __init__(self):
        self.app_id = '2553'  # ID của ứng dụng ZaloPay
        self.key1 = 'PcY4iZIKFCIdgZvA6ueMcMHHUbRLYjPL'  # Khóa bí mật của ứng dụng
        self.callback_url = 'http://127.0.0.1:5000/callback'  # URL callback
        self.bank_code = 'zalopayapp'  # Mã ngân hàng (ZaloPay App)

    def create_order(self, amount, redirect_url, app_trans_id=None):
        # Dữ liệu đơn hàng
        app_user = 'ZaloPayDemo'  # Tên người dùng ứng dụng
        app_time = str(int(time.time() * 1000))  # Thời gian hiện tại
        app_trans_id =app_trans_id # ID giao dịch duy nhất
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

def get_all_flights():
    return ChuyenBay.query.all()


def create_ticket(ma_chuyen_bay, tenHanhKhach, soCMND, soDienThoai, email, price, selected_seat):
    try:
        chuyen_bay = ChuyenBay.query.filter_by(maChuyenBay=ma_chuyen_bay).first()
        if not chuyen_bay:
            raise ValueError("Chuyến bay không tồn tại")

        existing_hanh_khach = HanhKhach.query.filter_by(email=email).first()

        if existing_hanh_khach:
            if (existing_hanh_khach.tenHanhKhach != tenHanhKhach or
                existing_hanh_khach.soCMND != soCMND or
                existing_hanh_khach.soDienThoai != soDienThoai):
                raise ValueError("Email đã đăng ký với thông tin khác")

            hanh_khach = existing_hanh_khach
        else:
            hanh_khach = HanhKhach(
                tenHanhKhach=tenHanhKhach,
                soCMND=soCMND,
                soDienThoai=soDienThoai,
                email=email
            )
            db.session.add(hanh_khach)
            db.session.flush()  

        ticket_id = f"MB{hanh_khach.id:06d}-{chuyen_bay.id}-{selected_seat}"
        ticket = VeMayBay(
            veMayBay_id=ticket_id,
            hanhKhach_id=hanh_khach.id,
            chuyenBay_id=chuyen_bay.id,
            email=email,
            giaVe=price,
            seat_number=selected_seat
        )
        db.session.add(ticket)
        db.session.commit()

        return ticket, None

    except Exception as e:
        db.session.rollback()
        print(f"Error occurred: {e}")
        err_msg = "Có lỗi xảy ra, email đã được đăng kí với thông tin khác"
        return None, err_msg



def get_seat_by_number_maChuyenBay(seat_number,ma_chuyen_bay):
    return Seat.query.join(ChuyenBay).filter(
        Seat.seat_number == seat_number,
        ChuyenBay.maChuyenBay == ma_chuyen_bay
    ).first()


def update_seat_status(seat_number, status,ma_chuyen_bay):
    seat = get_seat_by_number_maChuyenBay(seat_number,ma_chuyen_bay)
    if seat:
        seat.status = status
        db.session.commit()


def get_all_seats():
    return Seat.query.all()



def get_seats_by_maChuyenBay(maChuyenBay):
    # Lấy tất cả các ghế ngồi của chuyến bay có maChuyenBay
    return db.session.query(Seat).join(ChuyenBay).filter(ChuyenBay.maChuyenBay == maChuyenBay).all()


def count_available_seats(maChuyenBay):
    return db.session.query(Seat).join(ChuyenBay).filter(
        ChuyenBay.maChuyenBay == maChuyenBay,
        Seat.status == 'available'
    ).count()



def get_TuyenBay_by_maChuyenBay(maChuyenBay):
    return db.session.query(TuyenBay).filter(ChuyenBay.maChuyenBay == maChuyenBay).first()

def get_current_regulation():
    return Regulation.query.first()

def get_chuyenbay_by_maChuyenBay(ma_chuyen_bay):
    return ChuyenBay.query.filter_by(maChuyenBay=ma_chuyen_bay).first()

def get_thoiGianBay_by_maChuyenBay(ma_chuyen_bay):
    # Fetch the entire ChuyenBay object
    return  ChuyenBay.query.filter_by(maChuyenBay=ma_chuyen_bay).first()


# email
def send_email(to_email, customer_info):
    subject = "Xác Nhận Đặt Chuyến Bay"
    body = f"""
    Chào {customer_info['name']},
    
    Chúng tôi xin thông báo rằng bạn đã mua vé máy bay thành công.
    Thông tin chuyến bay:
    - Mã chuyến bay: {customer_info['maChuyenBay']}
    - Ghế đã chọn: {customer_info['selected_seat']}
    - Tổng giá vé: {customer_info['total_price']} VND
    - Số điện thoại: {customer_info['soDienThoai']}
    - Email: {customer_info['email']}

    Chúng tôi sẽ liên hệ với bạn qua email hoặc số điện thoại nếu có bất kỳ thay đổi nào.

    Cảm ơn bạn đã sử dụng dịch vụ của chúng tôi!
    Trân trọng,
    """
    from_email = 'nguyenlethanhthang@gmail.com'
    password = 'rudd yixj kljq ismb'  # Thay bằng mật khẩu ứng dụng mới
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        print('Email đã được gửi thành công!')
    except Exception as e:
        print(f'Có lỗi xảy ra: {e}')

def check_email_exists(email):
    return User.query.filter_by(email=email).first() is not None

