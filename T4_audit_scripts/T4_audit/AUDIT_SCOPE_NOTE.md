# Ghi chú phạm vi: AUDIT_REPORT.md xác nhận cái gì, KHÔNG xác nhận cái gì

**Ngày:** 2026-09-22
**Lý do viết file này:** `AUDIT_REPORT.md` (2026-09-22) dùng cụm "implementation độc
lập hoàn toàn với code thesis chính" ở phần mở đầu — cụm này **gây hiểu nhầm** và cần
đính chính rõ ràng trước khi dùng report đó cho bất kỳ kết luận nào.

---

## 1. Việc thực sự đã làm

Tôi (Claude) chạy lại **đúng các file bạn đã viết sẵn** trong
`T4_audit_scripts/T4_audit/` — `hica_core.py`, `kstar_rule.py`,
`test_handcheck.py`, `test_theorem.py`, `test_family_exact.py`,
`test_realizable.py`, `test_family.py` — trên máy này (Python 3.13, scipy 1.16.3),
KHÔNG viết lại bất kỳ phần logic nào theo cách khác.

`hica_core.py` **có** tách biệt khỏi pipeline CPLEX chính của thesis (không import
`t6_dp.py`, không dùng route pool/WDP solver của `spec_2a_2b`) — điều đó đúng như mô
tả docstring của chính file đó ("Independent of the thesis code base"). Nhưng đó là
tính độc lập **giữa hai module trong cùng một bộ code bạn viết**, không phải giữa hai
cách triển khai khác nhau của cùng một ai đó (hoặc hai người khác nhau).

## 2. Vì sao "số khớp" không phải bằng chứng toán học độc lập ở đây

Toàn bộ pipeline này **tất định**: cùng seed → cùng instance ngẫu nhiên → cùng route
pool → cùng lời giải WDP (MILP exact, không có yếu tố ngẫu nhiên trong solve). Chạy lại
chính xác cùng code trên máy khác (Python 3.13 + scipy 1.16.3 thay vì môi trường gốc
bạn dùng, có thể Python 3.12 + scipy 1.17 hoặc tương tự) và nhận cùng kết quả số chỉ
chứng minh:

- Code không phụ thuộc hành vi phiên bản Python/scipy cụ thể nào (không fragile).
- Không có lỗi môi trường ẩn (thiếu thư viện, sai đường dẫn, v.v.) khiến kết quả sai
  lệch giữa hai máy.

Nó **không** chứng minh gì thêm về việc bản thân thuật toán K* hay theorem đúng, vì
không có phép tính nào được thực hiện theo một con đường độc lập thứ hai — mọi con số
trong `AUDIT_REPORT.md` đều đến từ **một** implementation duy nhất
(`hica_core.py::enumerate_pool` + `hica_core.py::kstar` + `hica_core.py::solve_wdp`),
chỉ chạy hai lần trên hai máy.

## 3. Hai việc còn thiếu để có kiểm chứng độc lập thật sự

Theo đúng góp ý, còn hai hướng chưa làm, mỗi hướng độc lập đã đủ để nâng report lên
mức "cross-validated":

1. **Viết lại brute-force theo cách khác rồi so.** Ví dụ: ILP formulation khác cho
   WDP (khác biến/ràng buộc so với `solve_wdp` trong `hica_core.py`), hoặc DP khác cho
   route enumeration (khác cấu trúc trạng thái so với `enumerate_pool`/`sequences`).
   So kết quả K* / Z* / margin giữa hai implementation trên cùng instance.
2. **Chạy `kstar_rule.py` (pure Python, không cần scipy, đã viết sẵn cho việc này —
   xem docstring của chính file: "so it can run next to the thesis code (Py 3.7 +
   CPLEX)") trực tiếp trong môi trường thesis thật** (Python 3.7.7 + CPLEX 12.10,
   trên instance RQ1 thật từ `spec_2a_2b`, không phải instance ngẫu nhiên
   `random_instance`/`family`/`build` của `hica_core.py`), rồi:
   - so tỉ lệ route bị K* cắt so với route pool gốc từ `dp_labeling.build_route_pool`;
   - kiểm tra: mọi route xuất hiện trong lời giải WDP tối ưu thật (`t8_cplex.solve_wdp`)
     trên toàn bộ bid profile đã chạy trong `spec_2a_2b/results` có nằm trong K* không
     (đây chính là property Safety, nhưng đo trên dữ liệu/route pool thật của thesis,
     không phải instance tổng hợp).

**Chưa làm việc nào trong 2 việc trên.** `AUDIT_REPORT.md` chỉ nên được đọc là:
"pipeline audit tất định, tái lập được trên môi trường khác — không có lỗi cài đặt ẩn
theo phiên bản Python/scipy", không phải "đã kiểm chứng chéo độc lập" hay "đã kiểm
chứng trên dữ liệu thesis thật".

## 4. Đề xuất sửa `AUDIT_REPORT.md`

Câu ở dòng 5-8 của `AUDIT_REPORT.md`:

> kiểm chứng số học (numerical audit) cho theorem "Local Pruning Frontier" (K* rule,
> `kstar_rule.py` — Theorem 1 của `T4_Local_Pruning_Frontier.tex`), bằng một
> implementation **độc lập hoàn toàn** với code thesis chính (`hica_core.py`:
> brute-force route enumeration + exact set-partitioning WDP).

nên sửa thành (đề xuất, chưa áp dụng — bạn xác nhận trước khi tôi sửa trực tiếp file
kia):

> kiểm chứng số học (numerical audit) cho theorem "Local Pruning Frontier" bằng cách
> chạy lại `hica_core.py`/`kstar_rule.py`/các `test_*.py` (đã viết sẵn trong repo, tách
> biệt khỏi pipeline CPLEX chính của thesis) trên một môi trường khác (Python 3.13,
> scipy 1.16.3). Đây là kiểm tra **tái lập được** (reproducibility) trên toàn bộ seed
> đã chạy, KHÔNG phải đối chiếu chéo với một implementation độc lập thứ hai, và KHÔNG
> chạy trên dữ liệu/instance thật của thesis (`spec_2a_2b`) — xem `AUDIT_SCOPE_NOTE.md`
> để biết giới hạn cụ thể và hai việc còn thiếu để đạt mức kiểm chứng độc lập thật sự.
