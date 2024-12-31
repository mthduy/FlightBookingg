
function generateTicketClasses() {
        const count = document.getElementById('ticket-class-count').value;
        const tbody = document.getElementById('ticket-classes-body');
        tbody.innerHTML = '';

        for (let i = 1; i <= count; i++) {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><input type="text" name="class-${i}" value=" ${i}" readonly></td>
                <td><input type="number" name="price-${i}" placeholder="Nhập đơn giá" required></td>
                <td>
                    <input type="number" name="count-${i}" placeholder="Nhập số ghế (phải >= 6 và chia hết cho 6)" required>
                    <div class="error-message" id="error-message-${i}" style="color: red; display: none;">Số lượng ghế phải > 6 và chia hết cho 6</div>
                </td>
            `;
            tbody.appendChild(row);

            const countInput = row.querySelector(`input[name="count-${i}"]`);
            const errorMessage = row.querySelector(`#error-message-${i}`);

            countInput.addEventListener('input', function () {
                const countValue = parseInt(countInput.value);

                if (countValue < 6 || countValue % 6 !== 0) {
                    errorMessage.style.display = 'block';
                    countInput.setCustomValidity('Số lượng ghế phải >= 6 và chia hết cho 6');
                } else {
                    errorMessage.style.display = 'none';
                    countInput.setCustomValidity('');
                }
            });
        }
}

document.addEventListener('DOMContentLoaded', function () {
    const flightSelect = document.getElementById('flight');
    const seatMap = document.getElementById('seat_map');
    const priceInput = document.getElementById('price');
    const totalPriceInput = document.getElementById('total_price');
    const seatSelectedInput = document.getElementById('seat_selected');

    let selectedSeatElement = null;
    let totalMinutes = 0;


function calculateTotalHours(timeString) {
    if (!timeString) return 0;
    const [hours, minutes, seconds] = timeString.split(':').map(Number);
    // Tính tổng giờ và làm tròn lên
    return Math.ceil(hours + (minutes || 0) / 60 + (seconds || 0) / 3600);
}

    // Lấy tổng thời gian chuyến bay từ dữ liệu
    function updateFlightTime() {
        const flightTime = seatMap ? seatMap.dataset.thoiGianBay : '';
        const hourInput = document.getElementById('hour');
        const hourString = hourInput ? hourInput.value : '';
        totalMinutes = calculateTotalHours(flightTime || hourString);
        console.log('Total flight time (minutes):', totalMinutes);
    }

    // Hàm gắn sự kiện click cho ghế
    function attachSeatEvents() {
        const seats = seatMap.querySelectorAll('.seat');
        seats.forEach(seatElement => {
            seatElement.addEventListener('click', function () {
                if (seatElement.classList.contains('sold')) {
                    alert('Ghế này đã được bán. Vui lòng chọn ghế khác.');
                    return;
                }

                // Hủy chọn ghế trước đó
                if (selectedSeatElement) {
                    selectedSeatElement.classList.remove('selected');
                }

                // Chọn ghế mới
                seatElement.classList.add('selected');
                selectedSeatElement = seatElement;

                // Lấy giá tiền và số ghế từ thuộc tính
                const seatPrice = parseFloat(seatElement.dataset.ticketPrice) || 0;
                const totalPrice = seatPrice * totalMinutes;

                // Cập nhật giao diện
                totalPriceInput.value = totalPrice;
                priceInput.value = seatPrice;
                seatSelectedInput.value = seatElement.dataset.number;

                enableSubmitButton();
            });
        });
    }

    // Gắn sự kiện cho các ghế hiện có
    attachSeatEvents();

    // Lắng nghe sự kiện thay đổi chuyến bay
    flightSelect.addEventListener('change', function () {
        const maChuyenBay = flightSelect.value;

        if (!maChuyenBay) {
            alert('Vui lòng chọn một chuyến bay hợp lệ.');
            return;
        }

        fetch(`/api/seats?maChuyenBay=${maChuyenBay}`)
            .then(response => response.json())
            .then(data => {
                seatMap.innerHTML = ''; // Xóa sơ đồ ghế cũ
                selectedSeatElement = null; // Reset ghế được chọn

                data.forEach(seat => {
                    const seatElement = document.createElement('div');
                    seatElement.classList.add('seat', seat.status);
                    seatElement.setAttribute('data-number', seat.seat_number);
                    seatElement.setAttribute('data-ticket-price', seat.price);
                    seatElement.innerText = `${seat.seat_number} (${seat.status})`;

                    seatMap.appendChild(seatElement);
                });

                attachSeatEvents(); // Gắn lại sự kiện click cho ghế
                totalPriceInput.value = '0.00';
                priceInput.value = '0.00';
                seatSelectedInput.value = '';
            })
            .catch(error => console.error('Error loading seat map:', error));
    });

    // Lấy thời gian chuyến bay khi chọn chuyến bay
    flightSelect.addEventListener('change', function () {
        const flightCode = this.value;
        if (flightCode) {
            fetch(`/api/get_flight_duration?flight=${flightCode}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const hourInput = document.getElementById('hour');
                        if (hourInput) hourInput.value = data.thoiGianBay;
                        updateFlightTime();
                    } else {
                        alert(data.message);
                    }
                })
                .catch(err => console.error('Error fetching flight info:', err));
        }
    });

    // Cập nhật thời gian chuyến bay khi tải trang
    window.addEventListener('load', function () {
        updateFlightTime();
        totalPriceInput.value = '0.00';
        priceInput.value = '0.00';
        seatSelectedInput.value = '';
    });
});

function enableSubmitButton() {
        const selectedSeat = document.getElementById('seat_selected').value;
        document.getElementById('submitButton').disabled = !selectedSeat; // Chỉ bật nút khi ghế được chọn
    }


function openEditForm(id, name, email, role) {
        var editForm = document.getElementById('edit-form');

        // Hiển thị modal
        editForm.style.display = 'flex';  // Modal sẽ hiển thị với flex

        // Điền thông tin vào các trường trong modal
        document.getElementById('edit-id').value = id;
        document.getElementById('edit-name').value = name;
        document.getElementById('edit-email').value = email;
        document.getElementById('edit-role').value = 'Nhân Viên'; // Chỉ hiển thị 'Nhân Viên' trong UI
        document.getElementById('edit-role-hidden').value = 'EMPLOYEE'; // Gửi 'EMPLOYEE' qua form


        // Ngăn chặn sự kiện khác làm đóng modal tự động
        event.preventDefault();  // Ngừng các sự kiện khác
    }

    // Đóng modal khi bấm nút đóng
    function closeEditForm() {
        var editForm = document.getElementById('edit-form');
        editForm.style.display = 'none'; // Ẩn modal
    }

    // Ngăn form mặc định submit để tránh reload trang khi nhấn nút "Lưu"
    document.getElementById("edit-form").addEventListener("submit", function(event) {
        event.preventDefault();  // Ngừng submit mặc định

        // Gửi thông tin sửa qua AJAX hoặc reload trang sau khi sửa
        this.submit();  // Hoặc thực hiện AJAX để gửi dữ liệu
    });