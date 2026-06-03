# Individual Workshop - Mổ App AI Thật

**Sản phẩm dùng thử:** MoMo - Trợ thủ AI Moni  
**AI feature:** Chatbot tư vấn tài chính / chi tiêu / giá xe  
**Tình huống test:** User hỏi tư vấn giá xe bằng tiếng Trung, sau đó yêu cầu bot viết lại bằng tiếng Trung.

## 1. Product promise vs reality

### Product hứa gì?

Moni được định vị như một trợ thủ AI trong app MoMo: user có thể hỏi Moni bất cứ điều gì liên quan đến chi tiêu, tài chính cá nhân, ví MoMo và một số nhu cầu tư vấn đời sống.

### User kỳ vọng gì?

Trong tình huống này, user kỳ vọng Moni:

- Hiểu input bằng tiếng Trung.
- Nếu user hỏi bằng tiếng Trung, bot có thể trả lời bằng tiếng Trung hoặc ít nhất hỏi lại rõ ràng bằng cùng ngôn ngữ.
- Khi user nói "bạn có thể viết bằng tiếng Trung không?", bot phải hiểu đây là yêu cầu về ngôn ngữ output, không phải yêu cầu ngoài khả năng.
- Nếu bot đã có khả năng dịch nội dung sang tiếng Trung, bot nên áp dụng khả năng đó nhất quán trong correction path.

### Reality quan sát được

Moni có hành vi không nhất quán:

1. User nhập tiếng Trung: `所有车型`.
2. Bot trả lời bằng tiếng Việt, đưa bảng giá SUV BMW.
3. User tiếp tục nhập tiếng Trung: `我看不懂。你可以写汉语吗？`
4. Bot từ chối: "mình chỉ hỗ trợ bằng tiếng Việt thôi nha".
5. Sau đó user nhập tiếng Việt: "dịch phần tư vấn giá xe của bạn sang tiếng Trung".
6. Bot lại dịch được nội dung sang tiếng Trung bình thường.

Đây không phải lỗi "bot không biết tiếng Trung". Lỗi chính là bot không nhận diện đúng intent "write/respond in Chinese" khi intent đó được viết bằng tiếng Trung.

## 2. Evidence

| Evidence | Screenshot | Observation |
|---|---|---|
| User hỏi bằng tiếng Trung `所有车型`. | `1.jpg` | Bot hiểu một phần intent về "các dòng xe", nhưng trả lời hoàn toàn bằng tiếng Việt. |
| User nói bằng tiếng Trung `我看不懂。你可以写汉语吗？`. | `2.jpg` | Bot từ chối và nói chỉ hỗ trợ tiếng Việt, trong khi user đang yêu cầu đổi ngôn ngữ response. |
| User nói bằng tiếng Việt "dịch phần tư vấn giá xe của bạn sang tiếng Trung". | `3.jpg` | Bot dịch được sang tiếng Trung, chứng tỏ khả năng tạo output tiếng Trung tồn tại. |

Quote quan trọng từ response lỗi:

```text
Bạn muốn mình viết bằng tiếng Trung hả? Nhưng mà mình chỉ hỗ trợ bằng tiếng Việt thôi nha!
```

Mâu thuẫn với response sau đó:

```text
以下是宝马SUV车型的参考价格，供您参考：
```

## 3. Four paths

| Path | As-is | Vấn đề | To-be |
|---|---|---|---|
| Happy | User hỏi bằng tiếng Việt, bot trả lời bằng tiếng Việt và có bảng giá. | Path này hoạt động ổn nếu user dùng tiếng Việt. | Giữ nguyên, nhưng thêm ghi nhớ language preference trong session. |
| Low-confidence | User hỏi bằng tiếng Trung, bot vẫn trả lời bằng tiếng Việt mà không hỏi lại. | Bot không báo rõ có hiểu input hay không, cũng không xác nhận ngôn ngữ muốn trả lời. | Nếu detect input là tiếng Trung, bot hỏi lại ngắn gọn hoặc trả lời bằng tiếng Trung nếu policy cho phép. |
| Failure | User yêu cầu "viết bằng tiếng Trung" bằng tiếng Trung, bot từ chối sai. | Bot nhầm language-output request thành giới hạn sản phẩm "chỉ hỗ trợ tiếng Việt". | Bot phải nhận diện đây là correction về ngôn ngữ và viết lại bằng tiếng Trung. |
| Correction | User nói bằng tiếng Việt "dịch sang tiếng Trung", bot dịch được. | Correction chỉ thành công khi user dùng tiếng Việt; nếu user dùng tiếng Trung thì fail. | Correction language phải hoạt động bất kể user diễn đạt bằng ngôn ngữ nào. |

## 4. Finding thành product decision

```text
Khi user hỏi tư vấn giá xe bằng tiếng Trung và sau đó yêu cầu bot viết bằng tiếng Trung,
AI/product nhận sai yêu cầu ngôn ngữ: bot từ chối "chỉ hỗ trợ tiếng Việt" dù nó có thể dịch sang tiếng Trung khi user yêu cầu bằng tiếng Việt,
hậu quả là user bị kẹt trong workflow, mất niềm tin vào khả năng của trợ lý và phải tự đoán cách prompt lại bằng tiếng Việt.
Lỗi thuộc layer Intent + UX Recovery + Policy/Instruction consistency.
Nên sửa bằng một language-intent classifier nhỏ: detect input language, detect output-language request, và ưu tiên correction "rewrite/translate/respond in [language]" trước khi từ chối.
```

## 5. Sketch as-is / to-be

### As-is

```text
User: 所有车型
  -> Moni detects topic roughly as car/model/pricing
  -> Moni answers in Vietnamese
  -> User: 我看不懂。你可以写汉语吗？
  -> Moni understands "Chinese" but triggers unsupported-language refusal
  -> User is blocked
  -> User tries Vietnamese: "dịch ... sang tiếng Trung"
  -> Moni translates successfully
```

Điểm gãy: cùng một nhu cầu "viết bằng tiếng Trung", nhưng kết quả phụ thuộc vào ngôn ngữ user dùng để ra lệnh.

### To-be

```text
User: 所有车型
  -> Moni detects input_language = zh
  -> Moni detects task = car price consultation
  -> Moni chooses response_language = zh, or asks: "Bạn muốn mình trả lời bằng tiếng Trung hay tiếng Việt?"
  -> User: 我看不懂。你可以写汉语吗？
  -> Moni detects correction_type = output_language_change
  -> Moni rewrites previous answer in Chinese
  -> Moni stores session preference: response_language = zh
```

## 6. Requirement để đưa vào SPEC

### Requirement

Moni cần xử lý nhất quán các yêu cầu về ngôn ngữ trong cùng một session:

- Detect ngôn ngữ đầu vào của user.
- Detect intent đổi ngôn ngữ output, ví dụ: "write in Chinese", "viết bằng tiếng Trung", `写汉语`, `用中文回答`.
- Nếu policy cho phép dịch/viết bằng ngôn ngữ đó, bot phải viết lại câu trả lời trước đó thay vì từ chối.
- Nếu policy thực sự chỉ cho tiếng Việt, bot không nên dịch sang tiếng Trung ở bất kỳ path nào; response cần nhất quán.

### Test case tối thiểu

| Test | Input | Expected |
|---|---|---|
| Chinese query | `所有车型` | Bot không mặc định trả lời tiếng Việt nếu user đang dùng tiếng Trung; bot trả lời tiếng Trung hoặc hỏi lại ngôn ngữ. |
| Chinese correction | `我看不懂。你可以写汉语吗？` | Bot viết lại nội dung trước bằng tiếng Trung. |
| Vietnamese correction | `dịch phần tư vấn giá xe của bạn sang tiếng Trung` | Bot dịch sang tiếng Trung. |
| Consistency | So sánh 2 correction trên | Hai path phải cùng thành công hoặc cùng bị policy từ chối, không mâu thuẫn. |

## 7. Kết luận

Finding này đổi SPEC ở phần **failure mode** và **correction path**. Vấn đề cần sửa không nằm ở nội dung bảng giá xe, mà nằm ở khả năng hiểu correction về ngôn ngữ. Nếu Moni đã có khả năng dịch sang tiếng Trung, product cần cho phép user kích hoạt khả năng đó bằng chính tiếng Trung, không bắt user phải biết prompt lại bằng tiếng Việt.
