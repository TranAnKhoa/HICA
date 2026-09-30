# main_guideline.md — Bản đồ tiến độ & code cho agent tiếp theo

**Mục đích của file này:** một agent Claude mới đọc file này (cùng `Master_Thesis_Q1.md`) là
nắm được: (a) thesis đang cần chứng minh cái gì, (b) hai contribution kỹ thuật T4/T5 đang ở
đâu, (c) **file code nào đã tồn tại và test xong** để tái dùng chứ không code lại.

**Ngày cập nhật:** 2026-09-10. **Trạng thái một câu:** T5 (component decomposition) vừa PASS
Test8 trên CPLEX 12.10 thật → đã đủ làm trụ cột novelty. T4 (cận đơn điệu open-route) vẫn OPEN
nhưng T6 (forward label-setting DP) là một kết quả mạnh có thể thay thế Algorithm A.

---

## 0. Cấu trúc thư mục cần biết

| Đường dẫn | Nội dung |
|---|---|
| `Master_Thesis_Q1.md` | Đề cương v4. Đọc §4 (điều KHÔNG được claim), §5 (3 ứng viên contribution), §7.3 (T4), §9.3 (T5), §10 (theorem package). |
| `guideline_paper_summarize.md` | Tóm tắt các paper nền (Li & Zhang, Zou & Kafle, Luy et al., ...). |
| `Guideline/` | Spec + report cho **Algorithm A branch** (T4/T6): `Test1..Test6.2`. |
| `Guideline/HICA-S Algorithm A.md` | **Tài liệu tham chiếu đã kiểm chứng** cho Algorithm A — nhãn [PROVEN]/[VALIDATED]/[REJECTED]/[OPEN]. Đọc trước khi đụng T4. |
| `Guideline_A2/` | Spec + report cho **Algorithm B/C branch** (T5): `Test7`, `Test8`. |
| `experiments/T2BFS/` | **Toàn bộ code Test2–Test8** (Python thuần + CBC/CPLEX). Xem §4 dưới. |
| `experiments/T4/` | Code T4 chạy trên dataset Atlanta ARC thật (khác nhánh với T2BFS — xem memory `atlanta-dataset-t4`). |
| `Src_Cplex/` | Model OPL `.mod` + `cmain.py` (gọi `oplrun.exe`). Dùng cho pipeline VCG gốc, KHÔNG dùng cho Test7/8. |
| `Output/Test{2..6}/` | CSV kết quả từng test. |
| `Dataset/` | Instance Atlanta ARC + instance Cplex. |

---

## 1. Bài toán & ba thuật toán (rút gọn từ Master_Thesis_Q1 §0, §7–9)

Platform sinh route-bundle từ order nguyên tử cho **GW** (gigworker, open route) + **OD**
(occasional driver, kết thúc tại home, có detour budget), chọn allocation, trả **exact VCG
payment**. **FD** (fixed capacity) là outside option giá công khai `q_o`.

- **Algorithm A** — Bounded Route Generation. Sinh **đầy đủ** mọi feasible route `|S| ≤ B`,
  **không đọc bid**. Đây là nơi GW và OD khác nhau về mặt toán học (OD có anchor để cắt nhánh,
  GW không). → **T4** = tìm cận đơn điệu rẻ cho open-route.
- **Algorithm B** — Exact Winner Determination. MILP set-partitioning: `min Σ(K_ir+b_i·W_ir)x_ir
  + Σ q_o·z_o` s.t. mỗi order phủ đúng 1 lần, mỗi driver ≤ 1 route.
- **Algorithm C** — Exact Clarke-Pivot Payments. Với mỗi winner `i`: `p_i = c_i(x*) + Z*_{-i} −
  Z*`, trong đó `Z*_{-i}` = giải lại WDP sau khi disable toàn bộ route của `i`. → **T5** =
  component decomposition để `Z*_{-i}` giải trên sub-instance thay vì toàn bộ.

**Cần ít nhất MỘT trong T4/T5 thành công** (Master §10). Hiện trạng: **T5 đã có tín hiệu mạnh
(Test8)**, T6 là backup mạnh cho nhánh A.

---

## 2. T4 — Cận đơn điệu cho open-route bundle generation (nhánh Algorithm A)

**Trạng thái: [OPEN] cho đúng câu hỏi T4, nhưng [VALIDATED] một giải pháp thay thế (T6 DP).**

### Chuỗi test đã chạy (spec + report trong `Guideline/`)

| Test | Câu hỏi | Kết quả |
|---|---|---|
| **Test1/2** | BFS level-wise sinh bundle có **complete** không? | ✅ Gate pass tuyệt đối. Nhưng Q2: số sequence bùng nổ `(2k)!/2^k` → không dùng được ở n lớn. |
| **Test3** | Pareto-dominance có nén an toàn không? | ❌ **REJECTED** — phá completeness (31% GW violation). OD ready_time+corridor patch cắt được k=1 collapse nhưng bundling vẫn hiếm. |
| **Test4** | Forward-slack representative rule + dominance giữa các tập | d=1 sound, nén tốt; **d≥2 dominance FAIL** (2D "đường tắt chéo" ẩn dưới tóm tắt K/W). §5.4 fallback activate 32–44%, giảm theo n. |
| **Test4.1** | Re-check Test4 ở n lớn | Nhiều rule xấu đi rõ khi n tăng — bài học: **không tin số đo chỉ ở n nhỏ**. |
| **Test5** | Self-survival bound | Sound nhưng **prune 0%** ở chỗ cần → **CLOSED**, vô dụng. |
| **★ Test6** | Forward label-setting DP (xây route tiến theo thời gian, dominance trên state `(v,IV,C)`) | ✅ **KẾT QUẢ TỐT NHẤT.** Gate 1.A/B/C: 0/616. §2.3 dominance giữa chừng: 0/160. Nén **tốt lên** khi n tăng (16%→5.5%). Nhanh **5–10×** so với BFS, ổn định n=4..15. |
| **Test6.1** | Adversarial re-check Test6 (nhiều seed, phản ví dụ dựng tay, K/W độc lập) | ✅ Vẫn 0 violation. |
| **Test6.2** | Lấp khoảng trống 2D (Test6.1 toàn 1D, chưa test cơ chế "đường tắt chéo" đã giết Test3/4) | ✅ Phản ví dụ 2D thật cũng PASS. **Phát hiện cấu trúc:** dominance Test6 (khớp node-ID chính xác) **miễn nhiễm** với loại lỗ hổng đó — chỉ so 2 lịch sử đã hội tụ về đúng cùng 1 node vật lý. |

### Kết luận T4/T6

- Câu hỏi T4 gốc (cận đơn điệu rẻ để cắt **cả cây con** cho open route) **chưa giải được trên
  giấy**.
- Nhưng **Test6 DP** là giải pháp thực nghiệm mạnh: đủ căn cứ đề xuất **thay Algorithm A (BFS
  level-wise) bằng DP label-setting**, trong phạm vi đã đo (n∈{3..15}, B∈{2,3,4}, GW+OD).
- **Chưa đo:** B>4, n>15. Nếu main experiment (Master §12.4: n∈{10,15,20,30}) vượt các giá trị
  này → cần một vòng đối chứng bổ sung (tinh thần Test4.1) trước khi khoá kết luận thesis.
- Memory liên quan: `test4-fwdslack-inprogress.md`.

### Code T4/T6 (trong `experiments/T2BFS/`)

| File | Vai trò | Tái dùng thế nào |
|---|---|---|
| `t2_core.py` | **Nền tảng.** `WNode`, `is_feasible()` (viết 1 lần, GW+OD chung), `brute_force()`, `bfs_generate()`. | Import thẳng. Mọi test sau đều tái dùng — KHÔNG viết lại feasibility. |
| `t2_gen.py` | Sinh instance ngẫu nhiên (`build_instance`, `travel_time` — trả **phút**). | Import. Chú ý bug đơn vị: K cần km, phải quy đổi qua `SPEED_KMH/60` (Test6 §1 đã sửa). |
| `t4_profile.py` | `K_W_of_route()`, `route_distance_km()`, `KAPPA=1.0`. Công thức K/W chuẩn. | Import. Dùng chung `KAPPA` — không định nghĩa lại. |
| `t6_dp.py` | **★ Core DP.** `Label=(v,IV,C,t,K,W)`, transition pickup/delivery/home, dominance theo round `|IV|+|C|`, `run_dp()`. `_tt_to_km()` xử lý đơn vị. | **Đây là ứng viên thay Algorithm A.** Import `run_dp()`. |
| `t6_run_gate1.py` | Gate 1.A/B/C (bundle + Pareto completeness/soundness vs brute_force). | Chạy lại để verify sau khi sửa `t6_dp`. |
| `t6_run_gate1_dominance_midway.py` | §2.3 — DP_full vs DP_prune (dominance giữa chừng có mất label không). | Như trên. |
| `t6_run_viec2.py` / `t6_run_viec3.py` | State-space compression / wall-clock speedup vs BFS. | Đo lại nếu đổi grid. |
| `t61_run_viec2/3/4.py`, `t62_run_case_d.py` | Adversarial re-checks Test6.1 / 2D counterexample Test6.2. | Template để dựng phản ví dụ mới. |
| `t3_pareto.py`, `t3_rerun_od.py`, `t3_check_k1.py` | Test3 (Pareto REJECTED, OD patch). | Tham khảo — đừng tái dùng Pareto-dominance. |
| `t4_fwdslack.py`, `t4_gate0.py`, `t4_run_*.py`, `t5_ub.py`, `t5_run_*.py` | Test4/5 (forward-slack, self-survival — đều không đủ mạnh). | Tham khảo lịch sử. |

---

## 3. T5 — Component decomposition cho counterfactual VCG (nhánh Algorithm B/C)

**Trạng thái: [VALIDATED] — có giá trị thuật toán thật, xác nhận trên CPLEX 12.10 + CBC.**

### Ý tưởng

Conflict graph: node = driver, cạnh giữa `i`,`k` nếu tồn tại route của `i` và route của `k`
chia sẻ ≥ 1 order (nhìn **route pool**, KHÔNG nhìn lời giải tối ưu; FD **không** là cạnh). Claim
(Master §9.3): nếu `i` thuộc connected component `P`, thì `Z*_{-i} − Z*` chỉ phụ thuộc driver/
order trong `P` → `Z*_{-i}` giải được trên sub-instance giới hạn ở `P`, cộng cache phần còn lại.

### Test đã chạy (spec + report trong `Guideline_A2/`)

| Test | Câu hỏi | Kết quả |
|---|---|---|
| **Test7** | Decomposition có **đúng** không? 3 case dựng tay (baseline / FD nối ảo 2 đảo / FD rẻ hơn route), brute-force, không solver. | ✅ Cả 3 case **khớp tuyệt đối** (\|Δ\| = 0). Kể cả case FD rẻ hơn mọi route (FD separable per-order). + robustness case C' (FD marginal) cũng khớp. |
| **★ Test8** | Decomposition có tiết kiệm **thời gian thật** không, hay presolve của solver đã tự làm? Quét `n_components ∈ {2,4,8,16,32}`, 3 seed. | ✅ **T5 có giá trị thật (dòng đầu bảng ngưỡng §5).** Trên **CPLEX 12.10**: speedup nc=32 = **14.9× wall / 391× deterministic-ticks** (median), tăng đơn điệu. Presolve ON **không** thu hẹp khoảng cách — thậm chí ON còn chậm hơn OFF cho naive. Correctness gate: max \|Z_naive−Z_dec\| = 6.8e-13. **CBC 2.10.12** corroborate: speedup 12.4×. |

### Kết luận T5

- Decomposition **đúng** (Test7) và **nhanh thật** (Test8) — không phải hệ quả tự nhiên của
  presolve. **Đủ làm trụ cột novelty** (Master §5 ứng viên 2, §10 T5).
- **Việc còn lại (Test8 §6):**
  1. **Tie-breaking toàn cục vs cục bộ** — instance Test8 có Z* duy nhất, chưa test ties. Master
     §8.2 yêu cầu tie-break lexicographic **toàn cục**. Cần test: giải sub-instance theo
     component → tie-break cục bộ có chọn route khác → có làm **sai giá trị payment** không.
  2. **Cấu trúc component không đều** — Test8 giữ component 4-driver đồng nhất. Quét thêm
     component kích thước trộn + instance có **một** component lớn nuốt phần lớn driver (kịch
     bản xấu nhất, giống Case B Test7).
  3. **Proof** — Test7 §3 đã phác đường (objective tách rời theo route + FD-per-order; exchange
     argument cho phần ngoài `P`). Số liệu Test8 (naive == decomposed tới 1e-13) là bằng chứng
     thực nghiệm mạnh.
- Memory liên quan: `test7-component-decomposition-probe.md`, `python-37-cplex-api.md`.

### Code T5 (trong `experiments/T2BFS/`)

| File | Vai trò | Chạy bằng |
|---|---|---|
| `t7_probe.py` | **Test7 self-contained.** `solve_wdp_bruteforce()`, `build_conflict_graph()`, `connected_components()`, 3 case + case C'. Số liệu literal, brute-force, KHÔNG solver. | `anaconda3\python.exe` (3.13). `<1s`. |
| `t8_gen.py` | **Test8 instance generator.** `make_component()` (component độc lập tuyệt đối, FD ~50% rẻ hơn route rẻ nhất), `make_instance()` (ghép, không nối). Trả `n_components_designed` + `component_of` làm oracle. | Dùng chung cả 2 backend. |
| `t8_cplex.py` | **★ Test8 backend CPLEX 12.10 (primary).** Build MILP in-process, đo `c.solve()` wall + `get_dettime()` ticks, toggle `parameters.preprocessing.presolve`. `build_conflict_graph`/`connected_components`/`solve_wdp` viết lại (không import t8_core). Grid §3, oracle §1.2, gate §2.3, presolve probe §4. | **Python 3.7.7** (xem §5). `~12s`. |
| `t8_core.py` | Test8 backend CBC (đối chứng). LP writer + `cbc.exe` subprocess, `-preprocess on/off`, parse `Total time (CPU seconds)` + `.sol`. | `anaconda3\python.exe`. |
| `t8_run.py` | Driver cho backend CBC (gọi `t8_core`). Grid + gate + presolve probe. | `anaconda3\python.exe`, cần `T8_SCRATCH` env + `PYTHONIOENCODING=utf-8`. `~70s`. |
| `t8_results_cplex.csv` / `t8_presolve_cplex.csv` | **Kết quả CPLEX (dùng cái này).** 15 dòng + presolve nc=32. |
| `t8_results.csv` / `t8_presolve.csv` | Kết quả CBC (đối chứng). |

---

## 4. Bảng tra nhanh — file code theo test

```
experiments/T2BFS/
├── t2_core.py        Test2  [NỀN] is_feasible/brute_force/bfs_generate — MỌI test tái dùng
├── t2_gen.py         Test2  sinh instance ngẫu nhiên (travel_time -> PHÚT)
├── t2_run.py         Test2  gate completeness BFS
├── t3_pareto.py      Test3  Pareto-dominance [REJECTED]
├── t3_rerun_od.py    Test3  OD ready_time+corridor patch
├── t3_check_k1.py    Test3  k=1 collapse check
├── t4_profile.py     Test4  [NỀN] K_W_of_route/route_distance_km/KAPPA=1.0
├── t4_fwdslack.py    Test4  forward-slack representative rule
├── t4_gate0.py       Test4  gate 0
├── t4_run_*.py       Test4  các "việc" 1..5.4, kèm biến thể n10/n20
├── t5_ub.py          Test5  self-survival bound [CLOSED]
├── t5_run_*.py       Test5  việc 1..3
├── t6_dp.py          Test6  [★ CORE] forward label-setting DP — ứng viên thay Algorithm A
├── t6_run_gate1.py               Test6  Gate 1.A/B/C
├── t6_run_gate1_dominance_midway.py  Test6  §2.3 DP_full vs DP_prune
├── t6_run_viec2.py / viec3.py    Test6  state-space / speedup
├── t61_run_viec2/3/4.py          Test6.1  adversarial re-check
├── t62_run_case_d.py             Test6.2  2D counterexample
├── t7_probe.py       Test7  [★] component decomposition đúng đắn (brute-force)
├── t8_gen.py         Test8  instance generator (component có kiểm soát)
├── t8_cplex.py       Test8  [★ PRIMARY] backend CPLEX 12.10 (Python 3.7)
├── t8_core.py        Test8  backend CBC (đối chứng)
└── t8_run.py         Test8  driver cho backend CBC
```

**Nguyên tắc tái dùng (đã áp dụng xuyên suốt Test2–8):**
- KHÔNG viết lại `is_feasible()` — luôn import `t2_core`.
- KHÔNG viết lại công thức K/W — luôn import `t4_profile` (và dùng chung `KAPPA`).
- KHÔNG đọc bid ở bất kỳ đâu trong route generation (điều kiện DSIC — Master §0).
- Gate là phép kiểm **sound/không sound** (đúng/sai tuyệt đối), 1 vi phạm đủ bác bỏ.
- Không tin số đo chỉ ở n nhỏ — luôn re-check ở n≥10 (bài học Test4.1).

---

## 5. Môi trường chạy (chi tiết trong memory `python-and-cplex-environment` + `python-37-cplex-api`)

| Việc | Interpreter | Ghi chú |
|---|---|---|
| Test2–7, Test8-CBC, mọi script Python thuần | `C:\Users\An Khoa\anaconda3\python.exe` (3.13.9) | `python` trên PATH là stub Windows Store — hỏng. Dùng full path. Có pandas/numpy/sklearn/matplotlib. |
| **Test8-CPLEX** (`t8_cplex.py`) | `C:\Users\An Khoa\AppData\Local\Programs\Python\Python37\python.exe` (3.7.7) | Bắt buộc 3.7 vì binding CPLEX 12.10 là `py37_cplex12100.pyd`. Trong code: `sys.path.insert(0, r"K:\Programing Hardware\Cplex\cplex\python\3.7\x64_win64")` rồi `import cplex` → 12.10.0.0, engine đầy đủ. |
| Pipeline VCG gốc (OPL) | `oplrun.exe` tại `K:\Programing Hardware\Cplex\opl\bin\x64_win64\oplrun.exe` (CPLEX 12.10) | Qua `Src_Cplex/cmain.py`. Subprocess, overhead ~0.3–1.7s/lần. KHÔNG dùng cho Test7/8. Trap: `SheetConnection` trong `.mod` có thể treo vô hạn — inline data vào `.dat`. |
| CBC solver | `K:\Programing Hardware\Cplex\Cbc-releases.2.10.12-w64-msvc16-md (1)\bin\cbc.exe` | Bundled sẵn. `-preprocess on/off`, tự in `Total time (CPU seconds)`. |

**Mạng bị chặn** trên máy này (conda/pip SSL cert fail) — không tạo env mới / không pip install
được. Python 3.7.7 đã cài tay từ python.org.

---

## 6. Việc tiếp theo được đề xuất (không bắt buộc theo thứ tự)

1. **T5 (ưu tiên):** Test8 §6 việc 1–3 — tie-breaking toàn cục vs cục bộ (rủi ro DSIC nếu sai
   giá trị payment), cấu trúc component không đều, viết proof exchange-argument.
2. **T4/T6:** nếu main experiment cần n∈{20,30} hoặc B=5 → vòng đối chứng bổ sung cho `t6_dp.py`
   trước khi khoá kết luận thay-Algorithm-A.
3. **Tích hợp:** T6 DP (route generation) + Algorithm B MILP + Algorithm C decomposition thành
   một pipeline end-to-end trên instance thật (Master §16 là ví dụ mẫu kiểm tay được).
4. **RQ1** (Master §12.2, §5 ứng viên 3): chạy sớm sau khi naive C hoạt động — nhưng chú ý bẫy
   alignment (§12.2: khoá grid trước, không tune tham số để đạt gate).

---

## 7. Nhãn trạng thái tổng hợp

| Thành phần | Nhãn | Ghi chú |
|---|---|---|
| Algorithm A BFS completeness | [VALIDATED] | Test1/2, 1152+ instance. Nhưng sequence blowup ở n lớn. |
| Pareto-dominance nén | [REJECTED] | Test3 — phá completeness. |
| Forward-slack / self-survival | [REJECTED]/[CLOSED] | Test4/5 — không đủ mạnh. |
| **T6 forward label-setting DP** | **[VALIDATED]** | Test6/6.1/6.2 — 0 violation, nén tốt, nhanh 5–10×. Phạm vi n≤15, B≤4. Ứng viên thay Algorithm A. |
| **T4 cận đơn điệu open-route (đúng nghĩa)** | **[OPEN]** | Chưa giải trên giấy. T6 là workaround thực nghiệm. |
| Algorithm B MILP | [VALIDATED] | Chuẩn set-partitioning, chạy được CPLEX + CBC (code trong t8_*). |
| **T5 component decomposition** | **[VALIDATED]** | Test7 (đúng) + Test8 (nhanh thật, CPLEX 12.10). Đủ làm trụ cột novelty. |
| Tie-breaking toàn cục khi decompose | [OPEN] | Test8 chưa test ties — rủi ro DSIC. |
