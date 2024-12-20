from datetime import datetime, timedelta

from flask import Flask, render_template, request, redirect, url_for, session
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

    # Kiểm tra trạng thái đăng nhập
    if 'user_logged_in' not in session or session['user_logged_in'] != True:
        return redirect(url_for('login'))  # Nếu chưa đăng nhập, chuyển đến trang đăng nhập

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

        from_locationName = SanBayNameDAO.get_airport_name_by_id(from_location)
        to_locationName = SanBayNameDAO.get_airport_name_by_id(to_location)


        # Trả về trang kết quả tìm kiếm
        return render_template('search_results.html',results=results,from_locationName=from_locationName,to_locationName=to_locationName,departure_date=departure_date)

    # Nếu là GET request, chỉ hiển thị trang tìm kiếm
    return render_template('search.html', airports=airports)

@app.route('/booking/<flight_id>', methods=['GET', 'POST'])
def booking(flight_id):
    # Giả lập dữ liệu chuyến bay (thực tế có thể lấy từ cơ sở dữ liệu)
    flights = [
        {'flight': 'VN123', 'time': '10:00 AM', 'price': '1,000,000 VND'},
        {'flight': 'VN456', 'time': '2:00 PM', 'price': '1,200,000 VND'},
    ]

    # Lấy thông tin chuyến bay theo flight_id
    flight = next(f for f in flights if f['flight'] == flight_id)

    if request.method == 'POST':
        # Xử lý dữ liệu khi người dùng gửi form (lấy thông tin từ form)
        name = request.form['name']
        email = request.form['email']
        passengers = request.form['passengers']

        # Giả lập việc lưu thông tin đặt vé hoặc gửi email xác nhận
        return render_template('booking_results.html', flight=flight, name=name, email=email, passengers=passengers)

    # Hiển thị trang đặt vé
    return render_template('booking.html', flight=flight)


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

@app.route('/employee_sell_ticket')
def employee_sell_ticket():
    return render_template('employee/employee_sell_ticket.html')

@app.route('/employee_flight_search')
def employee_flight_search():
    return render_template('employee/employee_flight_search.html')


@app.route('/employee_schedule_flight', methods=['GET', 'POST'])
def employee_schedule_flight():
    # Lấy danh sách các sân bay
    airports = dao.get_all_airports()

    if not airports:
        return render_template('employee_schedule_flight.html', airports=airports,
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
        price = int(request.form.get("price"))
        # Gọi hàm thêm lịch bay
        dao.add_flight_schedule(flight_id, departure_airport_id, arrival_airport_id,
                            flight_time, flight_duration, first_class_seats, second_class_seats, price)
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
