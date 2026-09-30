# Report — Đo speedup THẬT bằng WDP thật (CPLEX), đóng câu hỏi cuối cùng của T5

**Ngày chạy:** 2026-09-12. **Người thực thi:** Claude Code, theo yêu cầu bổ
sung của người dùng sau khi đọc `report_2a_2b_full.md`. **Mục đích:** trả
lời câu hỏi duy nhất còn treo — *"WDP thật sự phân bổ winner theo kiểu nào
— (a) tỷ lệ thuận, (c) dồn vào cụm lớn nhất, hay (d) toàn driver đơn lẻ?"*
— bằng cách chạy Algorithm B (CPLEX 12.10, hạ tầng Test8) thật trên 3
instance đại diện, thay vì tiếp tục ước lượng đại số.

**Trạng thái một câu:** Speedup THẬT đo được là **~0.93–0.98× (KHÔNG có
speedup, thậm chí hơi chậm hơn)** ở cả 3 instance — thấp hơn NHIỀU so với
mọi kịch bản ước lượng đại số ở `report_2a_2b_full.md` (khoảng 1.9×–50×).
Nguyên nhân **không phải do component "xấu"** như giả thuyết ban đầu, mà là
một **phát hiện phương pháp luận mới, quan trọng hơn**: **81.8% driver OD
trong toàn bộ dữ liệu 2b không có route khả thi nào** (pool rỗng) — route
pool chỉ gồm driver GW, và driver GW LUÔN nằm gọn trong đúng 1 component
duy nhất (không có OD nào để "phá vỡ" nó ra). Nhân dịp này cũng phát hiện
và sửa 1 bug kỹ thuật: `hash()` của Python không ổn định xuyên tiến trình,
khiến các script trước đó dùng seed không tái tạo được đúng như đã ghi.

---

## 1. Thiết lập

Tái dùng NGUYÊN VẸN `t8_cplex.py` (Test8 — `build_model`, `solve_wdp`,
`naive_all`, `decomposed_all`, `build_conflict_graph`, `connected_components`)
— KHÔNG sửa. Viết mới `viec_extra_real_wdp_speedup.py`:

1. **Sinh lại route pool thật** cho 3 instance đại diện bằng
   `instance_gen.py` + `dp_labeling.py` (cùng hạ tầng đã dùng cho 2a/2b).
2. **Chuyển đổi sang định dạng Test8**: mỗi bundle `(K,W)` Pareto của 1
   driver → 1 route với `cost = K` (điểm Pareto có K nhỏ nhất — κ=1, KHÔNG
   dùng bid, đúng tinh thần DSIC "không đọc bid trong route generation").
   `fd_cost[o] = 1.3 × route rẻ nhất phủ order đó` (giả định thiết kế công
   khai, vì 2b chưa mô hình FD).
3. **Giải WDP thật** (`solve_wdp` full instance) → lấy winner THẬT (không
   phải giả định).
4. **Đo speedup thật**: `naive_all` (giải lại WDP-{i} trên CẢ instance cho
   từng winner) vs `decomposed_all` (giải trên từng component) — đúng công
   thức Test8 §2, đối chiếu `max|Z_naive - Z_decomp|` làm gate đúng đắn.

3 instance đại diện (chọn theo `largest_component_fraction` từ thấp đến
cao, cùng tinh thần "tốt/trung bình/xấu" người dùng đề xuất):

| Case | n | tau | mode | supply_ratio | seed | n_components | largest_frac |
|---|---|---|---|---|---|---|---|
| tot | 30 | 10 | dispersed | 0.3 | 0 | 6 | 0.444 |
| trungbinh | 30 | 30 | dispersed | 0.3 | 6 | 5 | 0.556 |
| xau | 50 | 60 | dispersed | 0.3 | 4 | 1 | 1.000 |

## 2. Phát hiện kỹ thuật quan trọng (phải sửa trước khi tin bất kỳ số nào)

### 2.1 Bug: `hash()` không ổn định xuyên tiến trình

Toàn bộ `run_2a.py`/`run_2b.py`/`run_2b_B2.py`/`probe_scaling.py`/
`run_gate0.py` dùng `gen_seed = hash((n, tau, mode, sr, seed, "spec2b")) &
0x7FFFFFFF` để sinh seed tái tạo. **`hash()` của Python trên tuple chứa
string bị RANDOMIZE theo tiến trình** (PYTHONHASHSEED, mặc định từ Python
3.3) — xác nhận thực nghiệm: `hash(('a','b'))` cho 2 giá trị KHÁC NHAU ở 2
lần gọi `python -c "..."` khác nhau.

**Hệ quả:** mọi tuyên bố "tái tạo được instance từ seed đã ghi" trong
`report_2a_2b.md`, `report_2a_2b_full.md` (mục "File & tái tạo") **không
đúng** — không process nào có thể tái sinh CHÍNH XÁC instance đã dùng trong
1 dòng cụ thể của `2a_summary.csv`/`2b_summary.csv` từ 1 tiến trình Python
mới. **Thống kê TỔNG HỢP của các báo cáo trước KHÔNG bị ảnh hưởng** (mỗi ô
lưới vẫn dùng 1 seed cố định xuyên suốt 1 lần chạy, không có lẫn lộn giữa
các ô trong cùng 1 lần chạy) — chỉ có khả năng "quay lại xem instance A đã
cho ra số X" là không dùng được.

**Sửa:** `viec_extra_real_wdp_speedup.py` dùng `stable_seed()` (dựa
`hashlib.sha256`, ổn định xuyên tiến trình, đúng mẫu đã dùng trong
`t6_run_gate1.seed_from()`). 3 instance đại diện ở đây dùng seed ỔN ĐỊNH
MỚI (không phải seed cũ trong `2b_raw/*.json`, vì seed cũ không tái tạo
được) — đã quét seed=0..9 trên đúng bộ tham số (n,tau,mode,sr) và CHỌN LẠI
seed cho mỗi case để cấu trúc component trải đều thấp→cao (không tin mù
seed=0 sẽ cho đúng cấu trúc như bảng tổng hợp cũ).

### 2.2 Phát hiện quan trọng hơn: 81.8% driver OD không có route nào

```
Quét toàn bộ pool_sizes_by_driver trong 720 file 2b_raw/*.json:
  OD: 7,456 / 9,120 driver-slot (81.8%)  CO POOL RONG (0 route)
  GW: 0     / 9,120 driver-slot (0.0%)   luon co pool (thuong hang nghin route)
```

**Nguyên nhân:** `instance_gen.py` (viết mới cho spec_2a_2b, KHÁC
`t2_gen.py` gốc) đặt pickup/delivery của OD **rải ngẫu nhiên toàn bộ hộp
20×20km** (giống GW) — không có cơ chế "corridor bias" (ưu tiên đặt gần
đoạn thẳng start→home) mà `t2_gen.py` đã phải thêm vào từ Test3 Việc 1 để
sửa đúng lỗi này (`CORRIDOR_BUFFER_KM`/`CORRIDOR_SHARE`, ghi rõ trong
`t2_gen.py` dòng 48-58: *"feasibility_rate_k1 của OD vẫn dưới 50% ở
tau=15/30 (3.9%/17.2%)... do P/D sinh random toàn vùng, không quanh
corridor"*). `instance_gen.py` của spec_2a_2b **không kế thừa fix này** —
với `deadline_home = t0 + direct_time + tau` (tau chỉ 10-60 phút) và pickup/
delivery đặt xa corridor, hầu hết route OD vi phạm deadline_home, dẫn đến
route pool rỗng.

**Hệ quả cho MỌI kết luận Hướng (B) trước đó:** conflict graph trong toàn
bộ 2a/2b/addition_1/full **thực chất chỉ phản ánh cấu trúc route pool của
GW** — OD gần như luôn là "singleton" trong graph không phải vì route của
họ tách rời về mặt logic, mà vì **họ không có route nào để tạo cạnh**. Điều
này KHÔNG làm sai kết luận Hướng (B) (GW thật sự luôn gộp thành 1 cụm lớn
duy nhất — xem §3), nhưng làm **thay đổi hoàn toàn cách đọc con số
`largest_component_fraction`**: con số 0.44-1.00 đo được trước đây không
phải "có nhiều cụm vừa phải + 1 cụm lớn" như đọc ban đầu, mà là **"1 cụm GW
lớn duy nhất + (n_drivers - n_gw) node OD cô lập vô nghĩa về mặt tính
toán"**.

## 3. Kết quả speedup THẬT — không đảo ngược Hướng B, nhưng đảo ngược MỨC ĐỘ

| Case | Z* (WDP that) | n_winners | n_components | largest_frac | speedup_wall | speedup_det | gate \|Δ\| |
|---|---|---|---|---|---|---|---|
| tot | 489.64 | 4 | 6 (1 GW-cụm + 5 OD-rỗng) | 0.444 | **0.953×** | 0.993× | 2.27e-13 |
| trungbinh | 478.64 | 5 | 5 (1 GW-cụm + 4 OD-rỗng) | 0.556 | **0.983×** | 1.001× | 1.14e-13 |
| xau | 562.12 | 10 | 1 (toàn bộ GW) | 1.000 | **0.931×** | 0.993× | 1.14e-13 |

**Gate đúng đắn (Test8 §2.3):** `max|Z_naive - Z_decomposed|` ≤ 2.27e-13 ở
cả 3 case — decomposition vẫn **ĐÚNG** (khớp Test7's kết luận), chỉ không
**NHANH HƠN**.

**Cơ chế chính xác (đã xác minh bằng cách in ra số route mỗi component):**

```
tot:        comp0 (4 GW, 18100 route) + 5 comp OD-rong (0 route/comp)
trungbinh:  comp0 (5 GW, 18101 route) + 4 comp OD-rong (0 route/comp)
xau:        comp0 (15 GW, 167010 route)   <- CHI 1 component, khong co gi de tach
```

Ở cả 3 case, **toàn bộ 4/5/10 winner đều là driver GW** (vì OD không có
route để thắng), và **tất cả winner GW đều rơi vào ĐÚNG 1 component** (cái
duy nhất chứa mọi route GW). Vì vậy:

- Với "tot"/"trungbinh": decomposition về lý thuyết CÓ 5-6 "component"
  nhưng chỉ 1 component có ý nghĩa tính toán (chứa hết winner) — bước
  `decomposed_all` vẫn phải giải sub-instance đúng bằng KÍCH THƯỚC route
  pool GW gốc (18,100 route), CỘNG THÊM chi phí xây conflict graph
  (`t_step1`) — nên **chậm hơn naive một chút**, không nhanh hơn.
- Với "xau": chỉ có 1 component tồn tại — decomposition về bản chất **là
  chính bài toán gốc**, cộng thêm overhead xây graph vô ích.

**Đây chính là kịch bản (c) worst-case của Việc 1 mở rộng, nhưng CỰC ĐOAN
HƠN cả (c) dự đoán** — (c) giả định "toàn bộ winner dồn vào cụm lớn nhất"
và ước lượng speedup ~1.9× (p=1); thực tế đo được ~0.93-0.98×, tức là
**còn tệ hơn cả kịch bản xấu nhất đã ước lượng bằng đại số** — bởi vì ước
lượng đại số Việc 1 dùng mô hình `cost ~ size^p` (giả định chi phí giải tỷ
lệ với LŨY THỪA kích thước), trong khi CPLEX thực tế có overhead cố định
(xây model, khởi tạo solver) không giảm khi kích thước sub-problem giảm
nhẹ — và ở đây sub-problem của "component chứa winner" hầu như KHÔNG giảm
kích thước so với instance gốc (vì đó là component duy nhất có routes).

## 4. Kết luận — SỬA LẠI khuyến nghị của `report_2a_2b_full.md`

**Câu hỏi đã được trả lời dứt điểm:** WDP thật **không** phân bổ winner
theo kịch bản (a)/(d) lạc quan — nó rơi đúng vào kịch bản gần với (c)
worst-case, thậm chí tệ hơn, vì cấu trúc route pool thật (GW luôn gộp 1
cục, OD gần như luôn rỗng) không cho decomposition cơ hội tách bất cứ thứ
gì có ý nghĩa.

**Khuyến nghị #2 của `report_2a_2b_full.md` cần SỬA LẠI** (không còn giữ
nguyên câu chữ "giá trị speedup thực nghiệm... 1.9× đến 18-50×"):

> *"T5 (component decomposition) đúng đắn (Test7, |Δ|=0; xác nhận lại ở
> đây với gate \|Z_naive-Z_decomp\|≤2.3e-13) nhưng KHÔNG mang lại speedup
> thực trên route pool thật đo được từ DP label-setting: 3 instance đại
> diện (τ thấp/trung/cao, cấu trúc component từ 0.44 đến 1.00) đều cho
> speedup ~0.93-0.98× — TƯƠNG ĐƯƠNG HOẶC CHẬM HƠN naive. Nguyên nhân không
> phải do 'cấu trúc component xấu' theo nghĩa lý thuyết, mà do một ràng
> buộc CỤ THỂ của instance sinh bởi `instance_gen.py`: driver OD hầu như
> luôn có route pool RỖNG (81.8% qua 720 instance), khiến toàn bộ winner
> luôn là driver GW, và driver GW luôn nằm gọn trong ĐÚNG 1 component. Con
> số speedup lớn của Test8 (14.9-391×) đo trên cấu trúc component NHÂN
> TẠO, tách rời TUYỆT ĐỐI theo thiết kế (t8_gen.make_instance) — không đại
> diện cho route pool thực tế của thuật toán sinh route (T6 DP) trên
> instance ngẫu nhiên."*

**Khuyến nghị bổ sung mới:**
1. **Nếu muốn T5 có cơ hội speedup thật**, cần trước tiên sửa
   `instance_gen.py` để OD có route khả thi (kế thừa corridor-bias của
   `t2_gen.py`, hoặc nới τ) — ĐÂY LÀ ĐIỀU KIỆN TIÊN QUYẾT, không phải việc
   phụ. Nếu không, driver OD không bao giờ đóng góp vào route pool/conflict
   graph, và kết luận Hướng B (dù đúng về mặt dữ liệu) đang dựa trên 1 nửa
   loại driver (chỉ GW) một cách không chủ ý.
2. **Không cần đo lại thêm — 3 instance đã đủ nhất quán** (0.93-0.98× ở cả
   3, biên độ hẹp, cơ chế rõ ràng và xác minh được bằng cách in route/
   component) để kết luận: trên route pool THẬT hiện tại (với bug OD ở
   trên), T5 **không có giá trị speedup thực nghiệm nào đáng kể** — khuyến
   nghị cuối cùng cho thesis nên là "correctness result" (đúng như Hướng B
   dự đoán ban đầu), **không phải** "giá trị có điều kiện 2-4× đến 18-50×"
   như bản `report_2a_2b_full.md` viết dựa trên ước lượng đại số.
3. **Sửa `main_guideline.md` §3 (T5)** một lần nữa: nhãn cuối cùng nên là
   **"[VALIDATED — correctness only]"**: đúng đắn (Test7 + gate ở đây) xác
   nhận vững; giá trị speedup (Test8) chỉ đúng trên cấu trúc component nhân
   tạo, KHÔNG tái hiện được trên route pool thật (đo trực tiếp ở đây, không
   phải ước lượng).

---

## File & tái tạo

```
spec_2a_2b/src/viec_extra_real_wdp_speedup.py   script chinh, import t8_cplex
                                                  NGUYEN VEN (khong sua)
spec_2a_2b/results/viec_extra_real_wdp_speedup.json   ket qua chi tiet 3 case
```

Chạy bằng Python 3.7.7 (bat buoc vi CPLEX binding):
```
"C:\Users\An Khoa\AppData\Local\Programs\Python\Python37\python.exe" \
    spec_2a_2b\src\viec_extra_real_wdp_speedup.py
```

Seed 3 case dùng `stable_seed()` (hashlib.sha256, ổn định) — KHÁC seed
`hash()` không ổn định của các script `run_2a.py`/`run_2b.py` cũ (xem §2.1).
Instance CÓ THỂ tái tạo chính xác từ file này (không như các báo cáo trước).
