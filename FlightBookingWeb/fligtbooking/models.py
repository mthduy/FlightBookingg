from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Time
from sqlalchemy.orm import relationship
import datetime

from fligtbooking import db, app


class Airport(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    location = Column(String(100), nullable=True)

    def __str__(self):
        self.name



class FlightTicket(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    flightCode = Column(String(50), unique=True, nullable=False)  # Mã chuyến bay
    departureTime = Column(DateTime, nullable=False)  # Thời gian khởi hành
    arrivalTime = Column(DateTime, nullable=False)  # Thời gian đến
    flightTime = Column(Time, nullable=False)  # Thời gian bay
    numClass1Seat = Column(Integer, nullable=False)  # Số ghế hạng 1
    numClass2Seat = Column(Integer, nullable=False)  # Số ghế hạng 2

    # Tham chiếu đến bảng Airport
    departureAirport_id = Column(Integer, ForeignKey('airport.id'), nullable=False)
    arrivalAirport_id = Column(Integer, ForeignKey('airport.id'), nullable=False)

    # Relationships
    departureAirport = relationship("Airport", foreign_keys=[departureAirport_id])
    arrivalAirport = relationship("Airport", foreign_keys=[arrivalAirport_id])
    intermediateAirports = relationship("IntermediateAirport", back_populates="flight")

class IntermediateAirport(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    flight_id = Column(Integer, ForeignKey('flight_ticket.id'), nullable=False)
    airport_id = Column(Integer, ForeignKey('airport.id'), nullable=True)
    stopTime = Column(Integer, nullable=True)
    note = Column(String(200), nullable=True)

    # Relationships
    flight = relationship("FlightTicket", back_populates="intermediateAirports")
    airport = relationship("Airport")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        # Thêm dữ liệu sân bay mặc định
        airports = [
            {"code": "HAN", "name": "Sân bay Nội Bài", "location": "Hà Nội"},
            {"code": "SGN", "name": "Sân bay Tân Sơn Nhất", "location": "TP.HCM"},
            {"code": "DAD", "name": "Sân bay Đà Nẵng", "location": "Đà Nẵng"},
            {"code": "HPH", "name": "Sân bay Cát Bi", "location": "Hải Phòng"},
            {"code": "VCL", "name": "Sân bay Chu Lai", "location": "Quảng Nam"},
            {"code": "PXU", "name": "Sân bay Pleiku", "location": "Gia Lai"},
            {"code": "UIH", "name": "Sân bay Phù Cát", "location": "Bình Định"},
            {"code": "VII", "name": "Sân bay Vinh", "location": "Nghệ An"},
            {"code": "CXR", "name": "Sân bay Cam Ranh", "location": "Khánh Hòa"},
            {"code": "VCS", "name": "Sân bay Côn Đảo", "location": "Bà Rịa - Vũng Tàu"}
        ]
        for airport in airports:
            db.session.add(Airport(code=airport["code"], name=airport["name"], location=airport["location"]))

        db.session.commit()