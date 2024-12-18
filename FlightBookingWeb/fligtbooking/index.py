from flask import Flask, render_template, request, redirect, url_for, session
from dao import get_all_airports
from select import select


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Đảm bảo key này không thay đổi mỗi lần chạy

@app.route("/")
def home():
    return render_template('index.html')  # Hiển thị trang chủ

# Trang Đặt vé
@app.route('/search', methods=['GET', 'POST'])
def search():
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

        # Giả lập kết quả tìm kiếm chuyến bay
        flights = [
            {'flight': 'VN123', 'time': '10:00 AM', 'price': '1,000,000 VND'},
            {'flight': 'VN456', 'time': '2:00 PM', 'price': '1,200,000 VND'},
        ]

        # Trả về trang kết quả tìm kiếm
        return render_template(
            'search_results.html',
            flights=flights,
            departure=from_location,
            destination=to_location,
            date=departure_date,
            return_date=return_date,
            passengers=passengers
        )

    # Nếu là GET request, chỉ hiển thị trang tìm kiếm
    return render_template('search.html')

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
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role')  # Sử dụng .get() để lấy giá trị từ dropdown

        # Kiểm tra nếu vai trò không được chọn
        if not role:
            return render_template('login.html', error="Vui lòng chọn vai trò")

        # Kiểm tra thông tin đăng nhập và vai trò
        if email == 'admin@gmail.com' and password == '123' and role == 'admin':
            session['user_logged_in'] = True
            session['role'] = 'admin'  # Lưu vai trò vào session
            next_page = request.args.get("next", url_for("home"))  # Nếu không có tham số next, chuyển đến trang chủ
            return redirect("admin")  # Chuyển đến trang yêu cầu sau khi đăng nhập thành công

        elif email == 'customer@gmail.com' and password == '123' and role == 'customer':
            session['user_logged_in'] = True
            session['role'] = 'customer'
            next_page = request.args.get("next", url_for("home"))  # Nếu không có tham số next, chuyển đến trang chủ
            return redirect(next_page)  # Chuyển đến trang yêu cầu sau khi đăng nhập thành công

        elif email == 'employee@gmail.com' and password == '123' and role == 'employee':
            session['user_logged_in'] = True
            session['role'] = 'employee'
            # next_page = request.args.get("next", url_for("home"))  # Nếu không có tham số next, chuyển đến trang chủ
            return redirect(url_for("employee"))

        else:
            return render_template('login.html', error="Tên đăng nhập, mật khẩu hoặc vai trò không đúng")

        # Nếu là GET request, chỉ hiển thị form login
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_logged_in', None)
    session.pop('role', None)
    return redirect(url_for('home'))  # Quay về trang chủ sau khi đăng xuất

@app.route("/employee")
def employee():
    if session.get("role") != "employee":
        return redirect(url_for("login"))
    return render_template('employee.html')

@app.route('/employee_sell_ticket')
def employee_sell_ticket():
    return render_template('employee_sell_ticket.html')

@app.route('/employee_flight_search')
def employee_flight_search():
    return render_template('employee_flight_search.html')

@app.route('/employee_schedule_flight')
def employee_schedule_flight():
    with app.app_context():
        airports = get_all_airports()
    return render_template('employee_schedule_flight.html', airports=airports)

@app.route('/admin')
def admin():
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    return render_template('admin.html')

@app.route('/admin_manage_employees')
def admin_manage_employees():
    return render_template('admin_manage_employees.html')

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
