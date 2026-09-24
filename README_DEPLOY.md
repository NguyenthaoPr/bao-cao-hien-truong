# BÁO CÁO HIỆN TRƯỜNG — THỦY LỢI AI

App độc lập để deploy trên Vercel. Không cần Render API.

## 1. Biến môi trường bắt buộc

Trong Vercel → Project → Settings → Environment Variables, thêm:

- `GEMINI_API_KEY` = API key Gemini của hệ thống
- `GEMINI_FILE_SEARCH_STORE` = tên File Search Store đang chứa hồ sơ THỦY LỢI AI
- `GEMINI_MODEL` = model Gemini muốn sử dụng (nếu bỏ trống sẽ dùng `gemini-3.6-flash` theo cấu hình hiện tại)

Không đưa API key vào `index.html`.

## 2. Deploy

1. Tạo GitHub repository mới, ví dụ `bao-cao-hien-truong`.
2. Upload toàn bộ nội dung thư mục này lên repository.
3. Vào Vercel → Add New Project → Import repository.
4. Framework: Other.
5. Không cần Build Command.
6. Deploy.

## 3. Luồng xử lý

Điện thoại → Vercel Function → Gemini Vision + Gemini File Search → dự thảo → cán bộ kiểm tra/chỉnh sửa → Vercel Function → PDF.

File Search được gọi ngay trong endpoint `/api/field-report`; nếu kho File Search có tài liệu phù hợp, Gemini được cung cấp công cụ File Search để truy xuất và kết quả trả về có danh sách citation khi Gemini cung cấp citation.

## 4. Lưu ý

- GPS được lấy trực tiếp trên điện thoại bằng Geolocation API.
- Ảnh được xử lý và đóng dấu phía trình duyệt trước khi gửi.
- PDF được tạo trực tiếp bởi Vercel Function, không qua Render.
- Nếu File Search không có tài liệu phù hợp, AI phải nói rõ thay vì tự bịa căn cứ.
- Đây là công cụ lập dự thảo; cán bộ có thẩm quyền vẫn cần kiểm tra trước khi dùng như báo cáo chính thức.
