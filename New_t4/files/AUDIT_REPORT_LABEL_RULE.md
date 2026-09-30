# Audit report — New_t4 / T4_Label_Rule (FD-completion label rule cho Algorithm A)

**Ngày chạy:** 2026-09-23
**Phạm vi:** đọc `T4_Label_Rule.tex`, đối chiếu với code (`dp_rules.py`, `dp_fast.py`), và
**tự chạy lại** `test_dp_rules.py` (không chỉ tin số report) để xác nhận claim toán học
lẫn số liệu thực nghiệm.

**Kết luận một câu:** thuật toán đúng và tái lập được — nhưng câu trả lời cho "cắt được
nhiều không" là **có điều kiện**: rule cắt rõ rệt số *label extensions* trong quá trình
DP (19–61%, tuỳ B và giá FD), nhưng **không** cắt nhiều ở tầng *route pool cuối cùng*
(chỉ 3–20% ít Pareto-route hơn) vì phần lớn công việc bị cắt là các nhánh đã bị Pareto
dominance/feasibility loại từ trước — và tốc độ wall-clock trên enumerator thuần Python
dao động quanh 1×, có thể **chậm hơn** baseline tuỳ mức giá FD.

---

## 1. Rule làm gì

Trong lúc DP mở rộng label (route đang xây dở), với mọi tập con `T` các đơn hàng **đã
phục vụ xong** trong label đó, tính một cận dưới — đúng cho **mọi** hoàn thiện khả thi
và **mọi** bid `b ∈ Θ` — của khoản tiết kiệm nếu bỏ `T` ra khỏi route và đẩy qua FD. Nếu
cận dưới đó ≥ giá FD `q(T)`, cắt cả nhánh con ngay lập tức (không mở rộng tiếp).

Đây chính xác là điều kiện "route con + phần dư đẩy FD rẻ hơn route lớn"
(`K' + q(T) < K`) — nhưng áp dụng **trong lúc xây route** (Algorithm A), không phải hậu
xử lý sau khi đã enumerate xong như K* rule cũ (`kstar_rule.py`, đã audit ở các report
trước).

Có 2 biến thể, cùng nguyên lý:
- **FW** (forward, trước khi ghé pickup): không bao giờ fire trong thực nghiệm — xem §4.
- **LB/LB2** (look-back, sau khi phục vụ xong `T`): fire thường xuyên, là rule chính tạo
  ra hiệu quả cắt.

---

## 2. Kiểm chứng toán học — PASS, tái lập độc lập

Chạy lại `test_dp_rules.py` (Python 3.13, anaconda), đối chiếu **mọi** completion khả
thi thật (không phải mẫu) với cận dưới đã dùng để cắt, cộng so K* trước/sau rule, cộng
so `Z*` (WDP) trên 40 bid profile ngẫu nhiên:

| B | seed | bound violations | K* giữ nguyên? | WDP gap (Z*) |
|---:|---:|---:|---|---:|
| 3 | 0 | 0 / 2,642 completion kiểm | True | 2.8e-14 |
| 3 | 1 | 0 / 2,358 | True | 0.0 |
| 3 | 2 | 0 / 4,253 | True | 1.4e-14 |
| 4 | 0 | 0 / 29,011 | True | 1.3e-13 |
| 4 | 1 | 0 / 21,400 | True | 2.0e-13 |

**0 vi phạm trên mọi seed/B đã thử, K* không đổi, Z* khớp trong sai số float.** Khớp
hoàn toàn với bảng Evidence trong `.tex`. Kết luận toán học của rule đúng — phần còn
lại của report này chỉ bàn về **mức độ cắt được bao nhiêu**, không phải "có đúng không".

---

## 3. Cắt được bao nhiêu — ba cách đo, ba câu trả lời khác nhau

### 3.1 Số route trong pool cuối cùng (Pareto front) — cắt ÍT

| B | seed | pareto trước | pareto sau | tỉ lệ cắt |
|---:|---:|---:|---:|---:|
| 3 | 0 | 336 | 326 | 3.0% |
| 3 | 1 | 333 | 308 | 7.5% |
| 3 | 2 | 349 | 306 | 12.3% |
| 4 | 0 | 614 | 595 | 3.1% |
| 4 | 1 | 668 | 614 | 8.1% |

Đây là con số quan trọng nhất cho câu hỏi thực tế "route pool nhỏ đi bao nhiêu" —
**chỉ 3–12%**. Route pool cuối cùng (sau Pareto filter) hầu như không đổi kích thước,
vì hầu hết route bị rule cắt **vốn đã bị loại bởi Pareto filter tự nhiên** (chúng không
phải Pareto-optimal trong bundle của mình) — rule chỉ giúp không phải *sinh ra* các
route đó, chứ không giúp pool cuối *nhỏ hơn nhiều*.

### 3.2 Số lần mở rộng label (label extensions) — cắt VỪA-NHIỀU

| B | seed | ext (không rule) | ext (có rule) | tỉ lệ cắt |
|---:|---:|---:|---:|---:|
| 3 | 0 | 21,770 | 19,025 | 12.6% |
| 3 | 1 | 20,560 | 17,798 | 13.4% |
| 3 | 2 | 21,416 | 16,117 | 24.7% |
| 4 | 0 | 285,261 | 217,078 | 23.9% |
| 4 | 1 | 280,204 | 217,467 | 22.4% |

Đây là chỉ số *công việc DP* thực sự tiết kiệm được (mỗi lần mở rộng label là một bước
tính toán). Cắt được **13–25%** trên các seed tôi tự chạy. `.tex` báo cáo rộng hơn với
implementation tối ưu (`dp_fast.py`, incremental O(1)/extension): **19–44% ở B=3, 26–61%
ở B=4**, và phụ thuộc mạnh vào mức giá FD (bảng dưới).

### 3.3 Wall-clock — KHÔNG chắc nhanh hơn

Theo `.tex` §Work and time (enumerator Python thuần, không phải implementation
production): **0.8×–2× baseline** ở mức giá FD mặc định — tức rule **có thể làm chậm
hơn** vì chi phí tính cận dưở mỗi lần mở rộng không phải miễn phí. Yếu tố quyết định là
**giá FD tương đối so với chi phí route**:

| FD price scale | 0.6× | 1.0× (mặc định) | 1.4× |
|---|---:|---:|---:|
| Label extensions saved | 73–76% | 27–30% | 7–9% |
| Wall-clock speedup | **2.8–3.1×** | ≈1.0× | **0.75× (chậm hơn)** |

Tức: nếu FD rẻ (driver dễ bị "đá" qua FD), rule cắt rất mạnh và nhanh hơn hẳn; nếu FD
đắt (driver hiếm khi đáng bị thay bằng FD), rule gần như vô dụng và thậm chí làm chậm đi
vì overhead tính cận dưở.

---

## 4. Rule FW (forward) — không hoạt động, đúng như report tự nhận

Cả 5 seed đã chạy (3×B=3, 2×B=4): **`fw=0`** — rule FW chưa từng fire một lần nào.
`.tex` gọi đây là "negative result" và giải thích cơ chế: trước khi ghé một pickup,
continuation chưa biết, nên cận dưở phải đúng cho continuation rẻ nhất có thể — luôn có
một stop nào đó gần hướng đi tự nhiên (distance credit chỉ 0.5–0.75 USD so với giá FD
15–21 USD), và detour thời gian gần như luôn bị hấp thụ hoàn toàn bởi waiting cho các
pickup mở cửa muộn hơn (absorption trung vị 34–46 phút so với detour ~5 phút). Đây là
lý do cấu trúc, không phải lỗi cài đặt — đã tự chạy lại xác nhận đúng `fw=0` trên mọi
seed thử.

---

## 5. Khoảng cách tới "trần lý thuyết"

`.tex` đo thêm: trong số label nằm trên đường dẫn tới **ít nhất một** route thuộc K*, một
rule cục bộ lý tưởng (Theorem 4(c) trong LPF) chỉ cần giữ **2.7%** (B=3) hoặc **0.6%**
(B=4) số label đó. Rule hiện tại giữ **56%** (B=3) và **50%** (B=4) — tức đóng được
**45–50%** khoảng cách tới trần lý thuyết. Còn nhiều dư địa lý thuyết chưa khai thác
được bằng một label rule cục bộ rẻ (không cần giải WDP).

---

## 6. Trên dữ liệu RQ1 thật — chỉ là suy đoán, chưa đo

`.tex` ghi rõ (§Work and time, câu cuối): trên instance RQ1 thật, `Π*` (K* hậu xử lý) đã
cắt **77–97%** pool, so với chỉ ~61% trên các instance tổng hợp dùng để audit rule này —
gợi ý FD tương đối rẻ hơn trên RQ1, nghĩa là rule label mới **có thể** hiệu quả hơn nhiều
trên dữ liệu thật so với các con số §3 ở trên. Nhưng chính `.tex` cũng nói thẳng: **"this
must be measured, not assumed"** — chưa có số đo thật trên RQ1 cho riêng rule label này
(khác với K* hậu xử lý, đã đo ở các report trước: `kstar_rq1_crosscheck.py`, cắt
76.89%–96.81%).

---

## 7. Trả lời thẳng câu hỏi "cắt được nhiều đáng kể không"

- **Route pool cuối cùng nhỏ đi bao nhiêu:** không nhiều (3–12% trên seed đã thử) — nếu
  mục tiêu là giảm kích thước pool đưa vào Algorithm B, rule này đóng góp khiêm tốn so
  với K* hậu xử lý (K* cắt 77–97% trên RQ1 thật).
- **Công việc DP tiết kiệm được:** đáng kể — 13–61% số label extension tuỳ B/giá FD,
  nhưng đây là tiết kiệm *trong lúc tính*, không phải *kết quả cuối*.
- **Tốc độ thực tế (wall-clock):** **không chắc chắn có lợi** — dao động 0.75×–3.1× tuỳ
  hoàn toàn vào mức giá FD tương đối; ở mức giá FD "trung bình" (1.0×, gần RQ1 mặc định
  theo suy đoán) gần như hoà vốn (≈1.0×), thậm chí có thể **chậm hơn** nếu giá FD cao.
- **Giá trị thật sự của rule này** nằm ở chỗ khác: nó chứng minh được (Theorem 2) rằng
  cắt sớm trong lúc DP **không** làm mất bất kỳ route nào của K* — một khẳng định lý
  thuyết chặt chẽ, đã audit kỹ (0 vi phạm, mutation test xác nhận từng thành phần cận
  dưở là cần thiết) — chứ không phải một cải tiến tốc độ đã được đo là ăn chắc trên dữ
  liệu RQ1 thật.

**Khuyến nghị:** nếu mục tiêu là báo cáo tốc độ/kích thước pool cho thesis, cần đo trực
tiếp trên instance RQ1 thật (như đã làm với K* hậu xử lý) trước khi dùng con số §3–5 ở
trên — các con số đó chỉ đến từ instance tổng hợp nhỏ (n=8), không phải RQ1.

---

## File & tái tạo

```
New_t4/files/dp_rules.py            Rule LB/LB2/FW (enumerator day du, dung cho audit)
New_t4/files/dp_fast.py             Ban incremental O(1)/extension cua LB2 (dung do runtime)
New_t4/files/test_dp_rules.py       Audit: bound violation + K* preserve + WDP gap
New_t4/files/hica_core.py           Dependency (copy tu T4_audit_scripts/T4_audit, giu lai
                                      theo yeu cau - de New_t4/files tu chua duoc)
```

Chạy lại (Python 3.13, anaconda):
```
"C:\Users\An Khoa\anaconda3\python.exe" test_dp_rules.py 3      # B=3, 3 seed
```
Đổi B qua `run(seed, B=4, ...)` trong `test_dp_rules.py` hoặc gọi `run()` trực tiếp.
