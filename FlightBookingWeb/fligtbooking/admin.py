from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from fligtbooking import app, db

# Cấu hình Admin trang home
admin = Admin(app=app, name="Flight Booking", template_mode="bootstrap4")



# View tùy chỉnh để quản lý nhân viên
class AdminManageEmployeeView(BaseView):
    @expose('/')
    def index(self):
        # Render file template admin_manage_employees.html từ thư mục admin
        return self.render('admin/admin_manage_employees.html')

# View tùy chỉnh để thay đổi quy định
class AdminChangeRegulationsView(BaseView):
    @expose('/')
    def index(self):
        # Render file template admin/change_regulations.html từ thư mục admin
        return self.render('admin/admin_change_regulations.html')

class AdminManagerFlightsView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/admin_manage_flights.html')

class AdminManagerRoutesView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/admin_manage_routes.html')

class AdminReportStatisticsView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/admin_report_statistics.html')

# Thêm View vào Flask-Admim
admin.add_view(AdminChangeRegulationsView(name="Change Regulations", endpoint="admin_change_regulations"))
admin.add_view(AdminManageEmployeeView(name="Manage Employees", endpoint="admin_manage_employees"))
admin.add_view(AdminManagerFlightsView(name="Manage Flights",endpoint="admin_manager_flights"))
admin.add_view(AdminManagerRoutesView(name="Manage Routes", endpoint="admin_manager_routes"))
admin.add_view(AdminReportStatisticsView(name="Report Statistics", endpoint="admin_report_statistics"))

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