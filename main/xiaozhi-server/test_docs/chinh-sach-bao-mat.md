# CHÍNH SÁCH BẢO MẬT THÔNG TIN
## Công ty TNHH Công Nghệ MekongAI
### Phiên bản 2.0 — Cập nhật ngày 01/04/2026

---

## 1. GIỚI THIỆU

Chính sách bảo mật này mô tả cách Công ty TNHH Công Nghệ MekongAI ("Công ty", "chúng tôi") thu thập, sử dụng, lưu trữ và bảo vệ thông tin cá nhân của khách hàng, đối tác và người dùng dịch vụ.

Chính sách này áp dụng cho tất cả sản phẩm và dịch vụ do MekongAI cung cấp, bao gồm nhưng không giới hạn:
- Trợ lý AI giọng nói Xiaozhi
- Nền tảng quản lý thiết bị IoT
- Dịch vụ xử lý ngôn ngữ tự nhiên (NLP)
- API tích hợp cho đối tác

---

## 2. THU THẬP THÔNG TIN

### 2.1 Thông tin chúng tôi thu thập

**Thông tin cá nhân cơ bản:**
- Họ tên, email, số điện thoại khi đăng ký tài khoản
- Địa chỉ IP và thông tin thiết bị (MAC address, hệ điều hành)

**Dữ liệu giọng nói:**
- Bản ghi âm giọng nói khi sử dụng trợ lý AI Xiaozhi
- Thời lượng tối đa mỗi phiên: 120 giây
- Dữ liệu giọng nói được mã hóa bằng giao thức Opus trước khi truyền

**Dữ liệu hội thoại:**
- Lịch sử trò chuyện với trợ lý AI
- Metadata phiên hội thoại (thời gian bắt đầu, kết thúc, session ID)

**Dữ liệu thiết bị IoT:**
- Trạng thái thiết bị (bật/tắt, nhiệt độ, độ ẩm)
- Lịch sử điều khiển thiết bị

### 2.2 Cách chúng tôi thu thập

- **Trực tiếp từ người dùng:** Khi bạn đăng ký, sử dụng dịch vụ, hoặc liên hệ hỗ trợ
- **Tự động:** Thông qua cookies, log hệ thống, và SDK tích hợp trên thiết bị
- **Từ bên thứ ba:** Đối tác cung cấp dịch vụ xác thực (Google, Facebook OAuth)

---

## 3. SỬ DỤNG THÔNG TIN

Chúng tôi sử dụng thông tin thu thập cho các mục đích sau:

### 3.1 Cung cấp dịch vụ
- Xử lý giọng nói thành văn bản (ASR - Automatic Speech Recognition)
- Tổng hợp giọng nói từ văn bản (TTS - Text-to-Speech)
- Phân tích ý định người dùng và trả lời câu hỏi
- Điều khiển thiết bị thông minh qua giọng nói

### 3.2 Cải thiện dịch vụ
- Huấn luyện và tối ưu mô hình AI (chỉ với dữ liệu đã được ẩn danh hóa)
- Phân tích xu hướng sử dụng để cải thiện trải nghiệm
- Kiểm tra và sửa lỗi hệ thống

### 3.3 Bảo mật
- Phát hiện và ngăn chặn gian lận, lạm dụng dịch vụ
- Xác thực danh tính người dùng
- Giám sát và phản ứng sự cố bảo mật

---

## 4. BẢO VỆ THÔNG TIN

### 4.1 Biện pháp kỹ thuật

**Mã hóa dữ liệu:**
- Tất cả dữ liệu truyền tải được mã hóa TLS 1.3
- Dữ liệu giọng nói mã hóa Opus codec trước khi gửi qua WebSocket
- Dữ liệu lưu trữ mã hóa AES-256 tại rest
- API keys và credentials mã hóa bằng SM2 asymmetric encryption

**Kiểm soát truy cập:**
- Xác thực JWT (JSON Web Token) cho tất cả API endpoints
- Phân quyền role-based: admin, user, device
- Rate limiting: tối đa 100 requests/phút/user
- IP whitelist cho các API quản trị

**Hạ tầng:**
- Máy chủ đặt tại các data center đạt chuẩn ISO 27001
- Sao lưu dữ liệu tự động mỗi 6 giờ
- Hệ thống giám sát 24/7 với cảnh báo tức thời
- Tường lửa WAF và DDoS protection

### 4.2 Biện pháp tổ chức

- Chỉ nhân viên được ủy quyền mới có quyền truy cập dữ liệu người dùng
- Đào tạo bảo mật định kỳ cho toàn bộ nhân viên
- Kiểm tra đánh giá bảo mật (penetration testing) mỗi quý
- Chính sách clean desk và screen lock

---

## 5. LƯU TRỮ VÀ XÓA DỮ LIỆU

### 5.1 Thời gian lưu trữ

| Loại dữ liệu | Thời gian lưu trữ | Ghi chú |
|---|---|---|
| Thông tin tài khoản | Đến khi xóa tài khoản | Có thể yêu cầu xóa bất kỳ lúc nào |
| Dữ liệu giọng nói | 30 ngày | Tự động xóa sau 30 ngày |
| Lịch sử hội thoại | 90 ngày | Có thể xóa thủ công |
| Log hệ thống | 180 ngày | Dùng cho mục đích debug và audit |
| Dữ liệu thiết bị IoT | 365 ngày | Bao gồm lịch sử trạng thái |
| Dữ liệu ẩn danh (analytics) | Vô thời hạn | Không liên kết với cá nhân |

### 5.2 Quy trình xóa dữ liệu

Khi người dùng yêu cầu xóa tài khoản:
1. Vô hiệu hóa tài khoản ngay lập tức
2. Xóa dữ liệu cá nhân trong vòng 7 ngày làm việc
3. Xóa bản sao lưu trong vòng 30 ngày
4. Gửi email xác nhận hoàn tất xóa

---

## 6. CHIA SẺ THÔNG TIN

### 6.1 Chúng tôi KHÔNG bán hoặc cho thuê thông tin cá nhân

### 6.2 Trường hợp chia sẻ với bên thứ ba

Chúng tôi chỉ chia sẻ thông tin trong các trường hợp:

- **Nhà cung cấp dịch vụ:** Google (Gemini LLM, TTS), Microsoft (Edge TTS), OpenAI (GPT models) — chỉ dữ liệu cần thiết để xử lý yêu cầu
- **Yêu cầu pháp lý:** Khi có yêu cầu từ cơ quan chức năng có thẩm quyền
- **Bảo vệ quyền lợi:** Để bảo vệ quyền lợi, tài sản hoặc an toàn của công ty và người dùng
- **Chuyển nhượng kinh doanh:** Trong trường hợp sáp nhập hoặc mua lại (với thông báo trước)

### 6.3 Dữ liệu gửi đến LLM providers

Khi bạn trò chuyện với trợ lý AI:
- Nội dung hội thoại được gửi đến LLM provider (Gemini/OpenAI) để xử lý
- Chúng tôi KHÔNG gửi thông tin cá nhân (họ tên, email, SĐT) đến LLM
- Dữ liệu giọng nói thô KHÔNG được gửi — chỉ văn bản đã chuyển đổi (ASR)

---

## 7. QUYỀN CỦA NGƯỜI DÙNG

Theo quy định pháp luật Việt Nam và GDPR (nếu áp dụng), bạn có quyền:

### 7.1 Quyền truy cập
- Yêu cầu xem toàn bộ dữ liệu cá nhân chúng tôi lưu trữ
- Nhận bản sao dữ liệu trong vòng 15 ngày làm việc

### 7.2 Quyền chỉnh sửa
- Cập nhật thông tin cá nhân bất kỳ lúc nào qua trang quản lý tài khoản
- Yêu cầu chỉnh sửa thông tin không chính xác

### 7.3 Quyền xóa
- Yêu cầu xóa toàn bộ dữ liệu cá nhân
- Xóa lịch sử hội thoại
- Xóa dữ liệu thiết bị

### 7.4 Quyền hạn chế xử lý
- Yêu cầu tạm ngừng xử lý dữ liệu (ngoại trừ lưu trữ)
- Rút lại sự đồng ý đã cấp trước đó

### 7.5 Quyền di chuyển dữ liệu
- Nhận dữ liệu ở định dạng máy có thể đọc được (JSON/CSV)
- Chuyển dữ liệu sang nhà cung cấp dịch vụ khác

---

## 8. BẢO HÀNH VÀ HỖ TRỢ

### 8.1 Chính sách bảo hành thiết bị IoT

- **Thời gian bảo hành:** 12 tháng kể từ ngày mua
- **Phạm vi:** Lỗi phần cứng do nhà sản xuất
- **Không bảo hành:** Hư hỏng do người dùng (rơi, nước, tự sửa)
- **Quy trình:** Liên hệ hotline → Gửi thiết bị → Kiểm tra → Sửa/thay mới trong 7 ngày

### 8.2 Hỗ trợ kỹ thuật

- **Email:** support@mekongai.com
- **Hotline:** 1900-xxxx-xx (8:00 - 22:00 hàng ngày)
- **Chat trực tuyến:** Trên website mekongai.com
- **Thời gian phản hồi:** Trong vòng 24 giờ (ngày làm việc)

---

## 9. COOKIE VÀ CÔNG NGHỆ THEO DÕI

### 9.1 Các loại cookie sử dụng

| Cookie | Mục đích | Thời hạn | Bắt buộc |
|---|---|---|---|
| session_token | Xác thực phiên đăng nhập | Phiên | Có |
| csrf_token | Bảo vệ CSRF attacks | Phiên | Có |
| preferences | Lưu cài đặt ngôn ngữ, theme | 1 năm | Không |
| analytics | Thống kê sử dụng (Google Analytics) | 2 năm | Không |

### 9.2 Cách quản lý cookie
- Bạn có thể tắt cookie không bắt buộc trong phần cài đặt trình duyệt
- Tắt cookie bắt buộc có thể khiến một số tính năng không hoạt động

---

## 10. THAY ĐỔI CHÍNH SÁCH

- Chúng tôi có thể cập nhật chính sách này định kỳ
- Mọi thay đổi quan trọng sẽ được thông báo qua email hoặc thông báo trong ứng dụng
- Phiên bản mới nhất luôn có sẵn tại: https://mekongai.com/privacy-policy
- Tiếp tục sử dụng dịch vụ sau khi thay đổi đồng nghĩa với việc chấp nhận chính sách mới

---

## 11. LIÊN HỆ

Nếu bạn có bất kỳ câu hỏi hoặc yêu cầu nào liên quan đến chính sách bảo mật:

- **Email bảo mật:** privacy@mekongai.com
- **Địa chỉ:** Tầng 5, Tòa nhà ABC, 123 Nguyễn Huệ, Quận 1, TP. Hồ Chí Minh
- **Số điện thoại:** (028) xxxx-xxxx
- **Người phụ trách bảo vệ dữ liệu (DPO):** Nguyễn Văn A — dpo@mekongai.com

---

*Tài liệu này có hiệu lực từ ngày 01/04/2026*
*© 2026 MekongAI. Bảo lưu mọi quyền.*
