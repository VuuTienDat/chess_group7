# Chess Evaluation Module

Module này chứa các hàm đánh giá vị trí cờ vua, được sử dụng bởi engine để đánh giá chất lượng của các nước đi.

## Cấu trúc

Module được chia thành các file nhỏ, mỗi file tập trung vào một khía cạnh đánh giá:

1. `base.py` - Lớp cơ sở cho evaluator
2. `weights.py` - Các hằng số và trọng số
3. `pawn_evaluation.py` - Đánh giá cấu trúc tốt
4. `king_evaluation.py` - Đánh giá an toàn vua
5. `piece_evaluation.py` - Đánh giá hoạt động quân
6. `position_evaluation.py` - Đánh giá vị trí quân
7. `main_evaluator.py` - Evaluator chính kết hợp tất cả

## Các yếu tố đánh giá

### 1. Đánh giá vật chất
- Giá trị cơ bản của các quân cờ
- Tốt = 100, Mã = 320, Tượng = 330, Xe = 500, Hậu = 900, Vua = 20000

### 2. Đánh giá cấu trúc tốt
- Tốt thông (không có tốt đối phương cản đường)
- Tốt cô lập (không có tốt đồng minh trên các cột liền kề)
- Tốt đôi (có tốt đồng minh trên cùng cột)
- Tốt lùi (không thể được hỗ trợ bởi tốt đồng minh)
- Chuỗi tốt (các tốt liên kết với nhau)
- Đa số tốt (nhiều tốt hơn đối phương trên một bên)

### 3. Đánh giá an toàn vua
- Vua ở trung tâm (bất lợi)
- Quyền nhập thành
- Khiên vua (tốt bảo vệ vua)
- Mẫu tấn công vua
- Hoạt động vua trong tàn cuộc
- Đối lập trong tàn cuộc

### 4. Đánh giá hoạt động quân
- Kiểm soát trung tâm
- Outpost (vị trí an toàn không bị tốt đối phương tấn công)
- Cột mở/bán mở cho xe
- Xe trên hàng 7
- Cặp tượng
- Phối hợp quân

### 5. Đánh giá chiến thuật
- Ghim quân
- Đòn đôi
- Tấn công phát hiện
- Tấn công xuyên

### 6. Đánh giá vị trí
- Kiểm soát trung tâm
- Phát triển quân
- Kiểm soát không gian
- Tempo (lợi thế về lượt đi)

## Sử dụng

```python
from evaluation.main_evaluator import MainEvaluator

# Tạo evaluator
evaluator = MainEvaluator()

# Đánh giá vị trí
score = evaluator.evaluate(board)
```

## Tối ưu hóa

Các hàm đánh giá đã được tối ưu hóa để:
1. Sử dụng cache cho các tính toán lặp lại
2. Giảm thiểu việc tạo bản sao bàn cờ
3. Sử dụng bitboard cho các phép tính nhanh
4. Tránh các tính toán không cần thiết
5. Sử dụng các cấu trúc dữ liệu hiệu quả 