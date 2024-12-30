import hashlib
import hmac

from datetime import datetime, timedelta

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_login import logout_user, login_user, current_user
from sqlalchemy.testing.util import total_size
from wtforms.validators import email
import cloudinary.uploader
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

#hiển thị toàn bộ chuyến bay
@app.route('/show_all_flights', methods=['GET', 'POST'])
def show_all_flights():
    flights = dao.show_all_flights()
    booking_time = dao.get_current_regulation()
    booking_time_limit = booking_time.customer_booking_time
    current_time = datetime.now()

    from_locationname = None  # Khởi tạo ngoài vòng lặp để tránh lỗi khi không có chuyến bay
    to_locationname = None

    if flights:  # Kiểm tra nếu có chuyến bay

        for flight in flights:
            from_locationname=(SanBayNameDAO.get_airport_name_by_id(flight.sanBayDi_id))
            to_locationname=(SanBayNameDAO.get_airport_name_by_id(flight.sanBayDen_id))

    # Trả về trang với các giá trị cần thiết, bao gồm việc kiểm tra nếu không có chuyến bay
    return render_template("show_all_flights.html", flights=flights,
                           from_locationname=from_locationname,
                           to_locationname=to_locationname,
                           booking_time_limit=booking_time_limit,
                           current_time=current_time,
                           timedelta=timedelta)


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
    # total_minutes = flight.get_thoiGianBay_minutes()
    total_minutes = flight.get_thoiGianBay_hours()
    if flight:
        seats = dao.get_seats_by_maChuyenBay(flight.maChuyenBay)
        print(f"Tổng phút bay: {total_minutes}")  # Debug lo

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        selected_seat = request.form['selected_seat']
        soDienThoai = request.form['soDienThoai']
        soCMND = request.form['soCMND']
        # Ensure price is converted to float
        price = int(request.form['price'])

        total_price=price*total_minutes

        if selected_seat not in [seat.seat_number for seat in seats]:
            err_msg = "Ghế bạn chọn không tồn tại hoặc đã được bán."
            return render_template('booking.html', flight=flight, seats=seats, err_msg=err_msg)


        return render_template('payment.html', flight=flight, name=name, email=email,
                                   selected_seat=selected_seat,
                                       soCMND=soCMND, soDienThoai=soDienThoai,total_price=total_price)

    return render_template('booking.html', flight=flight, seats=seats)


@app.route('/payment/<flight_id>', methods=['POST', 'GET'])
def payment(flight_id):
    price = request.form.get('price', '0')
    total_price = request.form.get('total_price')

    # Lấy dữ liệu từ form
    name = request.form.get("name")
    email = request.form.get("email")
    soDienThoai = request.form.get("soDienThoai")
    soCMND = request.form.get("soCMND")
    selected_seat = request.form.get("selected_seat")
    maChuyenBay = request.form.get("maChuyenBay")

    return render_template('order.html', price=price, name=name, email= email,maChuyenBay=maChuyenBay, soDienThoai=soDienThoai, soCMND=soCMND,selected_seat=selected_seat,total_price=total_price)



@app.route("/order/<flight_id>", methods=["POST"])
def order(flight_id):

    apptransid = dao.generate_apptransid()
    price = request.form.get('price')
    total_price = request.form.get('total_price')
    name = request.form.get('name')
    email = request.form.get('email')
    soDienThoai = request.form.get('soDienThoai')
    soCMND = request.form.get('soCMND')
    maChuyenBay = request.form.get('maChuyenBay')
    selected_seat=request.form.get('selected_seat')

    session['customer_info'] = {
        'apptransid': apptransid,
        'name': name,
        'email': email,
        'soDienThoai': soDienThoai,
        'soCMND': soCMND,
        'selected_seat': selected_seat,
        'maChuyenBay': maChuyenBay,
        'price' : price,
        'total_price':total_price
    }
    # dao.save_tmp_customer_info(apptransid,name,email,soDienThoai,soCMND,selected_seat,maChuyenBay,price)

    redirect_url = "http://127.0.0.1:5000/callback"
    if not total_price:
        return "Dữ liệu không hợp lệ!", 400  # Nếu không nhận được totalPrice
    # Chuyển tiếp đến ZaloPay để thanh toán
    zalopay_dao = dao.ZaloPayDAO()
    pay_url = zalopay_dao.create_order(total_price, redirect_url,apptransid)
    if "Error" not in pay_url:
        # Nếu không có lỗi, chuyển hướng đến trang thanh toán ZaloPay
        return redirect(pay_url)
    else:
        # Nếu có lỗi, hiển thị thông báo lỗi
        return pay_url


@app.route("/callback", methods=["GET", "POST"])
def callback():
    result = request.args  # Retrieve parameters from the ZaloPay callback
    status = result.get("status")
    customer_info = session.get('customer_info')

    if status == "1" and customer_info:
        try:

            # Create ticket
            ticket = dao.create_ticket(
                customer_info['maChuyenBay'],
                customer_info['name'],
                customer_info['soCMND'],
                customer_info['soDienThoai'],
                customer_info['email'],
                customer_info['total_price'],
                customer_info['selected_seat']
            )
            # Update seat status to 'sold'
            dao.update_seat_status(
                customer_info['selected_seat'],
                'sold',
                customer_info['maChuyenBay']
            )

            # Redirect to booking results page
            return redirect(url_for('booking_results'))

        except Exception as e:
            # Log the error with a detailed message
            app.logger.error(f"Error during callback processing: {e}")
            return "Error processing your request. Please try again later.", 500

    # Log if payment status is not successful or customer info is missing
    app.logger.warning("Payment failed or invalid callback data.")
    return "Payment failed or invalid callback data.", 400


@app.route("/booking_results")
def booking_results():
    customer_info = session.get('customer_info')
    if customer_info:
        to_email=customer_info['email']
        dao.send_email(to_email, customer_info)
        return render_template('booking_results.html', customer_info=customer_info)
    else:
        return "Thông tin không hợp lệ.", 400


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
    if user and user.role == Role.ADMIN:
        login_user(user)
        return redirect(url_for('admin.index'))  # Redirect đến trang quản trị
    else:
        flash("Tài khoản hoặc mật khẩu không đúng !", "error")  # Thêm thông báo lỗi
        return redirect(url_for('admin.index'))  # Redirect đến trang đăng nhập

@login_manager.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id=user_id)

@app.route('/register', methods=["GET", "POST"])
def register():
    err_msg = None
    if request.method.__eq__('POST'):
        password = request.form.get('password')
        confirm = request.form.get('confirm')
        email = request.form.get('email')
        if password.__eq__(confirm):
            # Kiểm tra email đã tồn tại
            if dao.check_email_exists(email):
                err_msg = "Email đã được đăng ký!"
            else:
                ava_path = None
                name = request.form.get('name')
                avatar = request.files.get('avatar')
                if avatar:
                    res = cloudinary.uploader.upload(avatar)
                    ava_path = res['secure_url']
                dao.add_user(name=name, email=email, password=password, avatar=ava_path)
                return redirect('/login')
        else:
            err_msg = "Mật khẩu không khớp!"
    return render_template('register.html', err_msg=err_msg)


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
    total_price = None  # Khởi tạo total_price mặc định là None

    if request.method == 'POST':
        # Lấy dữ liệu từ form
        ma_chuyen_bay = request.form.get('flight')
        name = request.form.get('name')
        soCMND = request.form.get('id_card')
        soDienThoai = request.form.get('phone')
        email = request.form.get('email')
        price = request.form.get('price')
        selected_seat = request.form.get('seat_selected')  # Lấy ghế đã chọn từ form
        total_price=request.form.get('total_price')
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
                                   err_msg=err_msg,
                                   total_price=total_price)  # Truyền total_price vào template

        try:
            # Tạo vé
            ticket, err_msg = dao.create_ticket(ma_chuyen_bay, name, soCMND, soDienThoai, email, total_price, selected_seat)

            if err_msg:
                return render_template('employee/employee_sell_ticket.html',
                                       flights=dao.get_all_flights(),
                                       seats=seats,
                                       err_msg=err_msg,
                                       total_price=total_price)  # Truyền total_price vào template

            dao.update_seat_status(selected_seat, 'sold', ma_chuyen_bay)
            ghe = dao.get_seat_by_number_maChuyenBay(selected_seat, ma_chuyen_bay)

            # Gửi email xác nhận
            customer_info = {
                'name': name,
                'maChuyenBay': ma_chuyen_bay,
                'selected_seat': selected_seat,
                'total_price': total_price,
                'soDienThoai': soDienThoai,
                'email': email
            }
            dao.send_email(email, customer_info)

            return render_template('employee/employee_sell_ticket_result.html',
                                   ticket=ticket,
                                   ghe=ghe,
                                   total_price=total_price)  # Truyền total_price vào result template

        except Exception as e:
            err_msg = "Lỗi không thể in vé"

    # Hiển thị danh sách chuyến bay
    flights = dao.get_all_flights()

    return render_template('employee/employee_sell_ticket.html',
                           flights=flights,
                           seats=seats,
                           err_msg=err_msg,
                           total_price=total_price)  # Truyền total_price vào template

@app.route('/api/get_flight_duration', methods=['GET'])
def get_flight_duration():
    ma_chuyen_bay = request.args.get('flight')
    if not ma_chuyen_bay:
        return jsonify({'success': False, 'message': 'Mã chuyến bay không hợp lệ'})

    flight = dao.get_thoiGianBay_by_maChuyenBay(ma_chuyen_bay)
    if flight:
        # Kiểm tra và trả về thời gian bay (thoiGianBay) dưới dạng chuỗi
        thoiGianBay = flight.thoiGianBay.strftime('%H:%M:%S')  # Chuyển sang định dạng string
        return jsonify({'success': True, 'thoiGianBay': thoiGianBay})
    else:
        # Trả về thông báo lỗi nếu không tìm thấy chuyến bay
        return jsonify({'success': False, 'message': 'Chuyến bay không tồn tại'})


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
            thoiGianKhoiHanh = request.form.get("search_time_flight")
            flight = dao.employee_search_flights_by_maChuyenBay_thoiGianBay(maChuyenBay,thoiGianKhoiHanh)
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
    min_stop_time = regulation.min_stop_time
    max_stop_time = regulation.max_stop_time
    min_flight_time = regulation.min_flight_time
    # Thêm chỉ số index cho từng loại vé
    ticket_classes = [
        {"index": idx + 1, "class_name": item["class_name"].strip(), "price": item["price"], "count": item["count"]}
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
                               ticket_classes=ticket_classes, max_intermediate_airports=max_intermediate_airports,max_stop_time=max_stop_time,min_stop_time=min_stop_time,min_flight_time=min_flight_time,
                               message="Lập lịch chuyến bay thành công!")

    return render_template('employee/employee_schedule_flight.html', airports=airports,max_stop_time=max_stop_time,min_stop_time=min_stop_time,min_flight_time=min_flight_time,
                           ticket_classes=ticket_classes, max_intermediate_airports=max_intermediate_airports)


if __name__ == "__main__":
    with app.app_context():
        app.run(debug=True)
