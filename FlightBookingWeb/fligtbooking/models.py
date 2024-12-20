from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Time
from sqlalchemy.orm import relationship
import datetime
from fligtbooking import db, app


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
    soChuyenBay = Column(Integer, nullable=False)  # Số chuyến bay

    # Mối quan hệ
    sanBayDi = relationship("SanBay", foreign_keys=[sanBayDi_id])  # Mối quan hệ với sân bay đi
    sanBayDen = relationship("SanBay", foreign_keys=[sanBayDen_id])  # Mối quan hệ với sân bay đến
    chuyenBays = relationship("ChuyenBay", backref="tuyenBay_relationship")  # Đổi tên backref


# Chuyến bay
class ChuyenBay(db.Model):
    __tablename__ = 'chuyenbay'  # Khai báo tên bảng cho Chuyến Bay
    id = Column(Integer, primary_key=True, autoincrement=True)
    maChuyenBay = Column(String(50), unique=True, nullable=False)  # Mã chuyến bay
    thoiGianKhoiHanh = Column(DateTime, nullable=False)  # Thời gian khởi hành
    thoiGianDen = Column(DateTime, nullable=False)  # Thời gian đến
    thoiGianBay = Column(Time, nullable=False)  # Thời gian bay
    soGheHang1 = Column(Integer, nullable=False)  # Số ghế hạng 1
    soGheHang2 = Column(Integer, nullable=False)  # Số ghế hạng 2
    giaTien = Column(Integer,nullable=False)
    # Tham chiếu đến bảng TuyenBay
    tuyenBay_id = Column(Integer, ForeignKey('tuyenbay.id'), nullable=False)
    # Mối quan hệ
    tuyenBay = relationship("TuyenBay", foreign_keys=[tuyenBay_id])  # Liên kết với bảng TuyenBay
    # Reverse relationship with SanBayTrungGian
    sanBayTrungGians = relationship("SanBayTrungGian", back_populates="chuyenBay")


# Sân bay trung gian
class SanBayTrungGian(db.Model):
    __tablename__ = 'sanbaytrunggian'
    id = Column(Integer, primary_key=True, autoincrement=True)
    chuyenBay_id = Column(Integer, ForeignKey('chuyenbay.id'), nullable=False)
    sanBay_id = Column(Integer, ForeignKey('sanbay.id'), nullable=True)
    thoiGianDung = Column(Integer, nullable=True)  # Thời gian dừng
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
    giaVe = Column(Integer, nullable=False)

    # Mối quan hệ với bảng HanhKhach
    hanhKhach = relationship('HanhKhach', backref='veMayBays')
    # Mối quan hệ với bảng ChuyenBay
    chuyenBay = relationship('ChuyenBay', backref='veMayBays')


# Bảng Hành Khách
class HanhKhach(db.Model):
    __tablename__ = 'hanhkhach'
    id = Column(Integer, primary_key=True, autoincrement=True)
    hanhKhach_id = Column(String(50), nullable=False)
    tenHanhKhach = Column(String(50), nullable=False)
    soCMND = Column(Integer, nullable=False)
    soDienThoai = Column(Integer, nullable=False)


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

        db.session.commit()
