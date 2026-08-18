# Detect Everything Mini

Dự án nhỏ để detect vật thể trên **ảnh/video** bằng YOLO-World và gán nhãn đoạn text trong
**file text/tài liệu**.
Bạn không cần tự dán nhãn hay train model cho bản demo này.

## Chương trình làm gì?

1. Bạn chọn ảnh, video hoặc tài liệu.
2. Bạn nhập tên vật cần tìm hoặc các nhãn text cần phân loại.
3. Với ảnh/video, model tự phát hiện, tự gắn tên, confidence và bounding box.
4. Với `.txt`, `.docx`, `.pdf`, chương trình trích xuất text và gán nhãn từng đoạn.
5. Kết quả được lưu vào thư mục `output`.

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
2. Chọn một hoặc nhiều ảnh/video/tài liệu cần xử lý.
3. Nhập class hoặc nhãn text, cách nhau bằng dấu phẩy.
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

Gán nhãn file text/tài liệu:

```powershell
python app.py --source "input\report.txt" "input\contract.docx" "input\invoice.pdf" --classes "invoice=hóa đơn tổng tiền khách hàng, contract=hợp đồng điều khoản bên A bên B, cv=kinh nghiệm kỹ năng học vấn"
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
    report_txt_detected.html
    contract_docx_detected.html
    invoice_pdf_detected.html
```

Với ảnh, số lượng in ra là số đối tượng trong ảnh.

Với `.txt`, `.docx`, `.pdf`, file kết quả `.html` sẽ chứa bảng `Labels` và phần
`Labeled Segments`. Mỗi đoạn text được gán một nhãn phù hợp nhất. Nên nhập nhãn theo
dạng `label=mô tả`, ví dụ `invoice=hóa đơn tổng tiền khách hàng`. PDF dạng scan ảnh có
thể không có text để trích xuất; trường hợp đó cần thêm OCR riêng.

Nếu đã cài `sentence-transformers`, chương trình sẽ gán nhãn theo ngữ nghĩa. Ví dụ nhãn
`bông hồng` vẫn có thể khớp với đoạn mô tả “một loài hoa màu đỏ, thân có gai...” dù đoạn
đó không viết trực tiếp chữ “bông hồng”. Nếu chưa cài thư viện này, chương trình sẽ dùng
cách so khớp từ khóa đơn giản hơn.

Với video, chương trình dùng tracking để đếm theo `track_id`, rồi gộp các track mới
xuất hiện gần vị trí track vừa mất dấu. Nhờ vậy cùng một người/xe xuất hiện qua nhiều
frame thường chỉ được tính một lần. Đây vẫn là con số ước tính, không phải nhận dạng
danh tính: nếu vật bị che khuất lâu, ra khỏi khung hình rồi vào lại, hoặc đứng quá gần
vật khác, chương trình vẫn có thể đếm lệch.

## Các file chính

```text
detector.py          Logic tải model và detect
text_detector.py     Logic đọc .txt/.docx/.pdf và gán nhãn đoạn text
app.py               Chạy bằng dòng lệnh
gui.py               Giao diện chọn ảnh/video/tài liệu
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

## Audio trong video

Với video có âm thanh, chương trình tạo thêm report cạnh file video kết quả:

```text
output/
    test_detected.mp4
    test_detected_report.html
    test_detected_report.json
```

File `.mp4` vẫn là video đã gắn bounding box cho phần hình ảnh. Nếu máy có `ffmpeg`,
chương trình sẽ ghép lại audio gốc vào video kết quả.

File `.html` là báo cáo tổng hợp:

- phần hình ảnh: đếm các object đã detect;
- phần lời nói: transcript theo mốc thời gian;
- nhãn nội dung từng đoạn nói dựa trên danh sách `--classes`;
- tóm tắt ngắn của từng đoạn transcript.

Để nhận dạng lời nói, máy cần cài `ffmpeg` và dependency `faster-whisper`. Model Whisper
mặc định là `base`; có thể đổi bằng biến môi trường:

```powershell
$env:DETECT_EVERYTHING_WHISPER_MODEL="small"
python app.py --source "input\meeting.mp4" --classes "technical_issue=lỗi kỹ thuật camera model, pricing=giá báo giá chi phí, complaint=khiếu nại không hài lòng"
```

Nếu thiếu `ffmpeg` hoặc model speech, chương trình vẫn tạo report và ghi rõ trạng thái
trong phần `Trạng thái`.
