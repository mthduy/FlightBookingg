import enum
import json
import math

from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Time, Boolean, event, update
from sqlalchemy.orm import relationship
import datetime
from fligtbooking import db, app

class HangGhe(enum.Enum):
    HANG_1 = 'Hạng 1'
    HANG_2 = 'Hạng 2'
    HANG_3 = 'Hạng 3'
    HANG_4 = 'Hạng 4'
    def __str__(self):
        return self.value


# Sân bay
class SanBay(db.Model):
    __tablename__ = 'sanbay'
    id = Column(Integer, primary_key=True, autoincrement=True)
    maSanBay = Column(String(10), unique=True, nullable=False)  # Mã sân bay
    tenSanBay = Column(String(100), nullable=False)  # Tên sân bay
    viTri = Column(String(100), nullable=True)  # Vị trí

    def __str__(self):
        return self.tenSanBay


# Tuyến bay
class TuyenBay(db.Model):
    __tablename__ = 'tuyenbay'  # Khai báo tên bảng cho Tuyến Bay
    id = Column(Integer, primary_key=True, autoincrement=True)
    maTuyenBay = Column(String(50), unique=True, nullable=False)  # Mã tuyến bay
    sanBayDi_id = Column(Integer, ForeignKey('sanbay.id'), nullable=False)  # Sân bay đi
    sanBayDen_id = Column(Integer, ForeignKey('sanbay.id'), nullable=False)  # Sân bay đến



    # Mối quan hệ
    sanBayDi = relationship("SanBay", foreign_keys=[sanBayDi_id])  # Mối quan hệ với sân bay đi
    sanBayDen = relationship("SanBay", foreign_keys=[sanBayDen_id])  # Mối quan hệ với sân bay đến
    chuyenBays = relationship("ChuyenBay", back_populates="tuyenBay", cascade="all, delete")  # Đổi tên backref




class ChuyenBay(db.Model):
    __tablename__ = 'chuyenbay'  # Khai báo tên bảng cho Chuyến Bay
    id = Column(Integer, primary_key=True, autoincrement=True)  # Khóa chính, tự động tăng
    maChuyenBay = Column(String(50), unique=True, nullable=False)  # Mã chuyến bay
    thoiGianKhoiHanh = Column(DateTime, nullable=False)  # Thời gian khởi hành
    thoiGianDen = Column(DateTime, nullable=False)  # Thời gian đến
    thoiGianBay = Column(Time, nullable=False)  # Thời gian bay

    # Tham chiếu đến bảng TuyenBay
    tuyenBay_id = Column(Integer, ForeignKey('tuyenbay.id'), nullable=False)
    # Mối quan hệ với bảng TuyenBay (Tuyến bay)
    tuyenBay = relationship("TuyenBay", foreign_keys=[tuyenBay_id], back_populates="chuyenBays")  # Liên kết với bảng TuyenBay
    # Mối quan hệ với bảng Seat (Ghế ngồi) - Chuyến bay có nhiều ghế
    seats = relationship("Seat", back_populates="chuyenBay", cascade="all, delete")  # Liên kết với bảng ghế ngồi
    # Mối quan hệ với bảng TicketType (Loại vé) - Một chuyến bay có nhiều loại vé
    ticket_types = relationship("TicketType", back_populates="chuyenBay", cascade="all, delete")  # Liên kết với bảng loại vé
    # Mối quan hệ với bảng SanBayTrungGian (Sân bay trung gian) - Chuyến bay có thể có nhiều sân bay trung gian
    sanBayTrungGians = relationship("SanBayTrungGian", back_populates="chuyenBay", cascade="all, delete")
    veMayBays = relationship('VeMayBay', back_populates='chuyenBay', cascade='all, delete')



    # Phương thức chuyển thời gian bay thành chuỗi (giờ:phút:giây)
    def get_thoiGianBay_str(self):
        if self.thoiGianBay:
            return self.thoiGianBay.strftime("%H:%M:%S")  # Chuyển Time thành chuỗi
        return "00:00:00"  # Trả về chuỗi mặc định nếu không có thời gian bay

    def get_thoiGianBay_hours(self):
        if self.thoiGianBay:
            total_hours = self.thoiGianBay.hour + self.thoiGianBay.minute / 60 + self.thoiGianBay.second / 3600
            return math.ceil(total_hours)
        return 0



class TicketType(db.Model):
    __tablename__ = 'ticket_type'  # Khai báo tên bảng cho loại vé
    id = Column(Integer, primary_key=True, autoincrement=True)  # Khóa chính, tự động tăng
    name = Column(String(50), nullable=False)  # Tên loại vé (ví dụ: Hạng 1, Hạng 2)
    giaTien = Column(Integer, nullable=False)  # Giá vé cho loại vé này

    # Tham chiếu đến bảng ChuyenBay (Chuyến bay)
    chuyenbay_id = Column(Integer, ForeignKey('chuyenbay.id'), nullable=False)
    # Mối quan hệ với bảng ChuyenBay (Chuyến bay)
    chuyenBay = relationship("ChuyenBay", foreign_keys=[chuyenbay_id], back_populates="ticket_types")


class Seat(db.Model):
    __tablename__ = 'seat'  # Khai báo tên bảng cho ghế ngồi
    id = Column(Integer, primary_key=True, autoincrement=True)  # Khóa chính, tự động tăng
    seat_number = Column(String(10), nullable=False)  # Số ghế (ví dụ: 1A, 2B, v.v.)
    status = Column(String(20), nullable=False, default='available')  # Trạng thái của ghế: "available" hoặc "sold"
    # Store the Enum value as a string, not the Enum member
    hang_ghe = Column(db.String(50), nullable=False, default=HangGhe.HANG_2.value)  # Store the actual value

    # Tham chiếu đến bảng ChuyenBay (Chuyến bay)
    chuyenbay_id = Column(Integer, ForeignKey('chuyenbay.id'), nullable=False)
    # Tham chiếu đến bảng TicketType (Loại vé)
    ticket_type_id = Column(Integer, ForeignKey('ticket_type.id'), nullable=False)
    # Mối quan hệ với bảng ChuyenBay (Chuyến bay)
    chuyenBay = relationship("ChuyenBay", foreign_keys=[chuyenbay_id], back_populates="seats")
    # Mối quan hệ với bảng TicketType (Loại vé)
    ticketType = relationship("TicketType", foreign_keys=[ticket_type_id])
    #Lấy maChuyenBay trong ChuyenBay
    @property
    def maChuyenBay(self):
        return self.chuyenBay.maChuyenBay

# Sân bay trung gian
class SanBayTrungGian(db.Model):
    __tablename__ = 'sanbaytrunggian'
    id = Column(Integer, primary_key=True, autoincrement=True)
    chuyenBay_id = Column(Integer, ForeignKey('chuyenbay.id'), nullable=False)
    sanBay_id = Column(Integer, ForeignKey('sanbay.id'), nullable=True)
    thoiGianDung = Column(Time, nullable=True)  # Thời gian dừng
    ghiChu = Column(String(200), nullable=True)  # Ghi chú

    # Mối quan hệ
    chuyenBay = relationship("ChuyenBay", back_populates="sanBayTrungGians")
    sanBay = relationship("SanBay")



# Bảng Vé Máy Bay
class VeMayBay(db.Model):
    __tablename__ = 'vemaybay'
    id = Column(Integer, primary_key=True, autoincrement=True)
    veMayBay_id = Column(String(50), nullable=False)
    hanhKhach_id = Column(Integer, ForeignKey('hanhkhach.id'), nullable=False)  # Khóa ngoại đến bảng HanhKhach
    chuyenBay_id = Column(Integer, ForeignKey('chuyenbay.id'), nullable=False)  # Khóa ngoại đến bảng ChuyenBay
    email = Column(String(50), nullable=False)
    giaVe = Column(Integer, nullable=False)
    seat_number = Column(String(50), nullable=False)

    # Mối quan hệ với bảng HanhKhach
    hanhKhach = relationship('HanhKhach', backref='veMayBays')
    # Mối quan hệ với bảng ChuyenBay
    # chuyenBay = relationship('ChuyenBay', backref='veMayBays',cascade="all, delete")
    chuyenBay = relationship('ChuyenBay', back_populates='veMayBays')


# Bảng Hành Khách
class HanhKhach(db.Model):
    __tablename__ = 'hanhkhach'
    id = Column(Integer, primary_key=True, autoincrement=True)
    hanhKhach_id = Column(String(50), nullable=False,unique=True)
    tenHanhKhach = Column(String(50), nullable=False)
    soCMND = Column(String(20), nullable=False)
    soDienThoai = Column(String(20), nullable=False)
    email = Column(String(50), nullable=False,unique=True)

    # Thêm khóa ngoại liên kết với bảng User
    user_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    user = relationship('User', back_populates='hanhkhach')

    @staticmethod
    def generate_hanhKhach_id(tenHanhKhach, id):
        return tenHanhKhach[:3].upper() + str(id)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.hanhKhach_id:
            self.hanhKhach_id = "TEMP"  # Giá trị tạm thời

@event.listens_for(HanhKhach, 'after_insert')
def after_insert_listener(mapper, connection, target):
    # Tạo giá trị hanhKhach_id
    hanhKhach_id = HanhKhach.generate_hanhKhach_id(target.tenHanhKhach, target.id)
    # Sử dụng SQLAlchemy để cập nhật giá trị
    stmt = update(HanhKhach).where(HanhKhach.id == target.id).values(hanhKhach_id=hanhKhach_id)
    connection.execute(stmt)


class Role(enum.Enum):
    EMPLOYEE = 'Nhân viên'
    ADMIN = 'Quản lý'
    CUSTOMER = 'Khách hàng'


class User(db.Model,UserMixin):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = Column(String(50), nullable=False)
    active = Column(Boolean, default=True)
    avatar = Column(String(200),default="https://res.cloudinary.com/dq5ajyj0q/image/upload/v1735387922/1077114_aohjw8.png")
    role = db.Column(db.Enum(Role), nullable=False, default=Role.CUSTOMER)

    hanhkhach = relationship('HanhKhach', back_populates='user', uselist=False,
                             primaryjoin="and_(HanhKhach.email == User.email, HanhKhach.user_id == User.id)")
    def __str__(self):
        return f"{self.name} - {self.role.value}"

class Regulation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    airport_count = db.Column(db.Integer, nullable=False, default=10)
    min_flight_time = db.Column(db.Integer, nullable=False, default=30)
    max_intermediate_airports = db.Column(db.Integer, nullable=False, default=2)
    min_stop_time = db.Column(db.Integer, nullable=False, default=20)
    max_stop_time = db.Column(db.Integer, nullable=False, default=30)
    customer_booking_time = db.Column(db.Integer, nullable=False, default=12)
    employee_sale_time = db.Column(db.Integer, nullable=False, default=4)
    ticket_class_count = db.Column(db.Integer, nullable=False, default=2)
    ticket_classes = db.Column(db.String(500),nullable=False, default=json.dumps([
        {"class_name": "1", "price": 1500000, "count": 6},
        {"class_name": "2", "price": 1000000, "count": 12}
    ]))


# class TmpCustomerInfo(db.Model):
#     __tablename__ = 'tmp_customer_info'
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     apptransid = Column(db.String(500), nullable=False)
#     name = db.Column(db.String(50),nullable=False)
#     email = db.Column(db.String(50),nullable=False)
#     soDienThoai = db.Column(Integer,nullable=False)
#     soCMND = db.Column(Integer, nullable=False)
#     gheDaChon = db.Column()
#     maChuyenBay = db.Column(db.String(50),nullable=False)
#

# Tạo cơ sở dữ liệu và thêm sân bay mặc định
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # Dữ liệu sân bay mặc định
        danhSachSanBay = [
            {"maSanBay": "HAN", "tenSanBay": "Sân bay Nội Bài", "viTri": "Hà Nội"},
            {"maSanBay": "SGN", "tenSanBay": "Sân bay Tân Sơn Nhất", "viTri": "TP.HCM"},
            {"maSanBay": "DAD", "tenSanBay": "Sân bay Đà Nẵng", "viTri": "Đà Nẵng"},
            {"maSanBay": "HPH", "tenSanBay": "Sân bay Cát Bi", "viTri": "Hải Phòng"},
            {"maSanBay": "VCL", "tenSanBay": "Sân bay Chu Lai", "viTri": "Quảng Nam"},
            {"maSanBay": "PXU", "tenSanBay": "Sân bay Pleiku", "viTri": "Gia Lai"},
            {"maSanBay": "UIH", "tenSanBay": "Sân bay Phù Cát", "viTri": "Bình Định"},
            {"maSanBay": "VII", "tenSanBay": "Sân bay Vinh", "viTri": "Nghệ An"},
            {"maSanBay": "CXR", "tenSanBay": "Sân bay Cam Ranh", "viTri": "Khánh Hòa"},
            {"maSanBay": "VCS", "tenSanBay": "Sân bay Côn Đảo", "viTri": "Bà Rịa - Vũng Tàu"}
        ]
        for sanBay in danhSachSanBay:
            db.session.add(SanBay(maSanBay=sanBay["maSanBay"], tenSanBay=sanBay["tenSanBay"], viTri=sanBay["viTri"]))

        import hashlib

        password = str(hashlib.md5("123".encode('utf-8')).hexdigest())
        u = User(name="CUSTOMER", email="customer@gmail.com", password=password)
        u1 = User(name="EMPLOYEE", email="employee@gmail.com", password=password,role=Role.EMPLOYEE)
        u2 = User(name="ADMIN", email="admin@gmail.com", password=password, role=Role.ADMIN)
        db.session.add(u)
        db.session.add(u1)
        db.session.add(u2)

        if Regulation.query.first() is None:
            default_regulation = Regulation()
            db.session.add(default_regulation)

        db.session.commit()