from fligtbooking.models import TuyenBay, SanBay, ChuyenBay
from fligtbooking import db, app

def get_all_airports():
    with app.app_context():  # Đảm bảo chạy trong app context
        return SanBay.query.all()


def add_flight_schedule(flight_id, departure_airport_id, arrival_airport_id,
                        flight_time, flight_duration, first_class_seats, second_class_seats):
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
        tuyenBay_id=tuyen_bay.id
    )

    db.session.add(chuyen_bay)
    db.session.commit()
