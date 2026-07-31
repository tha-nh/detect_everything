# Detect Everything Mini

Dự án nhỏ để detect vật thể trên **ảnh hoặc video** bằng YOLO-World.
Bạn không cần tự dán nhãn hay train model cho bản demo này.

## Chương trình làm gì?

1. Bạn chọn ảnh hoặc video.
2. Bạn nhập tên các vật muốn tìm bằng tiếng Anh.
3. Model tự phát hiện, tự gắn tên, confidence và bounding box.
4. Ảnh/video kết quả được lưu vào thư mục `output`.

Ví dụ class:

```text
person, laptop, mobile phone, bottle
```

## Yêu cầu

- Windows 10/11
- Python 3.10 hoặc 3.11 được khuyến nghị
- Internet trong lần chạy đầu tiên để:
  - cài thư viện;
  - tải model `yolov8s-worldv2.pt`.
- Không bắt buộc có GPU. CPU vẫn chạy được nhưng video sẽ chậm hơn.

## Cách chạy dễ nhất trên Windows

### Bước 1: Giải nén ZIP

Giải nén project vào đường dẫn ngắn, ví dụ:

```text
D:\AI\detect-everything-mini
```

### Bước 2: Cài Python

Khi cài Python, nhớ chọn:

```text
Add Python to PATH
```

Kiểm tra:

```powershell
python --version
```

### Bước 3: Cài project

Nhấp đúp:

```text
setup_windows.bat
```

File này tự:

- tạo môi trường `.venv`;
- cài Ultralytics;
- cài OpenCV.

### Bước 4: Mở giao diện

Nhấp đúp:

```text
run_gui.bat
```

### Bước 5: Sử dụng

1. Bấm **Chọn file**, **Chọn nhiều file** hoặc **Chọn thư mục**.
2. Chọn một hoặc nhiều ảnh/video cần xử lý.
3. Nhập class bằng tiếng Anh, cách nhau bằng dấu phẩy.
4. Để confidence là `0.15`.
5. Bấm **Chạy detect**.
6. Xem danh sách trong bảng **Kết quả**.
7. Chọn một dòng rồi bấm **Mở kết quả**, hoặc bấm **Mở thư mục output**.

## Ví dụ class nên thử

Ảnh trong văn phòng:

```text
person, laptop, mobile phone, keyboard, computer mouse, bottle, chair
```

Ảnh đường phố:

```text
person, car, motorcycle, bus, bicycle, traffic light
```

Ảnh nhà bếp:

```text
person, cup, bowl, spoon, bottle, refrigerator
```

Bạn cũng có thể thử mô tả:

```text
red cup, person wearing glasses, worker wearing helmet
```

Open-vocabulary không bảo đảm nhận chính xác mọi mô tả. Prompt càng rõ và vật thể
càng phổ biến thì thường càng dễ nhận.

## Chạy bằng lệnh

Kích hoạt môi trường:

```powershell
.venv\Scripts\activate
```

Detect ảnh:

```powershell
python app.py --source "input\test.jpg" --classes "person,laptop,phone,bottle"
```

Detect video:

```powershell
python app.py --source "input\test.mp4" --classes "person,car,motorcycle"
```

Detect nhiều file trong một lần:

```powershell
python app.py --source "input\a.jpg" "input\b.png" "input\c.mp4" --classes "person,car,phone"
```

Detect toàn bộ ảnh/video được hỗ trợ trong một thư mục:

```powershell
python app.py --source "input" --classes "person,car,phone"
```

Khi xử lý nhiều file, `--output` sẽ được hiểu là thư mục đầu ra.

Đổi confidence:

```powershell
python app.py --source "input\test.jpg" --classes "person,phone" --confidence 0.15
```

Ảnh có nhiều vật nhỏ hoặc nhiều người ở xa:

```powershell
python app.py --source "input\crowd.jpg" --classes "person" --confidence 0.10 --image-size 1600
```

- Tăng `--image-size`: dễ bắt vật nhỏ hơn nhưng chạy chậm hơn, nhất là video.
- Giảm `--confidence`: hiện nhiều box hơn nhưng có thể nhận nhầm hơn.

- Giảm confidence: tìm được nhiều hơn nhưng dễ nhận nhầm.
- Tăng confidence: ít nhận nhầm hơn nhưng có thể bỏ sót.

## Kết quả

```text
output/
    test_detected.jpg
    test_detected.mp4
```

Với ảnh, số lượng in ra là số đối tượng trong ảnh.

Với video, chương trình dùng tracking để đếm theo `track_id`, rồi gộp các track mới
xuất hiện gần vị trí track vừa mất dấu. Nhờ vậy cùng một người/xe xuất hiện qua nhiều
frame thường chỉ được tính một lần. Đây vẫn là con số ước tính, không phải nhận dạng
danh tính: nếu vật bị che khuất lâu, ra khỏi khung hình rồi vào lại, hoặc đứng quá gần
vật khác, chương trình vẫn có thể đếm lệch.

## Các file chính

```text
detector.py          Logic tải model và detect
app.py               Chạy bằng dòng lệnh
gui.py               Giao diện chọn ảnh/video
setup_windows.bat    Cài đặt tự động
run_gui.bat          Mở giao diện
input/               Nơi bạn có thể đặt file đầu vào
output/              Kết quả sau detect
```

## Lỗi thường gặp

### `python is not recognized`

Cài lại Python và chọn `Add Python to PATH`, hoặc mở terminal mới.

### Lần đầu chạy lâu

Model đang được tải về. Các lần sau sẽ dùng file đã tải.

### Video chạy chậm

Máy đang dùng CPU. Hãy thử:

- video ngắn;
- video 720p;
- ít class hơn;
- đóng ứng dụng nặng khác.

### Không phát hiện được vật

Thử:

- dùng tên tiếng Anh;
- giảm confidence từ `0.25` xuống `0.15`;
- dùng tên đơn giản hơn, ví dụ `phone` thay vì mô tả quá dài;
- kiểm tra vật thể có đủ lớn và rõ trong ảnh không.

## Lưu ý quan trọng

Đây là **inference bằng model có sẵn**, nên bạn không cần dán nhãn thủ công.
Bạn chỉ cần nhập danh sách vật cần tìm. Khi muốn nhận diện vật thể rất đặc thù
của công ty hoặc dự án, lúc đó mới cần tạo dataset, dán nhãn và huấn luyện.
