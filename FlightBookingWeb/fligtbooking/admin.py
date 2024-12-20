from flask import redirect
from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user

from fligtbooking import app, db
from fligtbooking.models import Role

# Cấu hình Admin trang home
admin = Admin(app=app, name="Flight Booking", template_mode="bootstrap4")


class MyBaseView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == Role.ADMIN


# View tùy chỉnh để quản lý nhân viên
class AdminManageEmployeeView(MyBaseView):
    @expose('/')
    def index(self):
        # Render file template admin_manage_employees.html từ thư mục admin
        return self.render('admin/admin_manage_employees.html')

# View tùy chỉnh để thay đổi quy định
class AdminChangeRegulationsView(MyBaseView):
    @expose('/')
    def index(self):
        # Render file template admin/change_regulations.html từ thư mục admin
        return self.render('admin/admin_change_regulations.html')

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