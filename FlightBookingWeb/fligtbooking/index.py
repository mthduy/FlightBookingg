import hashlib
import hmac
from datetime import datetime, timedelta

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_login import logout_user, login_user, current_user

import dao
from select import select

from fligtbooking import app,admin,login_manager
from fligtbooking.dao import SanBayNameDAO, search_flights
from fligtbooking.models import Role


@app.route("/")
def home():
    return render_template('index.html')  # Hiển thị trang chủ

# Trang Đặt vé
@app.route('/search', methods=['GET', 'POST'])
def search():
    airports = dao.get_all_airports()

    # Kiểm tra trạng thái đăng nhập (nếu cần)
    if not current_user.is_authenticated:
        return redirect("/login")  # Hoặc điều chỉnh đường dẫn phù hợp

    if request.method == 'POST':
        # Lấy dữ liệu từ form
        from_location = request.form['from_location']
        to_location = request.form['to_location']
        departure_date = request.form['departure_date']
        return_date = request.form.get('return_date')  # get() để tránh lỗi khi không có giá trị
        passengers = request.form['passengers']

        results = search_flights( from_location = from_location,
                                  to_location = to_location,
                                  departure_date = departure_date,
                                  return_date = return_date,
                                  passengers = passengers
                                  )

        from_locationname = SanBayNameDAO.get_airport_name_by_id(from_location)
        to_locationname = SanBayNameDAO.get_airport_name_by_id(to_location)

        # Trả về trang kết quả tìm kiếm
        return render_template('/search_results.html',results=results,from_locationname=from_locationname,to_locationname=to_locationname,departure_date=departure_date)

    # Nếu là GET request, chỉ hiển thị trang tìm kiếm
    return render_template('search.html', airports=airports)


@app.route('/booking/<flight_id>', methods=['GET', 'POST'])
def booking(flight_id):
    # Get flight details based on the flight_id
    flight = dao.get_flight(flight_id)

    seats = []
    if flight:
        # Get all seats for the specific flight (by flight code)
        seats = dao.get_seats_by_maChuyenBay(flight.maChuyenBay)

    if request.method == 'POST':
        # Get form data: passenger's name, email, and selected seat
        name = request.form['name']
        email = request.form['email']
        selected_seat = request.form['selected_seat']

        # Find the price for the selected seat
        price = dao.get_ticket_price_by_seat_number(selected_seat)

        if price is not None:
            # You can then proceed with ticket creation or other processes like payment
            return render_template('payment.html', flight=flight, name=name, email=email, selected_seat=selected_seat, price=price)

        #hiện lỗi
        err_msg = "Ghế bạn chọn không hợp lệ hoặc đã được bán."
        return render_template('booking.html', flight=flight, seats=seats, err_msg=err_msg)

    # Render booking page for GET request
    return render_template('booking.html', flight=flight, seats=seats)


@app.route('/payment/<flight_id>', methods=['POST', 'GET'])
def payment(flight_id):
        price = request.form['price']  # Lấy totalPrice từ form
        return render_template('order.html', price=price)


@app.route("/order/<flight_id>", methods=["POST"])
def order(flight_id):
    # Lấy totalPrice từ form
    price = request.form.get('price')
    redirect_url = "http://127.0.0.1:5000/callback"
    if not price:
        return "Dữ liệu không hợp lệ!", 400  # Nếu không nhận được totalPrice
    # Chuyển tiếp đến ZaloPay để thanh toán
    zalopay_dao = dao.ZaloPayDAO()
    pay_url = zalopay_dao.create_order(price, redirect_url)
    if "Error" not in pay_url:
        # Nếu không có lỗi, chuyển hướng đến trang thanh toán ZaloPay
        return redirect(pay_url)
    else:
        # Nếu có lỗi, hiển thị thông báo lỗi
        return pay_url


# Callback endpoint
@app.route("/callback", methods=["GET", "POST"])
def callback():
    result = request.args  # Lấy các tham số từ URL callback sandbox ZaloPay
    status = result.get("status")

    if status == "1":  # Nếu status = 1, thanh toán thành công
        return redirect(url_for('booking_results'))  # Quay lại trang kết quả của bạn
    else:
        return "Thanh toán không thành công! Vui lòng thử lại."

@app.route("/booking_results")
def booking_results():
    return render_template("booking_results.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect("/")
    err_msg = None
    if request.method.__eq__('POST'):
        email = request.form['email']
        password = request.form.get('password')
        role = request.form.get('role')  # Sử dụng .get() để lấy giá trị từ dropdown
        user = dao.auth_user(email=email, password=password)
        print(user.name + " " + str(user.role))
        if user and role=='customer' and user.role==Role.CUSTOMER:
            login_user(user)
            next_page = request.args.get("next", "/")  # Nếu không có tham số next, chuyển đến trang chủ
            return redirect(next_page)  # Chuyển đến trang yêu cầu sau khi đăng nhập thành công
        elif user and role=='employee' and user.role==Role.EMPLOYEE:
            login_user(user)
            return redirect("/employee")
        else:
            err_msg = "Tài khoản hoặc mật khẩu không đúng!"

    return render_template('login.html', err_msg=err_msg)


@app.route('/login-admin', methods=['post'])
def process_login_admin():
    email = request.form.get('email')
    password = request.form.get('password')
    user = dao.auth_user(email=email, password=password)
    if user and user.role==Role.ADMIN:
        login_user(user)
    else:
        err_msg = "Tài khoản hoặc mật khẩu không đúng!"

    return redirect('/admin')

@login_manager.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id=user_id)

@app.route('/register', methods=["get", "post"])
def register():
    err_msg = None
    if request.method.__eq__('POST'):
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        if password.__eq__(confirm):
            ava_path = None
            name = request.form.get('name')
            email = request.form.get('email')
            # avatar = request.files.get('avatar')
            # if avatar:
            #     res = cloudinary.uploader.upload(avatar)
            #     ava_path = res['secure_url']
            dao.add_user(name=name,email=email, password=password, avatar=ava_path)
            return redirect('/login')
        else:
            err_msg = "Mật khẩu không khớp!"
    return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')  # Quay về trang chủ sau khi đăng xuất


@app.route("/employee")
def employee():
    return render_template('employee/employee.html')

@app.route('/employee_sell_ticket', methods=['GET', 'POST'])
def employee_sell_ticket():
    err_msg = None
    seats = dao.get_all_seats()
    if request.method == 'POST':
        # Lấy dữ liệu từ form
        ma_chuyen_bay = request.form.get('flight')
        name = request.form.get('name')
        soCMND = request.form.get('id_card')
        soDienThoai = request.form.get('phone')
        price = int(request.form.get('price'))
        selected_seat = request.form.get('seat_selected')  # Lấy ghế đã chọn từ form

        try:
            # Tạo vé
            ticket = dao.create_ticket(ma_chuyen_bay, name, soCMND, soDienThoai, price, selected_seat)
            dao.update_seat_status(selected_seat, 'sold')
            return render_template('employee/employee_sell_ticket_result.html', ticket=ticket)
        except Exception as e:
            print(f"Error creating ticket: {e}")
            err_msg = "Lỗi không thể in vé"
            return redirect(url_for('employee_sell_ticket', err_msg=err_msg))

        # Hiển thị danh sách chuyến bay
    flights = dao.get_all_flights()
    return render_template('employee/employee_sell_ticket.html', flights=flights, seats=seats,err_msg=request.args.get('err_msg'))


@app.route('/api/seats')
def get_seats():
    maChuyenBay = request.args.get('maChuyenBay')  # Lấy ID chuyến bay từ query parameter
    seats = dao.get_seats_by_maChuyenBay(maChuyenBay)  # Lấy danh sách ghế của chuyến bay

    # Chuyển đổi dữ liệu thành dạng JSON để gửi về frontend
    seat_data = [
        {
            'seat_number': seat.seat_number,
            'status': seat.status,
            'price': seat.ticketType.giaTien  # Lấy giá vé từ loại ghế
        }
        for seat in seats
    ]
    return jsonify(seat_data)


@app.route('/employee_flight_search')
def employee_flight_search():
    return render_template('employee/employee_flight_search.html')


@app.route('/employee_schedule_flight', methods=['GET', 'POST'])
def employee_schedule_flight():
    # Lấy danh sách các sân bay
    airports = dao.get_all_airports()

    if not airports:
        return render_template('employee/employee_schedule_flight.html', airports=airports,
                               message="Không có sân bay nào trong hệ thống!")
    # Nếu phương thức là POST, xử lý dữ liệu từ form
    if request.method == 'POST':
        # Lấy dữ liệu từ form
        flight_id = request.form.get("flight_id")
        departure_airport_id = int(request.form.get("departure_airport"))
        arrival_airport_id = int(request.form.get("arrival_airport"))
        flight_time = datetime.strptime(request.form.get("flight_time"), "%Y-%m-%dT%H:%M")

        # Chuyển đổi thời gian bay (dạng chuỗi "hh:mm" thành timedelta)
        flight_duration_str = request.form.get("flight_duration")
        flight_duration = timedelta(hours=int(flight_duration_str.split(":")[0]),
                                    minutes=int(flight_duration_str.split(":")[1]))
        first_class_seats = int(request.form.get("first_class_seats"))
        second_class_seats = int(request.form.get("second_class_seats"))
        first_class_price = int(request.form.get("first_class_price"))
        second_class_price = int(request.form.get("second_class_price"))


        # Gọi hàm thêm lịch bay
        dao.add_flight_schedule(flight_id, departure_airport_id, arrival_airport_id,
                            flight_time, flight_duration, first_class_seats, second_class_seats, first_class_price,second_class_price)

        # Thông báo thành công và render lại trang
        return render_template('employee/employee_schedule_flight.html', airports=airports,
                               message="Lập lịch chuyến bay thành công!")

    # Nếu là GET, chỉ cần render lại form với danh sách sân bay
    return render_template('employee/employee_schedule_flight.html', airports=airports)


# @app.route('/admin')
# def admin():
#     if session.get("role") != "admin":
#         return redirect(url_for("login"))
#     return render_template('admin/admin.html')

@app.route('/admin_manage_employees')
def admin_manage_employees():
    return render_template('admin/admin_manage_employees.html')

@app.route('/admin_report_statistics')
def admin_report_statistics():
    return render_template('admin_report_statistics.html')

@app.route('/admin_change_regulations')
def admin_change_regulations():
    return render_template('admin_change_regulations.html')

@app.route('/admin_manage_flights')
def admin_manage_flights():
    return render_template('admin_manage_flights.html')

@app.route('/admin_manage_routes')
def admin_manage_routes():
    return render_template('admin_manage_routes.html')

if __name__ == "__main__":
    with app.app_context():
        app.run(debug=True)
