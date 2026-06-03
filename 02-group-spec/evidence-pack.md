# Evidence Pack — Chatbot tư vấn y tế an toàn

Nộp kèm thin SPEC cuối Day 05.

## 1. Nhóm và track

**Tên nhóm:** Nhóm chatbot tư vấn y tế  
**Track:** Healthcare / AI medical advisory assistant  
**Product/app đã chọn:** Chatbot dựa trên tài liệu bác sĩ - bệnh nhân và cơ sở dữ liệu thuốc SQL/CSV  
**Build slice đang nghĩ:** Người bệnh hỏi về triệu chứng phổ biến và thuốc OTC; bot trích xuất entity, tìm case tương tự + thông tin thuốc, rồi trả lời có nguồn và safety gate.

## 2. Self-use evidence

Nhóm tự dry-run workflow bằng các prompt đại diện. Bảng này là log self-use ban đầu; khi có prototype Day 06, bổ sung screenshot thật vào cùng thư mục.

| Observation | Screenshot/link | Path liên quan | Điều học được |
|---|---|---|---|
| Prompt: "Tôi sốt 38.5, đau đầu, nghi cúm, uống Paracetamol được không?" Flow cần nhận diện đồng thời symptom, disease nghi ngờ và medicine. | Self-use prompt log trong bảng này | Happy | Không thể chỉ search Q&A hoặc chỉ search thuốc; cần fusion cả case bệnh nhân tương tự và thông tin thuốc. |
| Prompt: "Em nóng người đau nhức uống thuốc gì?" thiếu tuổi, nhiệt độ, thời gian bị, bệnh nền và thuốc đang dùng. | Self-use prompt log trong bảng này | Low-confidence | Bot phải hỏi lại thay vì đoán bệnh hoặc đề xuất thuốc ngay. |
| Prompt: "Tôi sốt, đau ngực, khó thở, uống Paracetamol được không?" có dấu hiệu nguy hiểm. | Self-use prompt log trong bảng này | Failure | Red flag phải được xử lý trước retrieval/generation; câu trả lời chính là đi khám/cấp cứu, không phải tư vấn thuốc. |
| Prompt correction: "Không phải Paracetamol, tôi đang uống thuốc có acetaminophen rồi" làm thay đổi risk. | Self-use prompt log trong bảng này | Correction | Bot cần cập nhật entity và rerun Medicine Search; không giữ khuyến nghị cũ sau khi user sửa. |

## 3. User / review / social evidence

| Quote / review / observation | Nguồn | User là ai? | Pain/failure mode |
|---|---|---|---|
| Cúm có thể gây bệnh từ nhẹ đến nặng; một số dấu hiệu cần được chăm sóc y tế ngay. | CDC Flu Signs and Symptoms: https://www.cdc.gov/flu/signs-symptoms/index.html | Người có triệu chứng hô hấp/sốt/cúm | Bot trả lời chăm sóc tại nhà mà bỏ qua red flags. |
| Acetaminophen/Paracetamol có rủi ro khi dùng quá liều, dùng nhiều sản phẩm cùng hoạt chất, bệnh gan hoặc các cảnh báo an toàn khác. | MedlinePlus Drug Information: https://medlineplus.gov/druginfo/meds/a681004.html | Người hỏi về thuốc OTC | Bot khuyên dùng thuốc khi thiếu thông tin về chống chỉ định/cảnh báo. |
| AI trong y tế cần đặt đạo đức, quyền con người, giám sát và trách nhiệm giải trình vào thiết kế và triển khai. | WHO Ethics and Governance of AI for Health: https://www.who.int/publications/i/item/9789240029200 | Người bệnh và nhân viên y tế chịu ảnh hưởng bởi AI | Bot tự tin như bác sĩ, không nêu giới hạn, không có nguồn, không có human fallback. |
| Dữ liệu bác sĩ - bệnh nhân có thể chứa ca tương tự nhưng không chắc khớp hoàn toàn với user hiện tại. | Cơ sở dữ liệu Q&A nội bộ của nhóm | Người bệnh hỏi theo ngôn ngữ tự nhiên | Vector search trả case gần giống nhưng thiếu bối cảnh cá nhân; cần show source và confidence. |

Nếu cần thêm nguồn ngoài nhóm trước checkpoint M1 Day 06:

```text
Nhóm sẽ phỏng vấn nhanh 2-3 người từng tự tra triệu chứng/thuốc online và ghi lại:
- câu hỏi họ từng nhập,
- họ sợ nhất điều gì,
- họ cần bot nói rõ nguồn/đi khám như thế nào,
- họ có hiểu cảnh báo thuốc không.
```

## 4. Competitor / analog evidence

| App / mô hình tham khảo | Họ xử lý task này thế nào? | Pattern học được | Có áp dụng trong 1 ngày không? |
|---|---|---|---|
| MedlinePlus Drug Information | Tách thông tin thuốc thành uses, warnings, side effects, precautions. | Câu trả lời thuốc nên có cấu trúc rõ và không trộn lẫn với chẩn đoán. | Có. Dùng CSV/SQL thuốc và template response 4 phần. |
| CDC Flu information | Nêu triệu chứng thường gặp và nhóm/dấu hiệu cần chăm sóc y tế. | Symptom advice cần có red-flag gate trước khi trả lời chăm sóc chung. | Có. Hard-code rule red flags cho demo. |
| Symptom-checker style triage | Hỏi thêm thông tin khi input mơ hồ, phân biệt case tự chăm sóc và case cần gặp người thật. | Low-confidence path là hỏi lại, không đoán. | Có. Dùng 2-3 câu hỏi bổ sung theo entity thiếu. |
| RAG assistant có citation | Trả lời dựa trên đoạn trích và nguồn retrieved. | Với y tế, câu trả lời phải kèm nguồn Q&A/thuốc và mức độ chắc chắn. | Có. Mock citation bằng ID tài liệu và tên thuốc trong DB. |

## 5. Evidence -> Insight

```text
Evidence nổi bật nhất:
User hỏi y tế bằng câu tự nhiên, nhưng dữ kiện an toàn thường bị thiếu. Các nguồn thuốc/triệu chứng cho thấy thiếu một chi tiết nhỏ như red flag, bệnh gan, thuốc đang dùng hoặc dùng trùng hoạt chất có thể làm câu trả lời nguy hiểm.

Insight:
User không chỉ cần câu trả lời "uống thuốc gì" hoặc "có phải cúm không".
Thật ra họ cần hỗ trợ ra quyết định an toàn: hiểu bot đã hiểu gì, thiếu gì, nguồn nào đang được dùng và khi nào phải chuyển sang bác sĩ.

Opportunity:
AI có thể giúp bằng cách tự động extract entity, gọi đúng nguồn dữ liệu và draft câu trả lời có cấu trúc,
trong khi vẫn kiểm soát rủi ro bằng red-flag gate, câu hỏi bổ sung và human fallback.
```

## 6. Evidence đổi SPEC như thế nào?

- [x] Đổi user chính.
- [x] Đổi pain statement.
- [x] Đổi build slice.
- [x] Đổi Auto/Aug decision.
- [x] Đổi 4 paths.
- [x] Đổi failure mode.
- [x] Đổi owner/test plan.

```text
Trước evidence, nhóm định build chatbot tư vấn y tế rộng: triệu chứng, thuốc, bệnh, case Q&A và database thuốc.
Sau evidence, nhóm đổi thành một lát cắt hẹp: người bệnh hỏi về sốt/đau đầu/cúm và Paracetamol.
Lý do:
Miền y tế rủi ro cao; prototype 1 ngày nên chứng minh được core loop an toàn gồm entity extraction, retrieval kép, context fusion, response có nguồn và xử lý red flag/low confidence/correction.
```
