# Thin SPEC — Chatbot tư vấn y tế an toàn

Thin SPEC này chốt một lát cắt đủ nhỏ để build prototype trong Day 06, dựa trên flow: Entity Extraction -> Agent Planner -> Vector Search Q&A -> Medicine Search -> Context Fusion -> LLM -> Final Response.

## 1. Track, product/app và user

**Track:** Healthcare / AI medical advisory assistant  
**Product/app thật:** Chatbot tư vấn y tế dựa trên tài liệu bác sĩ - bệnh nhân và cơ sở dữ liệu thuốc SQL/CSV  
**User cụ thể:** Người bệnh trưởng thành hoặc người chăm sóc đang có triệu chứng phổ biến như sốt, đau đầu, ho, cúm và muốn biết có thể dùng thuốc OTC như Paracetamol hay không.  
**Nhóm có phải user thật không? Nếu không, khác ở đâu?** Nhóm có thể self-use ở vai trò người bệnh phổ thông, nhưng không thay thế được user thật vì thiếu bối cảnh bệnh nền, tuổi, thai kỳ, thuốc đang dùng, mức độ lo lắng và hành vi ra quyết định khi có rủi ro.

## 2. Evidence summary

| Evidence | Nguồn | User/pain nói lên điều gì? | SPEC phải đổi gì? |
|---|---|---|---|
| Flow hiện tại có 3 loại entity chính: Symptoms, Medicine, Disease. | Mô tả sản phẩm của nhóm | User hỏi tự nhiên thường trộn triệu chứng, tên thuốc và bệnh nghi ngờ trong cùng một câu. | Entity extraction phải trả về entity, intent, confidence và thông tin còn thiếu. |
| Prototype dùng cả Q&A database và medicine database. | Kiến trúc nhóm cung cấp | Câu trả lời y tế cần vừa giống tình huống bệnh nhân thật, vừa kiểm tra thông tin thuốc chính xác. | Agent planner phải gọi song song Vector Search và Medicine Search khi có thuốc hoặc bệnh liên quan. |
| CDC nêu cúm có thể nhẹ đến nặng và có dấu hiệu cần chăm sóc y tế ngay. | CDC: https://www.cdc.gov/flu/signs-symptoms/index.html | Với triệu chứng như cúm/sốt, bot không được chỉ trả lời mẹo chăm sóc chung; phải phát hiện red flags. | Thêm Safety Gate trước LLM: nếu có khó thở, đau ngực, lơ mơ, tím môi/mặt, mất nước nặng, nhóm nguy cơ cao thì ưu tiên hướng dẫn đi khám/cấp cứu. |
| MedlinePlus nêu acetaminophen/paracetamol có nguy cơ quá liều, tổn thương gan và cần lưu ý sản phẩm chứa cùng hoạt chất. | MedlinePlus: https://medlineplus.gov/druginfo/meds/a681004.html | User có thể hỏi "uống Paracetamol được không" nhưng thiếu tuổi, bệnh gan, rượu, thuốc đang dùng hoặc dùng nhiều thuốc cùng hoạt chất. | Medicine Search phải trả về uses, side effects, contraindications/cautions; LLM không đưa liều cá nhân nếu thiếu dữ kiện an toàn. |
| WHO nhấn mạnh AI trong y tế cần đạo đức, giám sát và trách nhiệm giải trình. | WHO: https://www.who.int/publications/i/item/9789240029200 | AI y tế rủi ro cao nếu tự tin trả lời như chẩn đoán/kê đơn. | Chọn conditional automation: AI tự tổng hợp trong case an toàn hẹp, nhưng user/bác sĩ giữ quyền quyết định; mọi câu trả lời phải có nguồn và giới hạn. |

## 3. Pain statement

```text
User người bệnh phổ thông đang gặp khó ở bước hiểu triệu chứng và quyết định có thể dùng thuốc OTC hay cần đi khám,
vì câu hỏi của họ thường mơ hồ, thiếu thông tin an toàn và trộn triệu chứng - thuốc - bệnh nghi ngờ,
dẫn tới nguy cơ tự dùng thuốc sai, bỏ qua dấu hiệu nặng hoặc tin vào câu trả lời AI không có nguồn.
Bằng chứng chính là flow nhóm đưa ra cần kết hợp NER/Intent, Q&A database và medicine database; đồng thời nguồn CDC/MedlinePlus cho thấy triệu chứng cúm và Paracetamol đều có các cảnh báo an toàn cần kiểm tra.
```

## 4. Build slice

```text
Cho người bệnh trưởng thành đang hỏi "Tôi sốt, đau đầu, nghi cúm, có uống Paracetamol được không?",
prototype sẽ dùng AI để trích xuất symptoms/medicine/disease, phát hiện red flags, truy xuất case Q&A tương tự và thông tin thuốc,
tạo ra câu trả lời tư vấn an toàn gồm: điều bot hiểu, thông tin thuốc có nguồn, câu hỏi cần bổ sung, khi nào cần đi khám,
và xử lý failure mode AI tư vấn thuốc thiếu an toàn bằng safety gate + low-confidence questions + fallback đi khám/bác sĩ.
```

## 5. Auto/Aug decision

- [ ] **Augmentation:** AI gợi ý/draft/phân loại, user quyết cuối.
- [x] **Conditional automation:** AI tự làm trong case hẹp; case mơ hồ/rủi ro chuyển người.
- [ ] **Automation:** AI tự quyết và tự hành động.

**Lý do chọn:** Miền y tế có rủi ro cao. AI có thể tự động hóa các bước hẹp như extract entity, retrieve nguồn, tổng hợp câu trả lời có cảnh báo. AI không được tự chẩn đoán, kê đơn, hoặc kết luận an toàn khi thiếu dữ kiện.  
**Human role:** reviewer / decider / rescuer. User quyết cuối; bác sĩ/dược sĩ là tuyến cứu hộ trong case red flag, thiếu thông tin hoặc chống chỉ định.

## 6. Four paths

| Path | Prototype phải thể hiện gì? |
|---|---|
| Happy | User hỏi triệu chứng nhẹ + thuốc phổ biến, không có red flag. Bot extract đúng `sốt`, `đau đầu`, `Paracetamol`, `cúm`; gọi Vector Search + Medicine Search; trả lời có nguồn, cảnh báo ngắn và khuyên theo dõi/đi khám nếu nặng hơn. |
| Low-confidence | User hỏi mơ hồ như "em bị nóng nóng đau người uống thuốc gì". Bot không đoán thuốc/bệnh; hỏi 2-3 câu: tuổi, thời gian sốt, nhiệt độ, bệnh nền/thuốc đang dùng, dấu hiệu khó thở/đau ngực. |
| Failure | User có red flag hoặc thuốc có cảnh báo, ví dụ đau ngực/khó thở/lơ mơ, bệnh gan, uống rượu nhiều, đang dùng nhiều thuốc chứa acetaminophen. Bot không đưa lời khuyên dùng thuốc; hiển thị cảnh báo đi khám/cấp cứu hoặc hỏi bác sĩ/dược sĩ. |
| Correction | User sửa "không phải Paracetamol, là Ibuprofen" hoặc "tôi có bệnh gan". Bot cập nhật entity, chạy lại Medicine Search, hiển thị phần thay đổi so với câu trả lời trước và không giữ khuyến nghị cũ. |

## 7. Failure mode nguy hiểm nhất

```text
Nếu user hỏi dùng Paracetamol khi đang sốt/đau đầu nhưng không nói bệnh gan, uống rượu, thuốc đang dùng hoặc đã dùng thuốc chứa cùng hoạt chất,
AI có thể trả lời tự tin rằng có thể dùng thuốc,
hậu quả là user tự dùng thuốc sai, quá liều hoặc bỏ qua tình trạng cần khám.
Prototype sẽ xử lý bằng safety gate bắt buộc: kiểm tra red flags + câu hỏi thiếu thông tin + hiển thị nguồn thuốc + không cá nhân hóa liều khi thiếu dữ kiện + fallback hỏi bác sĩ/dược sĩ.
Owner kiểm thử path này là Thành viên 4 (T.D.Mạnh) (Test / failure path).
```

## 8. Owner plan cho sáng Day 06

| Thành viên | Việc phụ trách | Bằng chứng cần có trong repo |
|---|---|---|
| L.V.Khiêm | Research / evidence | Evidence pack, link nguồn CDC/MedlinePlus/WHO,Openscience, 3 prompt self-use và ghi chú observation. |
| P.K.Khang | Thin SPEC cuối, sơ đồ flow, 4 paths, checklist safety. |
| N.D.Hưng | Prototype | Demo chatbot: NER + planner + vector mock/search + medicine CSV/SQL + context fusion + LLM response. |
| T.D.Mạnh | Test / failure path | Test cases happy, low-confidence, red flag, correction; log input/output. |
| N.D.M.Trí | Demo script / repo | Script demo 3-5 phút, README chạy prototype, ảnh/screenshot minh họa. |
