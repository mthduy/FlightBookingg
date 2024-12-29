
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
    const flightSelect = document.getElementById('flight'); // Dropdown chuyến bay
    const seatMap = document.getElementById('seat_map'); // Khu vực hiển thị sơ đồ ghế
    const priceInput = document.getElementById('price'); // Input để hiển thị giá vé
    const totalPriceInput = document.getElementById('total_price'); // Input để hiển thị tổng tiền
    const seatSelectedInput = document.getElementById('seat_selected'); // Input ẩn để lưu số ghế đã chọn

    let selectedSeatElement = null; // Biến lưu ghế hiện tại được chọn
    let totalMinutes = 0; // Biến lưu tổng thời gian chuyến bay tính bằng phút

    // Hàm tính tổng phút từ thời gian
    function calculateTotalMinutes(timeString) {
        if (!timeString) return 0;
        const [hours, minutes, seconds] = timeString.split(':').map(Number);
        return hours * 60 + minutes + (seconds || 0) / 60;
    }

    // Lấy tổng thời gian chuyến bay từ dữ liệu
    function updateFlightTime() {
        const flightTime = seatMap ? seatMap.dataset.thoiGianBay : '';
        const hourInput = document.getElementById('hour');
        const hourString = hourInput ? hourInput.value : '';
        totalMinutes = calculateTotalMinutes(flightTime || hourString);
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