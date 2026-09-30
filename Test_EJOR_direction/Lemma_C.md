# Lemma cho Test C — Tính cần thiết của C trong dominance key

> Viết theo đúng tinh thần Proposition 3 của T5 (`t5_decomposition.tex`): không chứng minh
> "mọi cách nới lỏng đều sai" (quá mạnh, không cần), chỉ chứng minh **một cơ chế cụ thể,
> đủ để giải thích và tổng quát hóa phản ví dụ đã tìm bằng thực nghiệm** (n=3, B_gw=2,
> seed=2). Phạm vi chứng minh là "sufficient condition for unsoundness", không phải một
> characterization đầy đủ — đúng độ mạnh cần thiết, không hơn.

---

## 0. Ký hiệu, dùng lại đúng định nghĩa trong `Algorithm_A_Description.md`

- Nhãn `ℓ = (v, IV, C, t, K, W)` — đúng định nghĩa §2.1 của Algorithm A.
- Với mỗi order `j`: `P_j` = node pickup của `j`, `l(P_j)` = cận trên time-window tại `P_j`
  (thời điểm đến muộn nhất còn hợp lệ).
- **Bất biến cấu trúc (structural invariant, hiển nhiên từ cách DP xây dựng):** `IV` và `C`
  luôn rời nhau; `C` chỉ tăng theo thời gian (chỉ `_try_delivery` thêm phần tử vào `C`,
  không phép toán nào loại bỏ phần tử khỏi `C`).
- **Giả thiết (A1) — đồng hồ không lùi:** mọi phép chuyển (`_try_pickup`, `_try_delivery`,
  `_try_home`) cho `t' = t + travel + service ≥ t` với `travel, service ≥ 0`. Do đó dọc
  theo bất kỳ chuỗi mở rộng nào từ một nhãn, thời gian không giảm.
- **Giả thiết (A2) — điều kiện khả thi của pickup:** `_try_pickup(j)` từ trạng thái `(v,t)`
  khả thi chỉ khi thời điểm đến `P_j` ≤ `l(P_j)`.
- Định nghĩa `Comp(ℓ)` := tập hợp mọi tập `C'` (giá trị `C` tại một nhãn **hoàn chỉnh**) đạt
  được bằng cách mở rộng `ℓ` qua một chuỗi phép chuyển khả thi bất kỳ.
- **Dominance key gốc** (`key_full`): so hai nhãn chỉ khi `(v, IV, C)` giống hệt nhau.
- **Dominance key nới lỏng đang xét** (`key_drop_C`): so hai nhãn khi `(v, IV)` giống nhau,
  bất kể `C`.

---

## 1. Lemma 1 (cơ chế bất khả tương thích — sufficient condition for unsoundness)

**Phát biểu.** Cho hai nhãn `ℓ_A = (v, IV, C_A, t_A, K_A, W_A)` và
`ℓ_B = (v, IV, C_B, t_B, K_B, W_B)` cùng `v`, cùng `IV` (tức cùng bucket theo `key_drop_C`),
với `C_A ≠ C_B`. Giả sử tồn tại `j ∈ C_B \ C_A` sao cho

```
l(P_j) < t_A.
```

Khi đó:

```
j ∈ C'  với mọi C' ∈ Comp(ℓ_B)        (i)
j ∉ C'  với mọi C' ∈ Comp(ℓ_A)        (ii)
```

Hệ quả trực tiếp: `Comp(ℓ_A) ∩ Comp(ℓ_B) = ∅` — hai nhãn này **không dẫn tới bất kỳ hoàn
thiện chung nào**, dù đứng cùng `(v, IV)`.

**Chứng minh.**

*(i)* Theo bất biến cấu trúc, `C` chỉ tăng dọc theo mọi chuỗi mở rộng. Vì `j ∈ C_B`, mọi
nhãn hoàn chỉnh mở rộng từ `ℓ_B` đều có `C' ⊇ C_B ∋ j`. □(i)

*(ii)* Trước hết, `j ∉ IV_A ∪ C_A`: nếu `j ∈ IV` thì vì `IV_A = IV_B = IV`, ta có `j ∈ IV_B`,
mâu thuẫn với `j ∈ C_B` (do `IV_B`, `C_B` rời nhau theo bất biến cấu trúc); còn `j ∉ C_A`
theo giả thiết `j ∈ C_B \ C_A`. Vậy tại `ℓ_A`, order `j` **chưa được đụng tới**.

Giả sử phản chứng: tồn tại `C' ∈ Comp(ℓ_A)` với `j ∈ C'`. Vì `j ∉ IV_A ∪ C_A`, để `j` xuất
hiện trong `C'`, chuỗi mở rộng từ `ℓ_A` phải chứa đúng một bước `_try_pickup(j)` tại một
thời điểm `t'' `. Theo (A1), `t'' ≥ t_A`. Theo (A2), bước pickup này khả thi chỉ khi
`t'' ≤ l(P_j)`. Kết hợp: `l(P_j) ≥ t'' ≥ t_A`, mâu thuẫn trực tiếp với giả thiết
`l(P_j) < t_A`. Vậy không tồn tại `C'` như vậy. □(ii)

∎

---

## 2. Hệ quả — vì sao dominance theo `key_drop_C` không đúng đắn (unsound)

**Corollary 1.** Dưới giả thiết Lemma 1, `ℓ_A` và `ℓ_B` không thể so sánh Pareto một cách
hợp lệ: chúng đại diện cho **hai tập tương lai rời nhau hoàn toàn**
(`Comp(ℓ_A) ∩ Comp(ℓ_B) = ∅`), không phải hai cách khác nhau để đạt cùng một tương lai với
chi phí khác nhau. Bất kỳ dominance rule nào so `(t, K, W)` giữa `ℓ_A`, `ℓ_B` rồi loại nhãn
"tệ hơn" — theo bất kỳ chiều nào — đều có nguy cơ loại mất **nhãn duy nhất** có thể dẫn tới
một `C' ∈ Comp(ℓ_B) \ Comp(ℓ_A)` (hoặc ngược lại), vi phạm tính đầy đủ (**A-P1**: Algorithm A
phải sinh **mọi** route khả thi có `|S| ≤ B`).

**Đối chiếu với phản ví dụ thực nghiệm (n=3, B_gw=2, seed=2):** `ℓ_A` = nhãn sau
`pickup o2` trực tiếp từ start (`C_A = ∅`); `ℓ_B` = nhãn sau `pickup o0 → deliver o0 →
pickup o2` (`C_B = {o0}`). Tại `t_A = 319.33`, `l(P_{o0}) = 78.76 < t_A`. Đúng điều kiện
Lemma 1 với `j = o0`. Kết luận của Lemma: không nhãn hoàn chỉnh nào mở rộng từ `ℓ_A` có thể
chứa `o0` — khớp chính xác quan sát thực nghiệm rằng bundle `{o0, o2}` (K=16.246216,
W=5.567214) chỉ đạt được qua `ℓ_B`, và bị mất hẳn khi `key_drop_C` xoá `ℓ_B` vì bị `ℓ_A`
"dominate" theo `(K, W)` thô.

**Proposition 1 (tồn tại — restated từ thực nghiệm).** Tồn tại instance (đã tìm được cụ
thể, xem trên) mà giả thiết Lemma 1 xảy ra trong quá trình chạy Algorithm A với `B_gw ≥ 2`.
Do đó `key_drop_C` (bỏ hẳn `C`) và `key_drop_C_size_only` (chỉ giữ `|C|`) **không đúng đắn
nói chung** — cả hai đều không phân biệt được `C_A`, `C_B` khi chúng khác nhau đúng ở phần tử
`j` thoả điều kiện Lemma 1, nên đều mắc lỗi như trên.

---

## 3. Điều kiện an toàn (necessary condition) — không phải fix, mà là ranh giới

**Corollary 2.** Một dominance key `κ(ℓ)` **thô hơn** `(v, IV, C)` (tức gộp một số nhãn khác
`C` vào cùng bucket) chỉ có thể đúng đắn giữa `ℓ_A`, `ℓ_B` nếu:

```
∀ j ∈ C_A △ C_B  (hiệu đối xứng):   l(P_j) ≥ max(t_A, t_B)
```

tức là **không có phần tử nào trong phần `C` khác biệt giữa hai nhãn mà deadline pickup của
nó đã trôi qua** tại thời điểm so sánh. Đây là điều kiện **cần**, suy trực tiếp từ phủ định
Lemma 1 áp cho cả hai chiều (`j ∈ C_B\C_A` và `j ∈ C_A\C_B`).

**Nhận xét quan trọng — vì sao đây không tự động cho một fix rẻ:** điều kiện trên phụ thuộc
đồng thời vào `t_A` **và** `t_B` (không phải một thuộc tính nội tại của riêng một nhãn), nên
không thể mã hoá thành một hàm khoá `κ(ℓ)` tính độc lập cho từng nhãn rồi bucket theo giá trị
đó — nó vốn dĩ là một điều kiện **theo cặp**, gần với kiểu kiểm tra "tương thích" (compatibility
check) như PCF hơn là một phép rút gọn khoá thuần tuý. Điều này giải thích cấu trúc, không
phải một hướng thuật toán mới cần thử — mọi biến thể "khoá thô hơn nhưng tính độc lập theo
từng nhãn" (bao gồm `key_drop_C_size_only` đã thử) đều **không thể** thoả điều kiện Corollary 2
một cách tổng quát, vì bản thân điều kiện không phải dạng phân hoạch theo nhãn.

**Kết luận cho A-T4:** `C` không phải trường thông tin dư thừa trong dominance key — nó
là một phần cần thiết để phân biệt các nhãn dẫn tới các tập bundle-đích khả thi khác nhau,
và điều kiện duy nhất để bỏ qua sự khác biệt đó (Corollary 2) không có dạng phù hợp với một
phép rút gọn khoá độc lập-theo-nhãn. Đây là lý do cấu trúc, không phải giới hạn của các biến
thể cụ thể đã thử.

---

## 4. Cách trích dẫn trong bài chính

Đặt ở Model/Method section, ngay sau phần mô tả dominance rule gốc (§2.5 Algorithm A), như
một đoạn ngắn giải thích *tại sao* key phải đầy đủ `(v, IV, C)`:

> Một cách tự nhiên để giảm kích thước frontier là nới lỏng điều kiện so sánh dominance,
> ví dụ bỏ qua tập order đã giao xong `C`. Chúng tôi chứng minh (Lemma 1) điều này không
> đúng đắn nói chung: hai nhãn cùng `(v, IV)` nhưng khác `C` có thể dẫn tới hai tập hoàn
> thiện rời nhau hoàn toàn, một khi tồn tại order trong phần `C` khác biệt mà deadline
> pickup đã trôi qua — trường hợp này xảy ra trong thực nghiệm của chúng tôi (Proposition 1)
> với tỷ lệ đáng kể (46.3% trên 720 instance kiểm chứng). Điều kiện an toàn tương ứng
> (Corollary 2) là một ràng buộc theo cặp, không quy giản được thành một phép rút gọn khoá
> độc lập theo từng nhãn — giải thích vì sao `C` không thể loại bỏ khỏi dominance key mà
> không phá vỡ tính đầy đủ (A-P1) của Algorithm A.

---

## 5. Việc cần làm khi ghép vào bài chính

1. Thay `Algorithm_A_Description.md §2.1/§2.5` bằng số thứ tự section thật trong bài.
2. Thêm bảng 720-instance (đã có trong báo cáo Test C) làm bảng thực nghiệm minh hoạ cho
   Proposition 1.
3. Cân nhắc thêm 1 hình minh hoạ 2 nhánh `ℓ_A`/`ℓ_B` (giống trace tay) — trực quan hoá tốt
   cho reviewer, chi phí thấp (1 hình đơn giản, 4-5 node).
4. Không cần chứng minh characterization đầy đủ ("mọi nguyên nhân unsoundness") — phạm vi
   Lemma 1 là **đủ để giải thích cơ chế đã quan sát**, đúng độ mạnh cần thiết theo tinh thần
   Proposition 3 của T5.