document.addEventListener('DOMContentLoaded', function () {
    const flightSelect = document.getElementById('flight');  // Dropdown chuyến bay
    const seatMap = document.getElementById('seat_map');  // Khu vực hiển thị sơ đồ ghế
    const priceInput = document.getElementById('price');  // Input để hiển thị giá vé
    const seatSelectedInput = document.getElementById('seat_selected');  // Input ẩn để lưu số ghế đã chọn

    let selectedSeatElement = null; // Biến lưu ghế hiện tại được chọn

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

                // Cập nhật giá và ghế được chọn
                priceInput.value = seatElement.dataset.ticketPrice;
                seatSelectedInput.value = seatElement.dataset.number;
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
function generateTicketClasses() {
        const count = document.getElementById('ticket-class-count').value;
        const tbody = document.getElementById('ticket-classes-body');
        tbody.innerHTML = ''; // Xóa các dòng cũ

        for (let i = 1; i <= count; i++) {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><input type="text" name="class-${i}" value=" ${i}" readonly></td>
                <td><input type="number" name="price-${i}" placeholder="Nhập đơn giá" required></td>
                <td><input type="number" name="count-${i}" placeholder="Nhập số ghế" required></td>
            `;
            tbody.appendChild(row);
        }
    }
