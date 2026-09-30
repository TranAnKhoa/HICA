# Report — K/W Unit Gate (new_02.md)

**Trạng thái: PASS tuyệt đối, kèm 1 quyết định thiết kế cần chốt (Việc 2).**
Chạy **trước** khi tiếp tục pipeline `new_01.md` (patch OD corridor bias), theo đúng yêu
cầu của spec — vì đổi generator (AREA_KM 20→8, corridor bias, tau grid mới) đồng nghĩa
sắp chạy lại hàng chục giờ tính toán, và một bug đơn vị kiểu Test6 (lệch 3× do
quy đổi phút↔km) sẽ âm thầm làm sai toàn bộ số liệu nếu không bắt trước.

File test: `spec_2a_2b/src/test_kw_units.py` (chạy bằng
`C:/Users/An Khoa/anaconda3/python.exe test_kw_units.py`, output tại
`spec_2a_2b/results/test_kw_units_stdout.txt`).

---

## Việc 0 — Xác nhận đơn vị chuẩn (đọc trực tiếp từ code, không đoán)

Xác nhận bằng cách đọc `t6_dp.py`, `t4_profile.py`, `instance_gen.py`:

```
travel_time(a,b)      -> PHÚT       (t2_gen.py / instance_gen.py quy ước)
SPEED_KMH              = 20.0        (hằng số DUY NHẤT, dùng ở CẢ 2 chiều quy đổi)
SERVICE_MIN            : field "s" của từng WNode — CỘNG vào W (thời gian), KHÔNG
                          cộng vào K (khoảng cách)
K (cost)                = kappa * distance_km, kappa = 1.0 (t4_profile.KAPPA = t6_dp.KAPPA)
W (billable time)       = active_time_phút / 60.0  (GW)
                          (detour_time_phút) / 60.0 (OD, trừ direct 1 lần lúc finalize)
```

Quy đổi phút↔km xuất hiện ở **2 chiều đối xứng, cùng 1 hằng số `SPEED_KMH=20.0`**:
- Chiều thuận (sinh `travel_time` từ tọa độ Euclid): `instance_gen.py:127`
  `_euclid_km(...)/SPEED_KMH*60.0`
- Chiều nghịch (suy `distance_km` từ `travel_time` để tính K): `t6_dp.py:101`
  (`_tt_to_km`) và `t4_profile.py:37` (`route_distance_km`), cả hai đều
  `tt_min * SPEED_KMH / 60.0`

**grep xác nhận** (`SPEED_KMH|/ 60|\* 60` trong `spec_2a_2b/src/`): mọi chỗ quy đổi đều
dùng đúng 1 hằng số `SPEED_KMH=20.0`, không có hằng số lệch (không còn dấu vết `30` hay
hằng số khác từng dùng minh họa trong spec). `feasibility_gate.py` **đọc lại**
`IG.SPEED_KMH` thay vì tự định nghĩa — không có bản sao lệch.

Không phải "1 hàm duy nhất" theo đúng nghĩa đen spec đề xuất (`travel_time_to_distance_km()`),
nhưng là **1 hằng số + 1 công thức duy nhất, áp dụng nhất quán ở mọi nơi** — kiểm chứng trực
tiếp bằng 4 test tính tay dưới đây khớp tuyệt đối với code thật, nên tương đương về mặt an
toàn với yêu cầu gate.

---

## Việc 1 — Unit test tính tay

Dùng trực tiếp `t6_dp.run_dp()` + `t6_dp.finalize_KW()` (không viết lại công thức) trên
instance dựng tay tối giản, số liệu **dùng đúng hằng số thật của code** (`SPEED_KMH=20.0`,
`kappa=1.0`) — không tự bịa `SPEED_KMH=30`/`kappa=0.5` như ví dụ minh họa trong spec, vì mục
tiêu là xác nhận đúng CODE THẬT, không phải một công thức trừu tượng.

### Test 1a — GW, 1 order

```
travel(start,pickup)=10p, travel(pickup,delivery)=20p, service=5p/điểm
tính tay: distance_km = 30*20/60 = 10km, K = 1.0*10 = 10.0
          W = (30 + 2*5)/60 = 0.666667 giờ
code trả: K=10.000000  W=0.666667   -> KHỚP TUYỆT ĐỐI
```
**PASS** (|ΔK| < 1e-6, |ΔW| < 1e-4)

### Test 1b — OD, detour dương cả K lẫn W

Bản đầu tiên dựng theo đúng ví dụ minh họa của spec (travel delivery→home=16p) cho
`detour_time>0` nhưng **`detour_distance=0`** (route 9.33km < direct 10km, bị `max(0,...)`
chặn) — đây **chính là loại "ví dụ tự dựng chưa hợp lý" mà spec cảnh báo trước**, phát
hiện được ngay khi tính tay, đúng tinh thần gate. Sửa lại: `delivery→home=24p` (thay vì
16p) để route dài hơn cả về khoảng cách lẫn thời gian:

```
route: O1->pickup=4p, pickup->delivery=8p, delivery->Dest1=24p, direct=30p
tính tay: route_dist=12km, direct_dist=10km -> detour_dist=2km -> K=2.0
          route_time=4+8+24+10(service)=46p, detour_time=46-30=16p -> W=0.266667
code trả: K=2.000000  W=0.266667   -> KHỚP TUYỆT ĐỐI
```
**PASS**

### Test 1c — service_time không bị tính nhầm vào K

```
route travel=0 (pickup=delivery=start, cùng tọa độ), chỉ có 2×service_time=5p
code trả: K=0.000000 (đúng - không di chuyển thì không tốn quãng đường)
          W=0.166667 = (2*5)/60 (đúng - service vẫn tính thời gian)
```
**PASS** — không có dấu hiệu cộng nhầm service_time (phút) vào phần tính K (cần km).

---

## Việc 2 — Thời gian chờ có tính vào W không? (câu hỏi mở, BẮT BUỘC phải chốt)

Dựng route driver đến sớm hơn `ready_time`, buộc phải chờ 40 phút trước khi bắt đầu
service:

```
travel(start,pickup)=10p, ready_time_pickup=50p -> chờ 40p (đến lúc t=10, phải đợi tới 50)
travel(pickup,delivery)=0p, service=5p/điểm
Giả thuyết A (chờ tính vào W): W = 60/60 = 1.000000
Giả thuyết B (chờ KHÔNG tính): W = 20/60 = 0.333333
code trả: W=1.000000
```

**KẾT LUẬN: W hiện tại BAO GỒM thời gian chờ.** Test khớp chính xác giả thuyết A, không
khớp giả thuyết B.

**Đây KHÔNG phải bug — là hành vi nhất quán và có chủ đích của code**: `t6_dp.py` cập
nhật `Bt = max(A, ready_time)` rồi `Dt = Bt + service`, và `label.t`/`label.W` được gán
trực tiếp bằng `Dt - t0` — tức "thời điểm hoàn tất" tích lũy, tự nhiên bao gồm mọi khoảng
chờ giữa các mốc. Không có chỗ nào trừ riêng phần chờ ra khỏi `W`.

**Quyết định thiết kế cần chốt vào tài liệu model (không để ngầm định):**
> W (billable time) = tổng thời gian tài xế bị "khóa" trong tuyến (từ lúc xuất phát tới
> lúc hoàn tất), bao gồm cả thời gian chờ do đến sớm hơn time-window của order. Đây là lựa
> chọn hợp lý về mặt kinh tế học chi phí cơ hội — tài xế không thể làm việc khác trong lúc
> chờ, nên thời gian chờ vẫn là chi phí thực. **Ghi nhận: mọi số liệu W trong toàn bộ dự án
> (Test4/5/6, spec_2a_2b, đo speedup thật) đều đã ngầm áp dụng định nghĩa này xuyên suốt —
> không có mâu thuẫn giữa các phần, chỉ là điểm chưa từng được viết tường minh.**

Không cần sửa code. Cần thêm dòng trên vào tài liệu mô hình chính thức (§2.2 đề cương,
ngoài phạm vi repo này) trước khi nộp thesis.

---

## Việc 3 — Có bao nhiêu nơi tính K/W độc lập?

`grep -rn "K_ir\|K =\|W_ir\|W =" spec_2a_2b/src/`:

| File | Vai trò | Có phải 1 công thức độc lập khác không? |
|---|---|---|
| `t6_dp.py` (`finalize_KW`) | **Nguồn duy nhất** dùng bởi pipeline (qua `dp_labeling.run_pool`) | — |
| `dp_labeling.py` | Chỉ **gọi lại** `D.finalize_KW()`, không tính lại | Không — dùng chung nguồn |
| `brute_force.py` | Oracle **độc lập có chủ đích** cho Gate 0 (đối chiếu DP) | Có, nhưng ĐÚNG MỤC ĐÍCH (không phải rủi ro — là thiết kế gate) |
| `viec_extra_real_wdp_speedup.py` (`convert_to_t8_format`) | Đọc `K_min = min(K for K,W in kw_list)` **trực tiếp từ Pareto front đã có** | Không — đây là READ, không phải công thức thứ 2. `W` bị bỏ qua có chủ đích, đã ghi rõ trong code (WDP ở đây không mô hình bid `b`) |

Không phát hiện điểm nào tính lại K/W bằng công thức riêng biệt ngoài `brute_force.py`
(đúng vai trò oracle độc lập của Gate 0) — không cần test so khớp chéo bổ sung.

---

## Ngưỡng chạy pipeline lớn — đối chiếu

```
✅ Test 1a, 1b (đã sửa ví dụ hình học), 1c: PASS tuyệt đối
✅ Việc 2: đã chốt tường minh — W BAO GỒM thời gian chờ (không phải bug, cần ghi vào model doc)
✅ Việc 3: chỉ 1 nguồn K/W dùng bởi pipeline; nơi khác hoặc là oracle độc lập có chủ đích
   (brute_force.py) hoặc chỉ đọc lại (viec_extra_real_wdp_speedup.py)
✅ grep xác nhận: 1 hằng số SPEED_KMH=20.0 duy nhất, áp dụng nhất quán 2 chiều
```

**Tất cả 4 mục đạt → được phép tiếp tục `run_gate0.py` → `run_2a.py` → ... theo đúng
guideline patch OD (`new_01.md`) đang thực hiện.**
