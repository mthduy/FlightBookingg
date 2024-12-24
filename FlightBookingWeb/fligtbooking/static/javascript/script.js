document.addEventListener('DOMContentLoaded', function () {
    const flightSelect = document.getElementById('flight');  // Dropdown chuyến bay
    const seatMap = document.getElementById('seat_map');  // Khu vực hiển thị sơ đồ ghế
    const priceInput = document.getElementById('price');  // Input để hiển thị giá vé
    const seatSelectedInput = document.getElementById('seat_selected');  // Input ẩn để lưu số ghế đã chọn

    let selectedSeatElement = null; // Biến lưu ghế hiện tại được chọn

    // Lắng nghe sự kiện thay đổi chuyến bay
    flightSelect.addEventListener('change', function () {
        const flightId = flightSelect.value; // Lấy ID chuyến bay đã chọn

        // Gửi yêu cầu AJAX (API call) tới Flask để lấy danh sách ghế
        fetch(`/api/seats?flight_id=${flightId}`)
            .then(response => response.json())  // Chuyển dữ liệu JSON từ API về
            .then(data => {
                // Xóa sơ đồ ghế cũ
                seatMap.innerHTML = '';
                selectedSeatElement = null; // Reset ghế được chọn khi thay đổi chuyến bay

                // Tạo lại sơ đồ ghế mới dựa trên dữ liệu từ API
                data.forEach(seat => {
                    const seatElement = document.createElement('div');
                    seatElement.classList.add('seat', seat.status);
                    seatElement.setAttribute('data-seat', seat.seat_number);
                    seatElement.setAttribute('data-price', seat.price);
                    seatElement.innerText = `${seat.seat_number} (${seat.status})`;

                    // Khi người dùng click vào ghế, cập nhật giá vé và ghế đã chọn
                    seatElement.addEventListener('click', function () {
                        if (seatElement.classList.contains('sold')) {
                            // Nếu ghế đã bán, không cho chọn
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
                        priceInput.value = seatElement.dataset.price;
                        seatSelectedInput.value = seatElement.dataset.seat;
                    });

                    seatMap.appendChild(seatElement);
                });
            })
            .catch(error => console.error('Error loading seat map:', error));  // Xử lý lỗi nếu có
    });
});
