
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
    const flightSelect = document.getElementById('flight');  // Dropdown chuyến bay
    const seatMap = document.getElementById('seat_map');  // Khu vực hiển thị sơ đồ ghế
    const priceInput = document.getElementById('price');  // Input để hiển thị giá vé
    const totalPriceInput = document.getElementById('total_price');  // Input để hiển thị tổng tiền

    const seatSelectedInput = document.getElementById('seat_selected');  // Input ẩn để lưu số ghế đã chọn

    let selectedSeatElement = null; // Biến lưu ghế hiện tại được chọn
    let totalMinutes = 0;  // Biến lưu tổng thời gian chuyến bay tính bằng phút

    // Kiểm tra xem có dữ liệu thời gian bay từ dataset không
const flightTime = seatMap ? seatMap.dataset.thoiGianBay : ''; // Lấy thoiGianBay từ dataset, mặc định là chuỗi rỗng
console.log('flightTime:', flightTime);  // Debug log

if (flightTime) {
    const [hours, minutes, seconds] = flightTime.split(':').map(Number); // Tách ra hours, minutes, seconds
    console.log('hours:', hours, 'minutes:', minutes, 'seconds:', seconds);  // Debug log
    totalMinutes = hours * 60 + minutes + seconds / 60; // Tính tổng số phút
} else {
    // Nếu không có thoiGianBay từ dataset, thử lấy từ input hour
    const hourInput = document.getElementById('hour');
    const hourString = hourInput ? hourInput.value : '';
    console.log('hourString:', hourString);  // Debug log
    if (hourString) {
        const [hours, minutes, seconds] = hourString.split(':').map(Number);
        console.log('hours:', hours, 'minutes:', minutes, 'seconds:', seconds);  // Debug log
        totalMinutes = hours * 60 + minutes + seconds / 60; // Tính tổng số phút
    }
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
                const seatPrice = parseFloat(seatElement.dataset.ticketPrice);

                // Tính tổng tiền (giả sử tính theo thời gian chuyến bay)
                const totalPrice = seatPrice * totalMinutes ; // Lấy tổng thời gian chuyến bay theo phút

                // Cập nhật giá và ghế được chọn
                totalPriceInput.value = totalPrice;
                priceInput.value = seatPrice;
                seatSelectedInput.value = seatElement.dataset.number; // Lưu số ghế đã chọn
            });
        });
    }

    // Gắn sự kiện cho các ghế có sẵn khi DOM tải xong
    attachSeatEvents();

    // Lắng nghe sự kiện thay đổi chuyến bay
    flightSelect.addEventListener('change', function () {
        const maChuyenBay = flightSelect.value; // Lấy ID chuyến bay đã chọn

        // Gửi yêu cầu AJAX (API call) tới Flask để lấy danh sách ghế
        fetch(`/api/seats?maChuyenBay=${maChuyenBay}`)
            .then(response => response.json())  // Chuyển dữ liệu JSON từ API về
            .then(data => {
                // Xóa sơ đồ ghế cũ
                seatMap.innerHTML = '';
                selectedSeatElement = null; // Reset ghế được chọn khi thay đổi chuyến bay

                // Tạo lại sơ đồ ghế mới dựa trên dữ liệu từ API
                data.forEach(seat => {
                    const seatElement = document.createElement('div');
                    seatElement.classList.add('seat', seat.status);
                    seatElement.setAttribute('data-number', seat.seat_number);
                    seatElement.setAttribute('data-ticket-price', seat.price);
                    seatElement.innerText = `${seat.seat_number} (${seat.status})`;

                    seatMap.appendChild(seatElement);
                });

                // Gắn lại sự kiện sau khi tạo ghế mới
                attachSeatEvents();
            })
            .catch(error => console.error('Error loading seat map:', error));  // Xử lý lỗi nếu có
    });
});
window.onload = function() {
        // Lắng nghe sự kiện thay đổi giá trị trong dropdown (chọn chuyến bay)
        document.getElementById('flight').addEventListener('change', function() {
            const flightCode = this.value;  // Lấy mã chuyến bay từ dropdown

            if (flightCode) {
                // Gửi yêu cầu GET tới server để lấy thông tin thời gian bay
                fetch(`/api/get_flight_duration?flight=${flightCode}`)
                    .then(response => response.json())  // Chuyển đổi response thành JSON
                    .then(data => {
                        if (data.success) {
                            // Gán thời gian bay vào input
                            document.getElementById('hour').value = data.thoiGianBay;
                        } else {
                            // Thông báo lỗi nếu không có dữ liệu
                            alert(data.message);
                        }
                    })
                    .catch(err => console.error('Error fetching flight info:', err));  // Xử lý lỗi nếu có
            }
        });
    };
