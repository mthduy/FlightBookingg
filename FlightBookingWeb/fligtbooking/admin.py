import json

from flask import redirect, request
from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user

from fligtbooking import app, db
from fligtbooking.models import Role, Regulation

# Cấu hình Admin trang home
admin = Admin(app=app, name="Flight Booking", template_mode="bootstrap4")


class MyBaseView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == Role.ADMIN

class AdminChangeRegulationsView(MyBaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):

        regulation = Regulation.query.first()
        if request.method == 'POST':
            # Lấy dữ liệu từ form
            airport_count = int(request.form.get('airport-count'))
            min_flight_time = int(request.form.get('min-flight-time'))
            max_intermediate_airports = int(request.form.get('max-intermediate-airports'))
            min_stop_time = int(request.form.get('min-stop-time'))
            max_stop_time = int(request.form.get('max-stop-time'))
            customer_booking_time = int(request.form.get('customer-booking-time'))
            employee_sale_time = int(request.form.get('employee-sale-time'))
            ticket_class_count = int(request.form.get('ticket-class-count'))
            ticket_classes = []
            for i in range(1, ticket_class_count + 1):
                class_name = request.form.get(f'class-{i}')
                price = int(request.form.get(f'price-{i}'))
                ticket_classes.append({"class_name": class_name, "price": price})
            ticket_classes_json = json.dumps(ticket_classes)
            ticket_sale_time = int(request.form.get('ticket-sale-time'))
            ticket_booking_time = int(request.form.get('ticket-booking-time'))

            # Cập nhật hoặc tạo quy định mới
            regulation = Regulation.query.first()
            if regulation:
                regulation.airport_count = airport_count
                regulation.min_flight_time = min_flight_time
                regulation.max_intermediate_airports = max_intermediate_airports
                regulation.min_stop_time = min_stop_time
                regulation.max_stop_time = max_stop_time
                regulation.customer_booking_time = customer_booking_time
                regulation.employee_sale_time = employee_sale_time
                regulation.ticket_class_count = ticket_class_count
                regulation.ticket_classes = ticket_classes_json
                regulation.ticket_sale_time = ticket_sale_time
                regulation.ticket_booking_time = ticket_booking_time
                db.session.commit()
            else:
                pass

            return redirect('/admin/admin_change_regulations')

        return self.render('admin/admin_change_regulations.html', regulation=regulation)


# View tùy chỉnh để quản lý nhân viên
class AdminManageEmployeeView(MyBaseView):
    @expose('/')
    def index(self):
        # Render file template admin_manage_employees.html từ thư mục admin
        return self.render('admin/admin_manage_employees.html')


class AdminManagerFlightsView(MyBaseView):
    @expose('/')
    def index(self):
        return self.render('admin/admin_manage_flights.html')

class AdminManagerRoutesView(MyBaseView):
    @expose('/')
    def index(self):
        return self.render('admin/admin_manage_routes.html')

class AdminReportStatisticsView(MyBaseView):
    @expose('/')
    def index(self):
        return self.render('admin/admin_report_statistics.html')


# class StatsView(MyBaseView):
#     @expose('/')
#     def index(self):
#         return self.render('admin/stats.html')


class LogoutView(MyBaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/admin')

# Thêm View vào Flask-Admim
admin.add_view(AdminChangeRegulationsView(name="Thay đổi quy định", endpoint="admin_change_regulations"))
admin.add_view(AdminManageEmployeeView(name="Quản lý nhân viên", endpoint="admin_manage_employees"))
admin.add_view(AdminManagerFlightsView(name="Quản lý chuyến bay",endpoint="admin_manager_flights"))
admin.add_view(AdminManagerRoutesView(name="Quản lý tuyến bay", endpoint="admin_manager_routes"))
admin.add_view(AdminReportStatisticsView(name="Thống kê báo cáo", endpoint="admin_report_statistics"))
admin.add_view(LogoutView(name="Đăng xuất"))

# #CHO NHAN VIEN
# class EmployeeFlightSearchView(BaseView):
#     @expose('/')
#     def index(self):
#         # Render file template admin_manage_employees.html từ thư mục admin
#         return self.render('employee/employee_flight_search.html')
#
# class EmployeeScheduleFlightView(BaseView):
#     @expose('/')
#     def index(self):
#         # Render file template admin_manage_employees.html từ thư mục admin
#         return self.render('employee/employee_schedule_flight.html')
#
# class EmployeeSellTicketView(BaseView):
#     @expose('/')
#     def index(self):
#         return self.render('employee/employee_sell_ticket.html')
#
# admin.add_view(EmployeeFlightSearchView(name="Flight Search",endpoint="employee_flight_search"))
# admin.add_view(EmployeeScheduleFlightView(name="Flight Schedule",endpoint="employee_schedule_flight"))
# admin.add_view(EmployeeSellTicketView(name="Sell Ticket",endpoint="employee_sell_ticket"))