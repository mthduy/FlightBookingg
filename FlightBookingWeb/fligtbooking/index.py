import hashlib
import hmac
from datetime import datetime, timedelta

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_login import logout_user, login_user, current_user

import dao
from select import select

from fligtbooking import app,admin,login_manager
from fligtbooking.dao import SanBayNameDAO, customter_search_flights
from fligtbooking.models import Role, Regulation


@app.route("/")
def home():
    if current_user.is_authenticated and current_user.role==Role.EMPLOYEE:
        return redirect("/employee")
    elif current_user.is_authenticated and current_user.role==Role.ADMIN:
        return redirect("/logout")
    return render_template('index.html')  # Hiển thị trang chủ

# Trang Đặt vé
@app.route('/search', methods=['GET', 'POST'])
def search():
    airports = dao.get_all_airports()

    # Kiểm tra trạng thái đăng nhập (nếu cần)
    if not current_user.is_authenticated:
        return redirect("/login")  # Hoặc điều chỉnh đường dẫn phù hợp

    booking_time=dao.get_current_regulation()
    booking_time_limit=booking_time.customer_booking_time

    if request.method == 'POST':
        # Lấy dữ liệu từ form
        from_location = request.form['from_location']
        to_location = request.form['to_location']
        departure_date = request.form['departure_date']
        return_date = request.form.get('return_date')  # get() để tránh lỗi khi không có giá trị
        passengers = request.form['passengers']



        results = customter_search_flights( from_location = from_location,
                                  to_location = to_location,
                                  departure_date = departure_date,
                                  return_date = return_date,
                                  passengers = passengers
                                  )

        current_time = datetime.now()

        from_locationname = SanBayNameDAO.get_airport_name_by_id(from_location)
        to_locationname = SanBayNameDAO.get_airport_name_by_id(to_location)

        # Trả về trang kết quả tìm kiếm
        return render_template('/search_results.html',results=results,
                                                                        from_locationname=from_locationname,
                                                                        to_locationname=to_locationname,
                                                                        departure_date=departure_date,
                                                                        current_time=current_time,
                                                                        booking_time_limit=booking_time_limit,
                                                                        timedelta=timedelta )

    # Nếu là GET request, chỉ hiển thị trang tìm kiếm
    return render_template('search.html', airports=airports)



@app.route('/booking/<flight_id>', methods=['GET', 'POST'])
def booking(flight_id):
    # Get flight details based on the flight_id
    flight = dao.get_flight(flight_id)

    seats = []
    if flight:
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
    if current_user.is_authenticated and current_user.role==Role.CUSTOMER:
        return redirect("/")
    elif current_user.is_authenticated and current_user.role==Role.EMPLOYEE:
        return redirect("/employee")
    err_msg = None
    if request.method.__eq__('POST'):
        email = request.form['email']
        password = request.form.get('password')
        role = request.form.get('role')  # Sử dụng .get() để lấy giá trị từ dropdown
        user = dao.auth_user(email=email, password=password)
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

        regulation = dao.get_current_regulation()
        employee_sale_time = regulation.employee_sale_time
        flight = dao.get_chuyenbay_by_maChuyenBay(ma_chuyen_bay)
        thoiGianKhoiHanh = flight.thoiGianKhoiHanh

        sale_deadline = thoiGianKhoiHanh - timedelta(hours=employee_sale_time)
        current_time = datetime.now()
        # Kiểm tra thời gian bán vé
        if current_time > sale_deadline:
            err_msg = f"Nhân viên chỉ được phép bán vé trước {employee_sale_time} giờ."
            return render_template('employee/employee_sell_ticket.html',
                                   flights=dao.get_all_flights(),
                                   seats=seats,
                                   err_msg=err_msg)

        try:
            # Tạo vé
            ticket = dao.create_ticket(ma_chuyen_bay, name, soCMND, soDienThoai, price, selected_seat)
            dao.update_seat_status(selected_seat, 'sold',ma_chuyen_bay)
            ghe= dao.get_seat_by_number_maChuyenBay(selected_seat, ma_chuyen_bay)
            return render_template('employee/employee_sell_ticket_result.html', ticket=ticket,ghe=ghe)
        except Exception as e:
            print(f"Error creating ticket: {e}")
            err_msg = "Lỗi không thể in vé"

    # Hiển thị danh sách chuyến bay
    flights = dao.get_all_flights()
    return render_template('employee/employee_sell_ticket.html', flights=flights, seats=seats, err_msg=err_msg)

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


@app.route('/employee_flight_search',methods=['GET','POST'])
def employee_flight_search():
        if request.method == 'POST':
            maChuyenBay = request.form.get("maChuyenBay")
            flight = dao.employee_search_flights_by_maChuyenBay(maChuyenBay)
            airport = dao.get_TuyenBay_by_maChuyenBay(maChuyenBay)
            seats = dao.count_available_seats(maChuyenBay)

            sanbaydi_name = SanBayNameDAO.get_airport_name_by_id(airport.sanBayDi_id)
            sanbayden_name = SanBayNameDAO.get_airport_name_by_id(airport.sanBayDen_id)

            return render_template('employee/employee_flight_search_result.html',flight=flight,sanbaydi_name=sanbaydi_name,sanbayden_name=sanbayden_name,seats=seats)

        return render_template('employee/employee_flight_search.html')


# @app.route('/employee_flight_search_result')
# def employee_flight_search_result():
#     return render_template('employee/employee_flight_search_result.html')


@app.route('/employee_schedule_flight', methods=['GET', 'POST'])
def employee_schedule_flight():
    # Lấy danh sách các sân bay
    airports = dao.get_all_airports()
    regulation = Regulation.query.first()

    # Parse ticket_classes thành danh sách'
    raw_ticket_classes = eval(regulation.ticket_classes) if regulation.ticket_classes else []

    # Số lượng sân bay trung gian tối đa
    max_intermediate_airports = regulation.max_intermediate_airports

    # Thêm chỉ số index cho từng loại vé
    ticket_classes = [
        {"index": idx + 1, "class_name": item["class_name"].strip(), "price": item["price"]}
        for idx, item in enumerate(raw_ticket_classes)
    ]

    if request.method == 'POST':
        # Lấy dữ liệu từ form
        flight_id = request.form.get("flight_id")
        departure_airport_id = int(request.form.get("departure_airport"))
        arrival_airport_id = int(request.form.get("arrival_airport"))
        flight_time = datetime.strptime(request.form.get("flight_time"), "%Y-%m-%dT%H:%M")
        flight_duration = timedelta(
            hours=int(request.form.get("flight_duration").split(":")[0]),
            minutes=int(request.form.get("flight_duration").split(":")[1])
        )

        # Lấy thông tin sân bay trung gian
        intermediate_airports = []
        for i in range(max_intermediate_airports):
            airport_id = request.form.get(f"intermediate_airports[{i}][id]")
            stop_time = request.form.get(f"intermediate_airports[{i}][stop_time]")
            if airport_id and stop_time:
                intermediate_airports.append({
                    "airport_id": int(airport_id),
                    "stop_time": stop_time
                })

        # Lấy thông tin ghế và giá tiền
        seats_info = []
        for ticket_class in ticket_classes:
            seats = int(request.form.get(f"class_{ticket_class['index']}_seats"))
            price = int(request.form.get(f"class_{ticket_class['index']}_price"))
            seats_info.append({
                "class_name": ticket_class["class_name"],
                "price": price,
                "seats": seats
            })

        # Gọi hàm thêm lịch bay và truyền tất cả các thông tin vào, bao gồm seats_info
        dao.add_flight_schedule(flight_id, departure_airport_id, arrival_airport_id, flight_time,
                                flight_duration, intermediate_airports, seats_info)

        return render_template('employee/employee_schedule_flight.html', airports=airports,
                               ticket_classes=ticket_classes, max_intermediate_airports=max_intermediate_airports,
                               message="Lập lịch chuyến bay thành công!")

    return render_template('employee/employee_schedule_flight.html', airports=airports,
                           ticket_classes=ticket_classes, max_intermediate_airports=max_intermediate_airports)




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
