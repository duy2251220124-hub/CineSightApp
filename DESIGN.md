---
name: CineSight
description: Hệ thống giám sát ghế ngồi thông minh & soát vé AI cho rạp chiếu phim
colors:
  primary: "#2563EB"
  primary-hover: "#1D4ED8"
  primary-light: "#3B82F6"
  accent: "#38BDF8"
  neutral-bg: "#070B14"
  surface: "#121826"
  surface-strong: "#182234"
  surface-card: "#141926"
  border: "#24324D"
  border-subtle: "rgba(255, 255, 255, 0.08)"
  text: "#F8FAFC"
  text-muted: "#94A3B8"
  success: "#10B981"
  success-bg: "rgba(16, 185, 129, 0.15)"
  warning: "#F59E0B"
  warning-bg: "rgba(245, 158, 11, 0.15)"
  danger: "#EF4444"
  danger-bg: "rgba(239, 68, 68, 0.15)"
typography:
  display:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "28px"
    fontWeight: 800
    lineHeight: 1.2
    letterSpacing: "-0.5px"
  headline:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "20px"
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "-0.2px"
  title:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "15px"
    fontWeight: 600
    lineHeight: 1.4
  body:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
    fontSize: "11px"
    fontWeight: 600
    lineHeight: 1.3
  code:
    fontFamily: "'JetBrains Mono', ui-monospace, Consolas, monospace"
    fontSize: "13px"
    fontWeight: 600
    lineHeight: 1.4
rounded:
  sm: "6px"
  md: "10px"
  lg: "14px"
  xl: "20px"
  full: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.text}"
    rounded: "{rounded.md}"
    padding: "12px 20px"
  button-primary-hover:
    backgroundColor: "{colors.primary-hover}"
  card-base:
    backgroundColor: "{colors.surface-card}"
    rounded: "{rounded.lg}"
    padding: "14px"
  status-tag-screening:
    backgroundColor: "{colors.success-bg}"
    textColor: "{colors.success}"
    rounded: "{rounded.full}"
    padding: "4px 10px"
  status-tag-danger:
    backgroundColor: "{colors.danger-bg}"
    textColor: "{colors.danger}"
    rounded: "{rounded.full}"
    padding: "4px 10px"
---

# Design System: CineSight

## Overview
CineSight là hệ thống giám sát rạp chiếu phim và soát vé AI hoạt động trong môi trường ánh sáng yếu (Dark Mode). Thiết kế tập trung vào tính tương phản cao, khả năng nhận diện hình ảnh tức thì không gây mỏi mắt, thao tác nhanh trên thiết bị di động (Mobile App) và hiển thị dữ liệu trực quan trên màn hình quản trị (Web Admin).

---

## Colors
Bảng màu được chia theo các vai trò ngữ nghĩa cụ thể:

* **Màu Nền & Lớp Bề Mặt (Surfaces):**
  - Nền chính ứng dụng: `{colors.neutral-bg}` (`#070B14`) – Sắc đen sâu chuyên dụng cho rạp chiếu phim.
  - Thẻ & Container nội dung: `{colors.surface-card}` (`#141926`) và `{colors.surface}` (`#121826`).
  - Lớp bề mặt tương phản cao: `{colors.surface-strong}` (`#182234`).
  - Đường viền phân cách: `{colors.border}` (`#24324D`) và `{colors.border-subtle}` (`rgba(255, 255, 255, 0.08)`).
* **Màu Thương Hiệu (Brand / Action):**
  - Electric Blue `{colors.primary}` (`#2563EB`) – Dành cho các nút hành động chính, tab điều hướng đang kích hoạt và điểm nhấn thương hiệu.
  - Cyan Accent `{colors.accent}` (`#38BDF8`) – Điểm nhấn phụ, viền màn chiếu 2D và badge công nghệ.
* **Màu Trạng Thái Nghiệp Vụ (Semantic Status):**
  - 🟢 **Success / Screening:** `{colors.success}` (`#10B981`) – Suất chiếu đang diễn ra, vé hợp lệ, ghế đã soát vé.
  - 🟠 **Warning / Upcoming:** `{colors.warning}` (`#F59E0B`) – Suất chiếu sắp tới, ghế cần kiểm tra, cảnh báo chưa phân công.
  - 🔴 **Danger / Alert:** `{colors.danger}` (`#EF4444` / `#DC2626`) – Cảnh báo đối soát AI (ngồi không vé/ngồi sai ghế), vé không hợp lệ, ghế hỏng.

---

## Typography
* **Font gia đình chính (Primary Typeface):** `Inter` kết hợp hệ thống phông mặc định của hệ điều hành (`-apple-system`, `Roboto`).
* **Font hiển thị dữ liệu kỹ thuật (Monospace):** `JetBrains Mono` – Sử dụng cho mã suất chiếu, mã vé QR, tọa độ ghế (VD: `G05`, `H06`), và đồng hồ thời gian thực.
* **Hệ thống phân cấp (Hierarchy):**
  - **Display (28px / Bold 800):** Tên logo, số liệu thống kê lớn.
  - **Headline (20px - 24px / Bold 700):** Tiêu đề trang, tên phim nổi bật.
  - **Title (14px - 16px / SemiBold 600):** Tên mục, thẻ suất chiếu, tên nhân viên.
  - **Body (12px - 13px / Regular 400):** Mô tả phụ đề, thời lượng phim, tên phòng chiếu.
  - **Label / Tag (10px - 11px / Bold 600):** Huy hiệu trạng thái, nhãn phân công nhân sự, mã suất.

---

## Layout
* **Nguyên tắc Responsive & Mobile Resilience:**
  - Mọi màn hình form và nhập liệu bắt buộc sử dụng bộ ba `LayoutBuilder` + `SingleChildScrollView` + `ConstrainedBox(minHeight)` + `IntrinsicHeight` để loại bỏ vĩnh viễn lỗi tràn màn hình (`RenderFlex overflow`) khi bàn phím ảo bật lên.
  - Các màn hình danh sách (Suất chiếu, Lịch sử vé, Cảnh báo) sử dụng `ListView` cuộn trơn tru kèm `RefreshIndicator`.
* **Căn lề chuẩn (Grid & Spacing):**
  - Padding ngang màn hình di động: `14px` đến `16px`.
  - Khoảng cách giữa các thẻ danh sách: `10px`.
  - Padding nội bộ thẻ (Card padding): `12px` đến `14px`.

---

## Elevation & Depth
* **Chiều sâu qua sắc độ nền (Tonal Layering):**
  Thay vì đổ bóng mờ dày đặc (dễ gây bẩn giao diện trong Dark Mode), hệ thống tạo cảm giác phân tầng bằng sự chênh lệch màu nền (`#070B14` -> `#141926` -> `#182234`) kết hợp đường viền mảnh `1px` (`rgba(255, 255, 255, 0.08)`).
* **Hiệu ứng phát sáng có chủ đích (Glow & Accents):**
  - Logo chính: `BoxShadow(color: Color(0x402563EB), blurRadius: 20, spreadRadius: 2)`.
  - Suất chiếu đang chiếu: Viền xanh lục nhẹ `rgba(16, 185, 129, 0.4)` giúp thu hút ánh nhìn tức thì.

---

## Shapes
* **Quy chuẩn bo góc (Border Radius):**
  - Huy hiệu trạng thái / Nút nhỏ: `{rounded.sm}` (`6px`).
  - Poster phim / Khung nhập liệu (Input field): `{rounded.md}` (`8px` - `10px`).
  - Thẻ thông tin (Card container): `{rounded.lg}` (`14px`).
  - Khung thông tin nhân viên & header chính: `{rounded.xl}` (`20px`).
  - Avatar / Chấm trạng thái / Viên thuốc: `{rounded.full}` (`9999px`).

---

## Components

### 1. Thẻ Suất Chiếu (Showtime Card)
* Cột trái: Ảnh poster TMDB bo góc 8px (kích thước `58x84`), có khung dự phòng chứa icon điện ảnh nếu chưa có ảnh hoặc mất mạng.
* Cột phải: Tên phim (in đậm trắng, tối đa 2 dòng), huy hiệu trạng thái (Đang chiếu / Giờ chiếu), phòng chiếu, thời lượng, mã suất và mũi tên điều hướng.

### 2. Khung Thông Tin Nhân Viên & Ca Trực (Staff Profile Header)
* Container nền `{colors.surface-card}`, bo góc `20px`.
* Hàng trên: Avatar tròn, tên nhân viên, chức vụ & mã số, nút chuông thông báo bo tròn.
* Thẻ phụ lồng bên trong: Nền `{colors.surface-strong}`, hiển thị tên rạp kèm chấm tròn xanh `●`, giờ ca làm việc và số lượng phòng đang hoạt động.

### 3. Nút Thao Tác Nhanh (Quick Action Buttons)
* 4 nút vuông/chữ nhật bo góc `16px` xếp hàng ngang: **Suất Chiếu**, **Phòng Chiếu**, **Lịch Sử Vé**, **Bàn Giao & SC**.
* Icon xanh `{colors.primary}` kích thước 28px, nhãn chữ in đậm 12px.

### 4. Huy Hiệu Trạng Thái (Status Tag)
* Dạng viên thuốc bo tròn toàn phần (`rounded-full`), nền trong suốt 15% cùng tông màu với chữ để duy trì độ tương phản dịu mắt.

---

## Do's and Don'ts

### ✅ Do's (Nên làm):
1. **Luôn có Poster phim:** Mọi danh sách suất chiếu hoặc lựa chọn phim phải hiển thị poster để nhân viên nhận diện bằng hình ảnh tức thì.
2. **Ưu tiên suất đang chiếu:** Luôn tự động đưa suất phim đang chiếu trong ngày lên đầu danh sách.
3. **Cảnh báo đi kèm 3 thông số:** Mọi thông báo vi phạm phải chứa đủ: Số vé đã soát, số người thực tế, số ghế nghi vấn.
4. **Bọc cuộn an toàn:** Luôn dùng `SingleChildScrollView` cho màn hình có ô nhập liệu để chống lỗi tràn pixel khi mở bàn phím.

### ❌ Don'ts (Tuyệt đối tránh):
1. **Không dùng màu trắng chói gắt:** Tránh dùng nền trắng tinh `#FFFFFF` toàn màn hình trên Mobile App vì sẽ gây chói mắt nhân viên và ảnh hưởng đến khách xem phim trong rạp tối.
2. **Không dùng Column trần không cuộn:** Không đặt form nhập liệu trong `Column` cứng mà không có thanh cuộn thích ứng.
3. **Không spam thông báo rời rạc:** Tránh bắn từng thông báo nhỏ riêng lẻ cho từng ghế khi phòng chiếu có nhiều vi phạm cùng lúc.

