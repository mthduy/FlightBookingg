import hashlib
import json
from datetime import datetime

from flask import redirect, request, flash, url_for, jsonify, make_response
from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.fields import QuerySelectField
from flask_login import current_user, logout_user
from markupsafe import Markup
from sqlalchemy.orm import aliased
from wtforms.fields.choices import SelectField
from wtforms.fields.simple import StringField
from wtforms.validators import DataRequired
from wtforms.widgets.core import html_params, Select

from fligtbooking import app, db
from fligtbooking.models import Role, Regulation, ChuyenBay, TuyenBay, SanBay, Seat, User, TicketType, VeMayBay

# Cấu hình Admin trang home
admin = Admin(app=app, name="Flight Booking", template_mode="bootstrap4")

class CustomSelectWidget(Select):
    def __call__(self, field, **kwargs):
        kwargs.setdefault("id", field.id)

        if self.multiple:
            kwargs["multiple"] = True

        # Lấy các cờ từ field
        flags = getattr(field, "flags", {})
        for k in dir(flags):
            if k in self.validation_attrs and k not in kwargs:
                kwargs[k] = getattr(flags, k)

        # Thiết lập các tham số HTML cho thẻ <select>
        select_params = html_params(name=field.name, **kwargs)
        html = [f"<select {select_params}>"]

        if field.has_groups():
            for group, choices in field.iter_groups():
                optgroup_params = html_params(label=group)
                html.append(f"<optgroup {optgroup_params}>")
                for choice in choices:
                    if len(choice) == 4:
                        val, label, selected, render_kw = choice
                        html.append(self.render_option(val, label, selected, **render_kw))
                    elif len(choice) == 3:
                        val, label, selected = choice
                        html.append(self.render_option(val, label, selected))
                html.append("</optgroup>")
        else:
            for choice in field.iter_choices():
                if len(choice) == 4:
                    val, label, selected, render_kw = choice
                    html.append(self.render_option(val, label, selected, **render_kw))
                elif len(choice) == 3:
                    val, label, selected = choice
                    html.append(self.render_option(val, label, selected))

        html.append("</select>")
        return Markup("".join(html))

class MyModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == Role.ADMIN

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
                count = int(request.form.get(f'count-{i}'))
                ticket_classes.append({"class_name": class_name, "price": price, "count": count})
            ticket_classes_json = json.dumps(ticket_classes)

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
                db.session.commit()
                flash("Cập nhật thành công", "success")
            else:
                flash("Cập nhật quy định thất bại", "error")

            return redirect('/admin/admin_change_regulations')

        return self.render('admin/admin_change_regulations.html', regulation=regulation)


# View tùy chỉnh để quản lý nhân viên
class AdminManageEmployeeView(MyBaseView):
    @expose('/', methods=['GET'])
    def index(self):
        # Lấy danh sách tất cả nhân viên có vai trò là EMPLOYEE
        query = User.query.filter(User.role == Role.EMPLOYEE.name)
        employees = query.all()

        # Render trang quản lý nhân viên, gửi dữ liệu nhân viên vào template
        return self.render('admin/admin_manage_employees.html', users=employees)

    @expose('/search_employee', methods=['GET'])
    def search_employee(self):
        err_msg = None
        search_name = request.args.get('search_name', '').strip()

        if not search_name:
            err_msg = "Vui lòng nhập tên nhân viên để tìm kiếm."
            flash(err_msg, "error")
            return redirect(url_for('.index'))

        query = User.query.filter(User.role == Role.EMPLOYEE.name)

        try:
            if search_name:
                query = query.filter(User.name.ilike(f'%{search_name}%'))
            employees = query.all()

            if not employees:
                err_msg = "Không tìm thấy nhân viên nào với tên đã nhập."
                flash(err_msg, "error")

        except Exception as e:
            err_msg = f"Đã xảy ra lỗi khi tìm kiếm: {str(e)}"
            flash(err_msg, "error")

        return self.render('admin/admin_manage_employees.html', users=employees)

    @expose('/add_employee', methods=['GET', 'POST'])
    def add_employee(self):
        err_msg = None
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()
            role = request.form.get('role', '').strip()

            if not name or not email or not password or not role:
                err_msg = "Tất cả các trường phải được điền đầy đủ!"
                return self.render('admin/add_employee.html', err_msg=err_msg)

            user_exists = User.query.filter_by(email=email).first()
            if user_exists:
                err_msg = "Email đã tồn tại trong hệ thống!"
                return self.render('admin/add_employee.html', err_msg=err_msg)
                # Kiểm tra vai trò có hợp lệ không
            if role != Role.EMPLOYEE.name:
                err_msg = "Vai trò phải là Nhân Viên!"
                return self.render('admin/add_employee.html', err_msg=err_msg)
            try:
                # Mã hóa mật khẩu
                hashed_password = hashlib.md5(password.encode('utf-8')).hexdigest()

                new_user = User(name=name, email=email, password=hashed_password, role=Role.EMPLOYEE.name)
                db.session.add(new_user)
                db.session.commit()
                flash("Thêm nhân viên thành công!", "success")
                return redirect(url_for('.index'))
            except Exception as e:
                db.session.rollback()
                err_msg = f"Lỗi khi thêm nhân viên: {e}"
                print(f"Lỗi chi tiết: {e}")
                return self.render('admin/add_employee.html', err_msg=err_msg)

        return self.render('admin/add_employee.html', err_msg=err_msg)

    @expose('/delete_employee/<int:id>', methods=['POST'])
    def delete_employee(self, id):
        err_msg = None
        user = User.query.get(id)
        if user:
            try:
                db.session.delete(user)
                db.session.commit()
            except Exception as e:
                db.session.rollback()  # Nếu có lỗi, rollback giao dịch
                err_msg = f"Lỗi khi xóa nhân viên: {e}"
                return self.render('admin/admin_manage_employees.html', err_msg=err_msg)

            return redirect(url_for('.index'))

        err_msg = "Không tìm thấy nhân viên hoặc không thể xóa!"
        return self.render('admin/admin_manage_employees.html', err_msg=err_msg)

    @expose('/edit_employee', methods=['POST'])
    def edit_employee(self):
        err_msg = None
        user_id = request.form.get('id')
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        role = request.form.get('role', '').strip()

        if role != Role.EMPLOYEE.name:
            err_msg = "Vai trò không hợp lệ!"
            return self.render('admin/admin_manage_employees.html', err_msg=err_msg)

        user = User.query.get(user_id)
        if user:
            try:
                user.name = name
                user.email = email
                user.role = Role.EMPLOYEE.name
                db.session.commit()
                return redirect(url_for('.index'))
            except Exception as e:
                db.session.rollback()  # Nếu có lỗi, rollback giao dịch
                err_msg = f"Lỗi khi sửa thông tin nhân viên: {e}"
                return self.render('admin/admin_manage_employees.html', err_msg=err_msg)

        err_msg = "Không tìm thấy nhân viên!"
        return self.render('admin/admin_manage_employees.html', err_msg=err_msg)

class AdminManagerFlightsView(MyModelView):
    column_labels = {
        'id': 'ID Chuyến Bay',
        'maChuyenBay': 'Mã Chuyến Bay',
        'thoiGianKhoiHanh': 'Thời Gian Khởi Hành',
        'thoiGianDen': 'Thời Gian Đến',
        'thoiGianBay': 'Thời Gian Bay',
        'tuyenBay_id': 'ID Tuyến Bay ',
        'tuyenBay.maTuyenBay':'Mã Tuyến Bay'
    }
    column_formatters = {
        'tuyenBay_id': lambda v, c, m, p: m.tuyenBay.maTuyenBay
    }
    column_list = ["maChuyenBay", "thoiGianKhoiHanh", "thoiGianDen", "thoiGianBay", "tuyenBay_id"]
    column_searchable_list = ["id", "maChuyenBay","tuyenBay.maTuyenBay","thoiGianDen", "thoiGianBay"]
    column_filters = ["id", "maChuyenBay","tuyenBay.maTuyenBay","thoiGianDen", "thoiGianBay"]
    can_export = True

    form_extra_fields = {
        'maChuyenBay': StringField('Mã chuyến bay', validators=[DataRequired()]),

        'tuyenBay_id': QuerySelectField(
            'Tuyến bay',
            query_factory=lambda: TuyenBay.query.all(),
            get_label='maTuyenBay',
            allow_blank=False,
            widget=CustomSelectWidget()
        )
    }

    def on_model_change(self, form, model, is_created):
        if form.tuyenBay_id.data:
            model.tuyenBay_id = form.tuyenBay_id.data.id

        if is_created:
            regulation = Regulation.query.first()
            if regulation and regulation.ticket_classes:
                ticket_classes = json.loads(regulation.ticket_classes)
            else:
                ticket_classes = []

            for ticket_class in ticket_classes:
                seats = ticket_class['count']
                hang_ghe = ticket_class['class_name']
                hang_ghe_format = f"Hạng {ticket_class['class_name']}"

                row = 1
                seat_letters = ['A', 'B', 'C', 'D', 'E', 'F']
                for seat_number in range(1, seats + 1):
                    seat_letter = seat_letters[(seat_number - 1) % len(seat_letters)]
                    seat_number_str = f"{row}{seat_letter}"

                    if seat_letter == 'F':
                        row += 1

                    seat = Seat(
                        seat_number=seat_number_str,
                        status="available",
                        hang_ghe=hang_ghe_format,
                        chuyenbay_id=model.id,
                        ticket_type_id=hang_ghe,
                    )
                    db.session.add(seat)

            db.session.commit()

        return super().on_model_change(form, model, is_created)


class AdminManagerRoutesView(MyModelView):
    column_labels = {
        'id': 'ID Tuyến Bay',
        'maTuyenBay': 'Mã Tuyến Bay',
        'sanBayDi_id': 'Sân Bay Đi ',
        'sanBayDen_id': 'Sân Bay Đến ',
        'sanBayDi.maSanBay': 'Mã Sân Bay Đi',
        'sanBayDen.maSanBay': 'Mã Sân Bay Đến',
        'sanBayDi.tenSanBay':'Tên Sân Bay Đi',
        'sanBayDen.tenSanBay':'Tên Sân Bay Đến'
    }
    column_list = ["maTuyenBay", "sanBayDi_id", "sanBayDen_id"]
    column_searchable_list = ["id", "maTuyenBay","sanBayDi.maSanBay","sanBayDen.maSanBay","sanBayDi.tenSanBay","sanBayDen.tenSanBay"]
    column_filters = ["id", "maTuyenBay","sanBayDi.maSanBay","sanBayDen.maSanBay","sanBayDi.tenSanBay","sanBayDen.tenSanBay"]
    can_export = True
    form_extra_fields = {
        'maTuyenBay': StringField('Mã Tuyến Bay', validators=[DataRequired()]),
        'sanBayDi_id': QuerySelectField(
            'Sân Bay Đi',
            query_factory=lambda: SanBay.query.all(),
            get_label=lambda sanBay: f"{sanBay.maSanBay} - {sanBay.tenSanBay}",
            allow_blank=False,
            widget=CustomSelectWidget()
        ),
        'sanBayDen_id': QuerySelectField(
            'Sân Bay Đến',
            query_factory=lambda: SanBay.query.all(),
            get_label=lambda sanBay: f"{sanBay.maSanBay} - {sanBay.tenSanBay}",
            allow_blank=False,
            widget=CustomSelectWidget()
        )

    }
    def on_model_change(self, form, model, is_created):
        if form.sanBayDi_id.data:
            model.sanBayDi_id = form.sanBayDi_id.data.id
        if form.sanBayDen_id.data:
            model.sanBayDen_id = form.sanBayDen_id.data.id
        return super().on_model_change(form, model, is_created)
# Tùy chỉnh cách hiển thị tên sân bay trong bảng
    column_formatters = {
        'sanBayDi_id': lambda v, c, m, p: f"{m.sanBayDi.maSanBay} - {m.sanBayDi.tenSanBay}",
        'sanBayDen_id': lambda v, c, m, p: f"{m.sanBayDen.maSanBay} - {m.sanBayDen.tenSanBay}"
    }

    def scaffold_form(self):
        form = super().scaffold_form()

        # Thêm QuerySelectField cho Sân Bay Đi và Sân Bay Đến
        form.sanBayDi_id.query_factory = lambda: SanBay.query.all()
        form.sanBayDen_id.query_factory = lambda: SanBay.query.all()

        return form

class AdminReportStatisticsView(MyBaseView):
    @expose('/')
    def index(self):
        # Hiển thị giao diện thống kê
        return self.render('admin/admin_report_statistics.html')

    @expose('/data', methods=['GET'])
    def get_data(self):
        month = request.args.get('month', default=datetime.now().month, type=int)
        year = datetime.now().year  # Năm mặc định là năm hiện tại

        # Truy vấn dữ liệu thống kê
        stats = db.session.query(
            TuyenBay.maTuyenBay.label('route'),
            db.func.sum(VeMayBay.giaVe).label('revenue'),
            db.func.count(ChuyenBay.id).label('flight_count')
        ).join(ChuyenBay, TuyenBay.id == ChuyenBay.tuyenBay_id) \
            .join(VeMayBay, VeMayBay.chuyenBay_id == ChuyenBay.id) \
            .filter(
            db.extract('month', ChuyenBay.thoiGianKhoiHanh) == month,
            db.extract('year', ChuyenBay.thoiGianKhoiHanh) == year,
            VeMayBay.hanhKhach_id.isnot(None)
        ) \
            .group_by(TuyenBay.maTuyenBay).all()

        # Tính tổng doanh thu
        total_revenue = sum(stat.revenue for stat in stats)

        # Đảm bảo truyền total_revenue vào template
        return self.render('admin/admin_report_statistics.html', stats=stats, month=month, year=year,
                           total_revenue=total_revenue)

    @app.template_filter('humanize')
    def humanize_number(value):
        try:
            if isinstance(value, int):
                # Định dạng số với dấu phân cách hàng nghìn
                return f"{value:,}".replace(",", ".")
            elif isinstance(value, float):
                # Định dạng số thập phân với dấu phân cách
                return f"{value:,.2f}".replace(",", ".")
            return value
        except Exception as e:
            return value

    @expose('/export_excel', methods=['GET'])
    def export_excel(self):
        from io import BytesIO
        import openpyxl
        from openpyxl.chart import BarChart, Reference

        month = request.args.get('month', default=datetime.now().month, type=int)
        year = datetime.now().year

        # Truy vấn dữ liệu thống kê
        stats = db.session.query(
            TuyenBay.maTuyenBay.label('route'),
            db.func.sum(VeMayBay.giaVe).label('revenue'),
            db.func.count(ChuyenBay.id).label('flight_count')
        ).join(ChuyenBay, TuyenBay.id == ChuyenBay.tuyenBay_id) \
            .join(VeMayBay, VeMayBay.chuyenBay_id == ChuyenBay.id) \
            .filter(
            db.extract('month', ChuyenBay.thoiGianKhoiHanh) == month,
            db.extract('year', ChuyenBay.thoiGianKhoiHanh) == year,
            VeMayBay.hanhKhach_id.isnot(None)
        ) \
            .group_by(TuyenBay.maTuyenBay).all()

        # Tính tổng doanh thu
        total_revenue = sum(stat.revenue for stat in stats)

        # Tạo workbook Excel
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"Tháng {month} - {year}"

        # Header
        headers = ["STT", "Tuyến Bay", "Doanh Thu", "Số Lượt Bay", "Tỷ Lệ (%)"]
        ws.append(headers)

        # Dữ liệu
        for idx, stat in enumerate(stats, start=1):
            percentage = round((stat.revenue / total_revenue * 100), 2) if total_revenue > 0 else 0
            ws.append([idx, stat.route, stat.revenue, stat.flight_count, percentage])

        # Tổng doanh thu
        ws.append(["", "Tổng Doanh Thu", total_revenue, "", ""])

        # Tạo biểu đồ
        chart = BarChart()
        chart.title = "Doanh Thu Tuyến Bay"
        chart.x_axis.title = "Tuyến Bay"
        chart.y_axis.title = "Doanh Thu"

        # Lấy dữ liệu biểu đồ
        categories = Reference(ws, min_col=2, min_row=2, max_row=len(stats) + 1)  # Tên tuyến bay
        data = Reference(ws, min_col=3, min_row=1, max_row=len(stats) + 1)  # Doanh thu

        chart.add_data(data, titles_from_data=True)
        chart.set_categories(categories)
        chart.height = 10  # Chiều cao biểu đồ
        chart.width = 20  # Chiều rộng biểu đồ

        # Thêm biểu đồ vào sheet
        ws.add_chart(chart, "G2")  # Vị trí đặt biểu đồ

        # Ghi vào file và trả về response
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = f"attachment; filename=bao_cao_doanh_thu_{month}_{year}.xlsx"
        response.headers["Content-Type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return response


class LogoutView(MyBaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/admin')

# Thêm View vào Flask-Admim
admin.add_view(AdminChangeRegulationsView(name="Thay đổi quy định", endpoint="admin_change_regulations"))
admin.add_view(AdminManageEmployeeView(name="Quản lý nhân viên", endpoint="admin_manage_employees"))
admin.add_view(AdminManagerFlightsView(ChuyenBay,db.session,name="Quản lý chuyến bay"))
admin.add_view(AdminManagerRoutesView(TuyenBay,db.session,name="Quản lý tuyến bay"))
admin.add_view(AdminReportStatisticsView(name="Thống kê báo cáo", endpoint="admin_report_statistics"))
admin.add_view(LogoutView(name="Đăng xuất"))


