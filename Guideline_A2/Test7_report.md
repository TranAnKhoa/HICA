# Test7 Report — Probe: Component Decomposition cho VCG Payment (T5 novelty)

**Loại:** bản thăm dò (probe), không phải bộ test đầy đủ như Test2–6.2. 3 case dựng tay, số
liệu literal, brute-force liệt kê toàn bộ allocation hợp lệ (không solver). Chạy < 1 giây.

**File:** `experiments/T2BFS/t7_probe.py` — chạy:
`"C:\Users\An Khoa\anaconda3\python.exe" experiments\T2BFS\t7_probe.py`

**Câu hỏi trung tâm:** khi loại winner `i` để tính counterfactual `Z*_{-i}`, có thể **chỉ giải
lại sub-instance giới hạn trong connected component `P`** (của conflict graph xây trên route
pool, FD không tham gia cạnh) và vẫn ra đúng payment không?

---

## Kết luận (theo đúng 3 nhánh cuối §1 của spec)

> **★ Cả 3 case A/B/C KHỚP TUYỆT ĐỐI** (|chênh lệch| = 0.000000 ở cả hai phép kiểm: `Z_full`
> vs `Z_decomposed`, và `delta_full` vs `delta_sub`).
>
> → **Tín hiệu tốt — đáng viết Test8.md đầy đủ** (gate nghiêm ngặt, quét nhiều instance, có
> MILP solver, kiểm tie-breaking toàn cục vs cục bộ, mở rộng n driver — xem §3 spec).

Một robustness case bổ sung (`C'` — FD là lựa chọn **biên/marginal** cho o3, `fd_cost=8` sát
route rẻ nhất `rC1=8`, đồng thời `o1` có FD rẻ `16` cạnh tranh sát route) cũng **khớp tuyệt
đối**. Điều này củng cố Case C: FD không phá separability dù nó rẻ (Case C) hay ở ranh giới
cạnh tranh (Case C').

---

## Case A — Baseline: hai "đảo" tách biệt

| Đại lượng | Giá trị |
|---|---|
| **Z\*** | **38.0** |
| allocation\* | A→rA3 {o1,o2} cost 18 · C→rC3 {o3,o4} cost 20 · FD: {} |
| Conflict graph | A–B, C–D |
| Components | `{A,B}`, `{C,D}` — **2 component** (đúng kỳ vọng) |

Kỳ vọng bằng tay của spec (A=rA3 18đ, C=rC3 20đ, B/D rảnh) **khớp chính xác** với brute-force.

| winner | component | Z_full | Z_decomposed | \|Δ delta\| | \|Δ level\| | p_full | p_decomp | match |
|---|---|---:|---:|---:|---:|---:|---:|:--:|
| A | {A,B} | 39.000 | 39.000 | 0.000000 | 0.000000 | 19.000 | 19.000 | ✅ |
| C | {C,D} | 39.000 | 39.000 | 0.000000 | 0.000000 | 21.000 | 21.000 | ✅ |

Loại A: chỉ phần `{o1,o2}` (component `{A,B}`) giải lại → `Z_sub`; phần `{o3,o4}` giữ nguyên
`C=rC3` từ alloc\* → `Z_sub_rest = 20`. Tổng khớp `Z_full` tuyệt đối. Cơ chế đo (§1 spec) cài
đặt đúng.

---

## Case B — ★ Stress test chính: route pool mở rộng, 2 "đảo" cùng reach o5

| Đại lượng | Giá trị |
|---|---|
| **Z\*** | **43.0** |
| allocation\* | A→rA3 {o1,o2} cost 18 · C→rC4 {o3,o5} cost 12 · D→rD2 {o4} cost 13 · FD: {} |
| Conflict graph | A–B, A–C (chung o5), C–D |
| Components | `{A,B,C,D}` — **1 component duy nhất** |

**Code tự phát hiện 1 component gộp** qua `build_conflict_graph` (A và C nối trực tiếp vì cùng
có route chạm o5: `rA4={o1,o5}`, `rC4={o3,o5}`), **không hard-code "2 component" như Case A**.

Lưu ý: kỳ vọng bằng tay của spec (A=rA3, C=rC3) **không phải** ground truth — brute-force là
trọng tài. Lời giải tối ưu thật dùng `C=rC4 {o3,o5}` (12đ) để phủ luôn o5, rẻ hơn phương án
đẩy o5 sang FD (50đ). `Z* = 18 + 12 + 13 = 43`.

| winner | component | Z_full | Z_decomposed | \|Δ delta\| | \|Δ level\| | p_full | p_decomp | match |
|---|---|---:|---:|---:|---:|---:|---:|:--:|
| A | {A,B,C,D} | 44.000 | 44.000 | 0.000000 | 0.000000 | 19.000 | 19.000 | ✅ |
| C | {A,B,C,D} | 45.000 | 45.000 | 0.000000 | 0.000000 | 14.000 | 14.000 | ✅ |
| D | {A,B,C,D} | 44.000 | 44.000 | 0.000000 | 0.000000 | 14.000 | 14.000 | ✅ |

Vì component gộp = toàn bộ instance, `Z_sub_rest = 0` và `Z_decomposed = Z_sub = Z_full` một
cách tầm thường — **nhưng đây chính là hành vi đúng cần confirm**: decomposition **không** tách
nhỏ `{C,D}` ra giải riêng (điều sẽ sai), vì `o5` là cầu nối thật. Conflict graph trên route
pool (không cần thêm FD làm cạnh) **đã đủ** để bắt loại phụ thuộc "2 driver ở 2 đảo cùng reach
1 order".

---

## Case C — ★★ Stress test khó nhất: FD rẻ hơn mọi route cho o3

| Đại lượng | Giá trị |
|---|---|
| **Z\*** | **36.0** |
| allocation\* | A→rA3 {o1,o2} cost 18 · D→rD2 {o4} cost 13 · **FD: {o3} cost 5** |
| Conflict graph | A–B, C–D (**giống hệt Case A** — đồ thị chỉ nhìn route pool, không nhìn `fd_cost`) |
| Components | `{A,B}`, `{C,D}` — **2 component** |

`o3` "thoát" khỏi cạnh tranh C/D và đi thẳng vào FD (`fd_cost=5 < rC1=8`). Component `{C,D}`
vẫn tồn tại trong đồ thị (vì `C,D` chia sẻ o3, o4 trong route pool), nhưng trong lời giải tối
ưu o3 dùng FD, chỉ o4 do driver phủ.

| winner | component | Z_full | Z_decomposed | \|Δ delta\| | \|Δ level\| | p_full | p_decomp | match |
|---|---|---:|---:|---:|---:|---:|---:|:--:|
| A | {A,B} | 37.000 | 37.000 | 0.000000 | 0.000000 | 19.000 | 19.000 | ✅ |
| D | {C,D} | 37.000 | 37.000 | 0.000000 | 0.000000 | 14.000 | 14.000 | ✅ |

- **Loại A** (component `{A,B}`, `orders_P = {o1,o2}`): sub-instance chỉ gồm `{o1,o2}` + A/B.
  Phần ngoài P (`{o3,o4}`) giữ nguyên từ alloc\*: `D=rD2` (13) + FD(o3) (5) → `Z_sub_rest = 18`.
  Khớp `Z_full = 37` tuyệt đối.
- **Loại D** (component `{C,D}`, `orders_P = {o3,o4}`): giải lại sub-instance `{o3,o4}` + C/D
  **có bao gồm FD cho o3**. `Z_sub` chọn `FD(o3)=5 + C=rC2{o4}=14 = 19`. Phần ngoài P
  (`{o1,o2}`) giữ `A=rA3=18` → `Z_sub_rest = 18`. `Z_decomposed = 37` khớp.

**Đây là phép chứng minh trực tiếp cho lo ngại §9.3 spec** ("FD cost là separable per-order
nên có thể vẫn tách được, nhưng phải chứng minh"): FD cost **tách được theo từng order**, và
việc gán một order trong component sang FD **không** kéo theo phụ thuộc toàn cục — miễn là khi
giải sub-instance ta cho phép FD phục vụ các order trong `orders_P` với đúng giá công khai của
chúng (điều `solve_wdp_bruteforce` đã làm sẵn qua `fd_orders = order_set - covered`).

**Cơ chế vì sao khớp:** FD chỉ coupling qua objective (`Σ q_o·z_o`), là **tổng tách rời theo
order**. Order thuộc `orders_P` → chi phí FD của nó nằm trọn trong `Z_sub`. Order ngoài
`orders_P` → chi phí FD của nó nằm trọn trong `Z_sub_rest` và **bất biến** khi loại `i ∈ P`
(vì `i` không có route chạm order đó — định nghĩa component). Không có hạng tử FD nào bị tính
hai lần hoặc bỏ sót.

---

## Robustness bổ sung — Case C' (không trong spec, thêm để chắc)

FD ở **ranh giới cạnh tranh** thay vì rẻ áp đảo: `fd_cost = {o1:16, o2:50, o3:8, o4:50}` —
`o3` FD tie với `rC1=8`, `o1` FD (16) sát `rA1=10`/`rB1=11`. Cấu trúc route giống Case A/C.

- `Z* = 38.0`, allocation\*: A→rA3 (18) · C→rC3 {o3,o4} (20) · FD: {} — ở đây FD **thua** (route
  rC3 gộp rẻ hơn). Components `{A,B}`, `{C,D}`.
- Winner A: Z_full = Z_decomposed = 39.000, |Δ| = 0. Winner C: 39.000, |Δ| = 0. **Khớp tuyệt đối.**

→ Decomposition đứng vững ở cả 3 chế độ của FD: irrelevant (Case A/B, `fd_cost=50`), dominant
(Case C, `fd_cost=5`), marginal (Case C', `fd_cost=8` tie).

---

## Việc cần làm ở Test8.md (ghi chú, không làm lúc này — theo §3 spec)

1. **Tie-breaking toàn cục vs cục bộ.** Spec §8.2 gốc yêu cầu tie-break lexicographic theo
   `route_id` trên **toàn bộ** instance. Test7 chưa có case có ties thật (mọi Z\* ở đây là
   nghiệm duy nhất). Test8 cần: dựng instance có nhiều optimum, kiểm khi giải sub-instance
   theo component thì tie-break cục bộ có chọn route khác tie-break toàn cục không — và nếu
   có, điều đó có làm **sai giá trị payment** (không chỉ sai việc chọn route nào trong các
   lựa chọn ngang giá) hay không.
2. **Mở rộng n.** Brute-force còn chạy được tới ~8–10 driver; quá đó cần MILP solver thật
   (CPLEX qua `Src_Cplex/config.py`). Kiểm phân phối kích thước component ở instance thật
   (detour budget chặt + time window hẹp → component nhỏ → speedup lớn); nếu component luôn
   gộp thành 1 khối như Case B thì T5 không đáng theo đuổi.
3. **Proof.** Số liệu Test7 gợi ý đường chứng minh: (a) objective = Σ (route cost) + Σ (FD cost
   per-order), FD hạng tử tách rời theo order; (b) loại `i ∈ P` không đụng route/order ngoài
   `P` (định nghĩa component); (c) do đó `Z*_{-i} - Z*` = `(Z_sub - Z*_P)` và phần ngoài `P`
   triệt tiêu. Cần viết chặt bước (b) — đặc biệt lý do phần ngoài `P` giữ **đúng** allocation\*
   gốc là tối ưu (argument trao đổi: nếu đổi được phần ngoài để rẻ hơn thì alloc\* gốc đã
   không tối ưu).

---

## Bảng số liệu gọn (đối chiếu nhanh)

| Case | Z\* | Components | #winners | Tất cả khớp? | max \|Δ\| |
|---|---:|---|---:|:--:|---:|
| A | 38.0 | {A,B}, {C,D} | 2 | ✅ | 0.000000 |
| B | 43.0 | {A,B,C,D} | 3 | ✅ | 0.000000 |
| C | 36.0 | {A,B}, {C,D} | 2 | ✅ | 0.000000 |
| C' (bổ sung) | 38.0 | {A,B}, {C,D} | 2 | ✅ | 0.000000 |
