# Patch ngắn cho Test2 — 2 việc

## Việc 1 — Sửa bug neo ready_time của OD

**Bug:** `ready_time_pickup ~ U[0,120]` sinh độc lập với `t0` và `tau` của driver → pickup thường sẵn sàng sau khi `deadline_home = t0 + direct_time + tau` đã trôi qua → OD chết ngay ở k=1 (0.8–27% sống).

**Sửa:** neo ready_time theo tau thay vì tuyệt đối:

```python
ready_time_pickup = t0 + random.uniform(0, tau)
deadline_pickup    = ready_time_pickup + tw_width   # giữ nguyên công thức cũ
```

**Thêm 1 check bắt buộc sau khi sinh xong instance, trước khi đưa vào BFS:**
```python
feasibility_rate_k1 = % order sống ở k=1 (BRUTE_FORCE trên subset đơn)
assert feasibility_rate_k1 >= 0.5   # nếu dưới 50%, in cảnh báo, không chạy tiếp cell đó
```
In bảng `feasibility_rate_k1` theo `tau` — nếu vẫn thấp sau patch, còn bug khác (khả năng: P/D được sinh ngẫu nhiên trong cả vùng, không quanh corridor start→home, nên detour quá xa bất kể ready_time đúng lúc). Nếu vậy, sinh P/D lệch có trọng số về phía đoạn thẳng start→home (ví dụ: 70% điểm nằm trong buffer 3km quanh corridor, 30% ngẫu nhiên toàn vùng) — ghi rõ tỷ lệ này vào report vì nó là một giả định thiết kế, không phải tham số trung lập.

Chạy lại toàn bộ Test2 (gate + Q2 + Q3) sau patch, chỉ với OD, đối chiếu bảng feasibility k=1 mới với bảng cũ.

---

## Việc 2 — Test Pareto-dominance có phá completeness không

**Câu hỏi:** thay vì lưu toàn bộ `Seq(S)`, chỉ giữ tập không bị thống trục (Pareto) theo:

```python
label(seq) = (end_node(seq), arrival_time(end_node), K(seq), W(seq))
label1 dominates label2  ⟺  end_node giống nhau
                          AND arrival1 ≤ arrival2
                          AND K1 ≤ K2
                          AND W1 ≤ W2
                          AND ít nhất 1 bất đẳng thức strict
```
`Pareto(S)` = các sequence trong `Seq(S)` không bị dominate bởi sequence nào khác trong `Seq(S)`.

**Cách test — chỉ chạy trên bộ instance nhỏ đã có ground truth (n≤6, đã có `small_raw.csv`):**

```
BFS_PARETO(driver, orders, B):
    # giống hệt BFS_GENERATE cũ, nhưng ở mỗi level:
    Seq[S] = dedupe(...)              # như cũ
    Pareto[S] = filter_pareto(Seq[S]) # MỚI: giữ lại để dùng làm parent cho level sau
    # LEVEL SAU CHỈ ĐƯỢC CHÈN TỪ Pareto[P], KHÔNG PHẢI Seq[P]
```

**Đo 2 con số, cho mỗi subset S ở mọi level:**

1. `compression_ratio(S) = |Pareto(S)| / |Seq(S)|` — mức nén tiềm năng.
2. `VIOLATION`: so `BFS_PARETO` với `BRUTE_FORCE` — với mọi subset S' ở level tiếp theo, kiểm `set(BFS_PARETO[S']) ⊇ nothing_missing`. Cụ thể: với mỗi sequence R' trong `BRUTE_FORCE[S']`, kiểm xem `BFS_PARETO` có sinh ra được **ít nhất một** sequence cùng `canonical()` hay không (không cần y hệt, chỉ cần tồn tại). Nếu `BRUTE_FORCE[S']` khác rỗng mà `BFS_PARETO[S']` rỗng, hoặc thiếu sequence mà route đó là **cách duy nhất** dẫn tới một superset khả thi ở level sau nữa (kiểm đệ quy 1 level xa hơn) → đếm là 1 violation.

**Log ra:**
```csv
n, B, class, tw_width, tau, k, subset_id,
seq_count, pareto_count, compression_ratio,
violation (bool), violation_detail
```

**Ngưỡng đọc kết quả:**

| violation rate trên toàn bộ instance nhỏ | compression_ratio trung vị | Kết luận |
|---|---|---|
| 0% | bất kỳ | Dominance an toàn trong thực nghiệm → dùng Pareto thay Seq, chạy lại Q2 ở quy mô lớn (n=8..15) để xem bùng nổ có biến mất không |
| > 0% nhưng hiếm (<1% subset) | cao | Dominance gần đúng nhưng không an toàn tuyệt đối — cần tìm điều kiện bổ sung (ví dụ chỉ dùng Pareto khi route chưa từng "chèn giữa", chỉ nối đuôi) |
| > 0%, không hiếm | bất kỳ | Xác nhận phản ví dụ lý thuyết là phổ biến, không phải cá biệt — Pareto-dominance kiểu này **không dùng được**, dừng hướng này, báo cáo rõ |

Chạy xong việc 2 trước, vì nó quyết định có đáng sửa OD sâu hơn (việc 1) để dùng cho Q2 quy mô lớn hay không.