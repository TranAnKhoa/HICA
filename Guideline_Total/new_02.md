# Gate bắt buộc — Kiểm tra đơn vị K/W trước khi chạy lại pipeline (đã sửa OD + lưới tau mới)

## Vì sao gate này bắt buộc, và bắt buộc chạy TRƯỚC pipeline lớn

Đã có tiền lệ: Test6 từng có bug lệch đúng 3.0× vì `travel_time()` trả về phút nhưng
công thức tính K lại cần km — không phát hiện được cho tới khi Gate 1.B/1.C bắt được ở
mức instance nhỏ. Sắp tới sẽ chạy lại pipeline tốn nhiều giờ với generator mới (đã sửa
OD feasibility, lưới tau mới {30,45,60}) — nếu bug đơn vị kiểu này còn sót hoặc tái phát
ở code mới, toàn bộ vài chục giờ chạy sẽ cho ra số liệu sai mà không ai biết cho tới khi
đọc kết quả và thấy vô lý.

**Nguyên tắc:** không tin bất kỳ dòng code nào tính K/W cho tới khi có unit test tính tay
khớp tuyệt đối. Đây là gate rẻ (chạy vài giây), làm trước, không phải làm sau khi nghi
ngờ.

---

## Việc 0 — Xác định rõ và viết thành comment ngay đầu file tính K/W

Trước khi viết bất kỳ test nào, xác nhận và ghi rõ bằng comment trong code (không chỉ
trong đầu):

```python
# ĐƠN VỊ CHUẨN CỦA TOÀN BỘ MODULE:
# - travel_matrix[i][j]  : phút  (thời gian di chuyển thô, KHÔNG phải khoảng cách)
# - distance_matrix[i][j]: km    (nếu có ma trận riêng; nếu không, suy ra từ travel_matrix)
# - SPEED_KMH            : km/h (hằng số quy đổi, dùng CHỈ để suy ra distance từ travel_time
#                           khi không có distance_matrix riêng)
# - SERVICE_MIN           : phút (thời gian xử lý tại 1 điểm, CỘNG vào W, KHÔNG cộng vào K)
# - K (cost)               : cost-unit = kappa * distance_km   (kappa: cost-unit/km)
# - W (billable time)       : GIỜ = (travel_min + service_min, KHÔNG gồm thời gian chờ) / 60
```

Nếu hiện tại KHÔNG có `distance_matrix` riêng (theo đúng thực tế bạn vừa nêu — chỉ có
travel_matrix theo thời gian), bắt buộc phải có một hàm suy ra khoảng cách **tường minh**,
không được để phép tính "km từ phút" nằm rải rác nhiều chỗ trong code:

```python
def travel_time_to_distance_km(travel_minutes: float, speed_kmh: float) -> float:
    """DUY NHẤT một chỗ trong toàn bộ codebase làm phép quy đổi phút -> km.
    Mọi nơi khác PHẢI gọi hàm này, không tự viết lại công thức."""
    return travel_minutes * speed_kmh / 60.0
```

**Kiểm tra bằng bash/grep:** tìm mọi chỗ trong code có `* SPEED` hoặc `/ 60` hoặc phép
nhân/chia liên quan tới quy đổi thời gian-khoảng cách — nếu có chỗ nào KHÔNG gọi qua hàm
duy nhất này, đó là điểm nguy cơ lặp lại bug 3× kiểu Test6 (một chỗ tính đúng, một chỗ
quên nhân/chia, ra lệch đúng hệ số SPEED_KMH hoặc 60).

---

## Việc 1 — Unit test tính tay, route đơn giản nhất có thể (1 điểm)

### Test 1a — GW, route chỉ có 1 order

Dựng tay 1 instance tối giản, mọi con số chọn tròn để tính nhẩm được:

```
start_node -> pickup(o1) -> delivery(o1)
travel(start, pickup)   = 10 phút
travel(pickup, delivery)= 20 phút
SERVICE_MIN             = 5 phút (mỗi điểm)
SPEED_KMH                = 30 km/h
kappa                    = 0.5 cost-unit/km
KHÔNG có chờ (ready_time đủ sớm, không kích hoạt max(...) chờ)
```

**Tính tay trước, ghi ra giấy/comment, KHÔNG chạy code trước:**

```
total_travel_min = 10 + 20 = 30 phút
distance_km       = 30 * (30/60) = 15 km        <- dùng travel_time_to_distance_km
K_tay              = 0.5 * 15 = 7.5 cost-unit
W_tay               = (30 phút travel + 2*5 phút service) / 60 = 40/60 = 0.6667 giờ
```

**Chạy code, so sánh:**

```python
def test_1a_single_order_gw():
    K_code, W_code = compute_KW_for_route(route=[...])  # route dựng tay ở trên
    assert abs(K_code - 7.5) < 1e-6, f"K sai: {K_code} != 7.5"
    assert abs(W_code - 0.6667) < 1e-4, f"W sai: {W_code} != 0.6667"
```

Nếu lệch đúng theo hệ số 30 (SPEED_KMH) hoặc 60 (phút→giờ) hoặc 2 (double-count gì đó) —
đây chính xác là dấu hiệu bug kiểu Test6, dò ngay theo hệ số lệch, không đoán mò.

### Test 1b — OD, có trừ direct trip (đây là công thức DỄ NHẦM NHẤT — kiểm kỹ hơn)

```
c1: start=O1, home=Dest1
direct_distance = 10 km, direct_time = 30 phút   (đi thẳng O1 -> Dest1, không detour)
Route thật: O1 -> pickup(o1) -> delivery(o1) -> Dest1
travel(O1, pickup)         = 4 phút
travel(pickup, delivery)    = 8 phút
travel(delivery, Dest1)      = 6 phút
SERVICE_MIN = 5 phút/điểm, SPEED_KMH=30, kappa=0.5
```

**Tính tay:**

```
route_total_time_min = 4 + 8 + 6 + 2*5(service) = 28 phút
route_total_distance_km = (4+8+6) * (30/60) = 9 km   <- CHỈ quy đổi phần travel, KHÔNG
                                                          quy đổi phần service (service
                                                          không di chuyển, không tính km)

detour_distance = max(0, route_total_distance_km - direct_distance)
                = max(0, 9 - 10) = 0        <- route ngắn hơn cả direct?? xem cảnh báo dưới
detour_time     = max(0, route_total_time_min - direct_time)
                = max(0, 28 - 30) = 0
```

**⚠️ Cảnh báo quan trọng phát hiện ngay từ ví dụ tính tay này:** nếu route thật (có ghé
2 điểm) lại có tổng **thời gian di chuyển thô** ngắn hơn cả đi thẳng, đó là dấu hiệu ví
dụ dựng tay chưa hợp lý về mặt hình học (ghé 2 điểm không thể nhanh hơn đi thẳng, trừ khi
2 điểm đó nằm đúng trên đường thẳng). **Sửa lại ví dụ cho hợp lý hình học trước khi dùng
làm test** — ví dụ đổi `travel(delivery, Dest1) = 16 phút` để tổng = 4+8+16+10(service)=38
phút, khi đó `detour_time = 38-30 = 8 phút > 0`, mới là ví dụ có ý nghĩa kiểm tra công
thức `max(0, ...)`. Đây chính là loại sai sót dễ mắc khi tự dựng test tay — bản thân việc
phát hiện ra ví dụ vô lý này là một phần giá trị của gate, không phải điều cần bỏ qua.

**Sau khi sửa ví dụ hợp lý, tính lại tay, rồi mới viết assert — không viết assert trước
khi chắc chắn số tính tay hợp lý về mặt hình học.**

```python
def test_1b_od_detour_positive():
    # dùng ví dụ ĐÃ SỬA cho detour > 0
    K_code, W_code = compute_KW_for_route_OD(route=[...], direct_distance=10, direct_time=30)
    assert abs(K_code - K_tay_da_sua) < 1e-6
    assert abs(W_code - W_tay_da_sua) < 1e-4
```

### Test 1c — Kiểm riêng: service_time có bị tính nhầm vào distance không

Đây là kiểm tra hẹp, trực tiếp nhắm vào loại lỗi "cộng nhầm phút-service vào chỗ cần km":

```python
def test_1c_service_time_not_counted_as_distance():
    # Route chỉ có travel = 0 (2 điểm trùng vị trí), chỉ có service_time
    # Nếu code tính đúng: K phải = 0 (không di chuyển = không tốn quãng đường)
    #                      W phải > 0 (vẫn tốn thời gian xử lý)
    route = make_route(travel_times=[0, 0], service_min=5, n_stops=2)
    K, W = compute_KW_for_route(route)
    assert abs(K - 0.0) < 1e-6, "K phải bằng 0 khi không di chuyển, dù có service_time"
    assert W > 0, "W phải > 0 vì service_time vẫn tính, dù K=0"
```

Nếu `K > 0` ở test này → có chỗ nào đó đang cộng nhầm service_time (phút) vào phần tính
K (cần km) — bắt được lỗi sớm, chính xác vào đúng cơ chế của loại bug đã từng xảy ra.

---

## Việc 2 — Kiểm tra "thời gian chờ" có bị tính nhầm vào W không

Đây là câu hỏi mở đã nêu ở phần giải thích trước — cần chốt bằng test, không chốt bằng
lời nói.

```python
def test_2_waiting_time_excluded_from_W():
    """
    Dựng route mà driver ĐẾN SỚM hơn ready_time của order kế tiếp, buộc phải chờ.
    ready_time(next) = 100
    arrival tự nhiên nếu đi ngay = 60  ->  phải chờ 40 phút trước khi service bắt đầu
    """
    route = make_route_with_forced_wait(wait_minutes=40, travel_before_wait=60,
                                          service_min=5)
    K, W = compute_KW_for_route(route)
    # W CHỈ được cộng travel + service, KHÔNG cộng 40 phút chờ
    W_expected_hours = (60 + 5) / 60.0   # KHÔNG cộng 40
    assert abs(W - W_expected_hours) < 1e-4, (
        f"W={W} có vẻ đã cộng nhầm thời gian chờ. "
        f"Kỳ vọng {W_expected_hours} nếu chờ KHÔNG tính vào W."
    )
```

**Nếu test này FAIL** (tức code hiện tại đang cộng cả thời gian chờ vào W) — đây là một
**quyết định thiết kế cần chốt tường minh**, không phải mặc định để vậy: hỏi lại chính
mình "tài xế có nên được trả tiền cho lúc đứng chờ không?" — nếu câu trả lời là CÓ (hợp
lý nếu chờ cũng là một dạng chi phí cơ hội), thì sửa lại toàn bộ tài liệu model
(§2.2 trong đề cương) để ghi rõ W bao gồm cả thời gian chờ, và bug này thực ra không phải
bug mà là hành vi đúng — nhưng phải quyết định và ghi rõ, không để ngầm định không rõ
ràng cho tới khi báo cáo kết quả.

---

## Việc 3 — Kiểm nhất quán giữa Algorithm A (sinh route) và bất kỳ nơi nào khác dùng lại K/W

Nếu có code ở nơi khác (ví dụ Algorithm B/WDP, hoặc script đo speedup CPLEX) tự tính lại
K/W từ route thay vì đọc từ output của Algorithm A — đây là nguy cơ **2 công thức khác
nhau cho cùng 1 đại lượng**, dễ lệch nếu sửa một chỗ quên sửa chỗ kia.

```bash
grep -rn "K_ir\|K =" --include="*.py" spec_2a_2b/src/ | grep -v "test_"
grep -rn "W_ir\|W =" --include="*.py" spec_2a_2b/src/ | grep -v "test_"
```

Liệt kê mọi nơi tính K hoặc W — nếu có nhiều hơn 1 hàm độc lập làm việc này (không phải
gọi lại cùng 1 hàm dùng chung), viết thêm 1 test so sánh chéo: cùng 1 route, gọi cả 2 nơi,
kết quả phải khớp tuyệt đối. Đây chính là bug đã gặp ở phần "đo speedup thật" — script đó
tự chuyển đổi định dạng route sang cho CPLEX, là đúng một điểm nguy cơ kiểu này.

---

## Ngưỡng để được phép chạy pipeline lớn

```
✅ Test 1a, 1b (đã sửa ví dụ hợp lý hình học), 1c: PASS tuyệt đối (sai số < 1e-6 cho K, < 1e-4 cho W)
✅ Test 2: PASS hoặc FAIL-nhưng-đã-quyết-định-tường-minh (ghi rõ vào model doc)
✅ Việc 3: mọi nơi tính K/W đã xác nhận dùng chung 1 nguồn, hoặc có test so khớp chéo PASS
✅ grep xác nhận CHỈ có 1 hàm làm phép quy đổi phút->km trong toàn bộ codebase
```

Chỉ khi cả 4 mục trên đều xanh mới bắt đầu chạy `run_gate0.py` → `run_2a.py` → ... như
guideline patch OD đã định.

---

## Việc KHÔNG được làm

- Không viết test rồi chỉnh số "tính tay" ngược lại cho khớp với code hiện tại — phải
  tính tay ĐỘC LẬP trước, dựa trên định nghĩa model (§2.2 đề cương), rồi mới so với code.
  Nếu lệch, sửa CODE, không sửa lại số tính tay cho khớp.
- Không bỏ qua Test 1c vì "chắc không sao đâu" — đây là test rẻ nhất, nhanh nhất, và
  nhắm thẳng vào đúng cơ chế bug đã từng xảy ra thật.
- Không để Việc 2 (thời gian chờ) ở trạng thái "không rõ" — phải chốt 1 trong 2 hướng
  và ghi vào tài liệu model, vì đây ảnh hưởng trực tiếp đến số W dùng trong mọi tính toán
  sau này.
