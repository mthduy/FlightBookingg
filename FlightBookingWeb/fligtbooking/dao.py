from fligtbooking.models import TuyenBay, SanBay, ChuyenBay
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
