# Test6.2 Report — Lấp khoảng trống hình học 2D của Test6.1 (Case D)

**Bối cảnh:** người dùng chỉ ra chính xác một khoảng trống thật trong Test6.1 Việc 2: cả 3 case
A/B/C đều dùng toạ độ **1D (trục số)**, nên chỉ kiểm được cơ chế "thứ tự thời gian" (case B/C) —
chưa kiểm lại được cơ chế **"đường tắt hình học 2D"** (một cạnh chéo rẻ bất ngờ mà 4 con số tóm
tắt của route không nhìn thấy được), vốn là cơ chế cốt lõi đã hạ gục Pareto-dominance ở Test3 và
D1 ở Test4. Nhận xét của người dùng về case A (yếu hơn B/C, gần với kiểm feasibility đơn giản
hơn là kiểm đúng cơ chế nguy hiểm) cũng được ghi nhận đúng khi nhìn lại — case A không có gì
thay thế được ở đây (case D nhắm đúng chỗ case A định làm nhưng làm chưa tới).

**Kết luận ngắn gọn: Case D (2D thật, thiết kế mới) PASS tuyệt đối.** DP tìm đúng bundle khó
nhất, khớp brute_force tuyệt đối, và một phát hiện phụ có giá trị riêng về cấu trúc dominance
của Test6 được ghi nhận ở §3.

---

## 1. Thiết kế Case D — hai lần thử sai trước khi tìm đúng cấu trúc

Ghi lại quá trình vì bản thân nó là một phát hiện: thiết kế phản ví dụ 2D đúng nghĩa hẹp
(dominance-giữa-chừng, `v_a=v_b`) khó hơn thiết kế 1D, vì cần **hai lịch sử khác nhau hội tụ về
đúng cùng một node ID** — không chỉ "gần giống nhau về toạ độ".

**Lần thử 1 (thất bại về mặt thiết kế, phát hiện được ngay khi viết docstring):** đặt D1, D2 ở
hai node khác nhau nhưng toạ độ gần trùng nhau (lệch 0,0001). Nhận ra ngay: dominance của Test6
(§1.2 spec) yêu cầu `v_a=v_b` theo **ID node**, không theo toạ độ — nên dù D1, D2 ở cùng một vị
trí vật lý gần như tuyệt đối, dominance kỹ thuật vẫn **không** áp dụng giữa 2 nhánh này (an toàn
tầm thường, không kiểm được gì có ý nghĩa).

**Lần thử 2 (thiết kế đúng):** cho O1 và O2 **cùng giao về một node vật lý chung** `DSHARED` —
hợp lệ trong model (một địa điểm có thể là điểm giao của nhiều đơn khác nhau qua nhiều lượt ghé).
Xác nhận bằng `brute_force()`: cả 6 thứ tự chèn hợp lệ của `{O1,O2}` đều kết thúc đúng tại
`DSHARED` — dominance giờ **thực sự** áp dụng giữa các nhánh, đúng nghĩa hẹp Sec2.3.

---

## 2. Số liệu Case D

```
X=(0,0). P1=(10,15) "nhánh +y". P2=(10,-15) "nhánh -y" (đối xứng qua trục x).
O1: P1 → DSHARED=(20,0).  O2: P2 → DSHARED=(20,0).
O3: P3=(26,16), D3=(34,18), deadline_p=36 (CHẶT).
```

**Bất đối xứng hình học cốt lõi (đã đo, không phải ước lượng):**
```
X→P1 = X→P2 = 18,028  (ĐỐI XỨNG — quãng đường tới bước đầu bằng nhau tuyệt đối)
P1→P3 = 16,031   (GẦN)
P2→P3 = 34,886   (XA gấp hơn 2 lần — phải "vòng qua" phía đối diện trục x)
```

**K/W của `{O1,O2}` (tính bằng brute_force, 4/6 thứ tự chèn ra kết quả giống hệt nhau):**
```
K=22,019, W=1,101  (4 thứ tự: pickup cả 2 trước, giao theo thứ tự bất kỳ)
K=24,037, W=1,202  (2 thứ tự: pickup-giao-pickup-giao tuần tự)
```
K/W của đa số nhánh **giống hệt nhau tuyệt đối** — đúng ý đồ thiết kế: dominance phải dựa vào
(K,W) thật đo được, không phải một chênh lệch ngẫu nhiên nào đó.

**Kết quả brute_force cho `{O1,O2,O3}`:** khả thi (9 thứ tự đầy đủ), và **toàn bộ 9 thứ tự đều
bắt đầu bằng pickup O1 hoặc pickup O3** — không một thứ tự nào bắt đầu bằng pickup O2. Đúng dự
đoán hình học: chỉ nhánh "đã ghé P1 sớm" mới đủ thời gian tranh thủ rẽ sang O3 trước deadline=36.

---

## 3. Kết quả kiểm — PASS tuyệt đối, cộng một phát hiện phụ có giá trị

```
Gate (Pareto front DP vs brute_force, giống Test6 Gate 1.A/B/C): PASS — 0 vi phạm
Kiểm §2.3-style (DP_full vs DP_prune, y hệt Test6.1 Việc 1): PASS — 0 vi phạm
DP_full: 75 label tạo ra | DP_prune: 60 label (giảm 20% — mức cắt vừa phải, không tầm thường)
Bundle hoàn chỉnh DP tìm được: bao gồm đúng {O1,O2,O3} — khớp brute_force
```

**Phát hiện phụ (không phải lỗi, ghi nhận vì có giá trị cho phần lý luận của thesis):** lần thử
1 ở trên (D1,D2 gần trùng toạ độ nhưng khác ID) cho thấy **dominance của Test6 miễn nhiễm về mặt
cấu trúc với đúng loại lỗ hổng đã hạ Test3/Test4** — không phải vì may mắn, mà vì định nghĩa
dominance (§1.2: yêu cầu `v_a=v_b` theo ID) chỉ bao giờ so sánh hai lịch sử đã hội tụ về **đúng
cùng một điểm vật lý thật** (không phải "gần giống nhau"). "Đường tắt ẩn dưới tóm tắt" — cơ chế
đã hạ Test3/Test4 — xảy ra khi so sánh 2 route ở 2 vị trí **khác nhau** dựa trên vài con số tóm
tắt (K, W, arrival); Test6 không bao giờ làm phép so sánh đó. Đây là một lý do cấu trúc (không
chỉ thực nghiệm) để tin dominance của Test6 an toàn hơn hẳn các dominance trước — nhưng **Case D
vẫn cần thiết**: nó xác nhận rằng ngay cả khi ép hai lịch sử hội tụ đúng nghĩa (điều kiện bắt
buộc để lỗ hổng geometric có cơ hội xảy ra), K/W tích luỹ qua cạnh chéo 2D vẫn được tính đúng và
dominance vẫn không mất bundle nào.

---

## 4. Kết luận

**Case D lấp đúng khoảng trống người dùng chỉ ra**: kiểm lại cơ chế "đường tắt hình học 2D" bằng
dữ liệu 2D thật (Euclid), độc lập với 3 case 1D của Test6.1, dominance-giữa-chừng đúng nghĩa hẹp
(hai lịch sử hội tụ về đúng cùng node ID). **PASS tuyệt đối** — không tìm thêm được phản ví dụ
nào. Kết hợp với phát hiện phụ ở §3 (dominance của Test6 miễn nhiễm cấu trúc với loại lỗ hổng
"tóm tắt che giấu vị trí thật"), **kết luận của Test6/Test6.1 được củng cố thêm một bậc**: không
chỉ "chưa tìm ra phản ví dụ" mà còn "có lý do cấu trúc để tin không tồn tại phản ví dụ dạng này".

Không có gì cần sửa trong `t6_dp.py`. Không hạ cấp bất kỳ kết luận nào của Test6/Test6.1.

---

## 5. File

| File | Nội dung |
|---|---|
| `experiments/T2BFS/t62_run_case_d.py` | Case D — `DistTable2D` (Euclid thật), `case_D_v2()` |

Không có violation nào để ghi vào CSV riêng — in trực tiếp ra console (PASS tuyệt đối ở cả 2
phép kiểm: Pareto front vs brute_force, và DP_full vs DP_prune). Thời gian chạy: <1 giây (case
D chỉ có 3 order, B=3).
