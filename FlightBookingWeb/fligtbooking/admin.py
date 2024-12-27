import json

from flask import redirect, request, flash
from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.fields import QuerySelectField
from flask_login import current_user, logout_user
from markupsafe import Markup
from wtforms.fields.choices import SelectField
from wtforms.fields.simple import StringField
from wtforms.validators import DataRequired
from wtforms.widgets.core import html_params, Select

from fligtbooking import app, db
from fligtbooking.models import Role, Regulation, ChuyenBay, TuyenBay, SanBay

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
    @expose('/')
    def index(self):
        # Render file template admin_manage_employees.html từ thư mục admin
        return self.render('admin/admin_manage_employees.html')

class AdminManagerFlightsView(ModelView):
    column_labels = {
        'id': 'ID Chuyến Bay',
        'maChuyenBay': 'Mã Chuyến Bay',
        'thoiGianKhoiHanh': 'Thời Gian Khởi Hành',
        'thoiGianDen': 'Thời Gian Đến',
        'thoiGianBay': 'Thời Gian Bay',
        'tuyenBay_id': 'Tuyến Bay ID'
    }
    column_list = ["maChuyenBay", "thoiGianKhoiHanh", "thoiGianDen", "thoiGianBay", "tuyenBay_id"]
    column_searchable_list = ["id", "maChuyenBay"]
    column_filters = ["id", "maChuyenBay"]
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
            model.tuyenBay_id = form.tuyenBay_id.data.id  # Lấy id của TuyenBay thay vì đối tượng
        return super().on_model_change(form, model, is_created)


class AdminManagerRoutesView(MyModelView):
    column_labels = {
        'id': 'ID Tuyến Bay',
        'maTuyenBay': 'Mã Chuyến Bay',
        'sanBayDi_id': 'Sân Bay Đi ID',
        'sanBayDen_id': 'Sân Bay Đến ID',
        'soChuyenBay': 'Số Chuyến Bay',
        'maSanBay': 'Mã Sân Bay',
    }
    column_list = ["maTuyenBay", "sanBayDi_id", "sanBayDen_id", "soChuyenBay"]
    column_searchable_list = ["id", "maTuyenBay"]
    column_filters = ["id", "maTuyenBay"]
    can_export = True
    form_extra_fields = {
        'maTuyenBay': StringField('Mã Tuyến Bay', validators=[DataRequired()]),
        'sanBayDi_id': QuerySelectField(
            'Sân Bay Đi',
            query_factory=lambda: SanBay.query.all(),
            get_label='maSanBay',
            allow_blank=False,
            widget=CustomSelectWidget()
        ),
        'sanBayDen_id': QuerySelectField(
            'Sân Bay Đến',
            query_factory=lambda: SanBay.query.all(),
            get_label='maSanBay',
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

class AdminReportStatisticsView(MyBaseView):
    @expose('/')
    def index(self):
        return self.render('admin/admin_report_statistics.html')



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


