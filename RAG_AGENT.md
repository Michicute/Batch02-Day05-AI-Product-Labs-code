# Medicine Q&A RAG Agent

Agent này dùng hai file clean:

- `data_clean.csv`: medical Q&A theo `qtype`, `Question`, `Answer`
- `medicine_clean.csv`: thông tin thuốc, thành phần, công dụng, tác dụng phụ, nhà sản xuất, review

## Chạy bằng CLI

```bash
python -m src.rag_agent --no-llm "What are the side effects of Augmentin 625 Duo Tablet?"
```

Mặc định agent retrieve bằng TF-IDF local. Không cần API key.

Nếu có `OPENAI_API_KEY`, có thể bật phần sinh câu trả lời:

```bash
python -m src.rag_agent --llm "What are the treatments for breast cancer?"
```

## Chạy giao diện demo

```bash
streamlit run app.py
```

## Cách hoạt động

1. Convert mỗi dòng trong `data_clean.csv` và `medicine_clean.csv` thành một document.
2. Build TF-IDF index bằng `scikit-learn`.
3. Khi user hỏi, retrieve top-k document liên quan nhất.
4. Nếu không dùng LLM, trả về các record liên quan nhất kèm nguồn.
5. Nếu dùng LLM, chỉ cho model trả lời dựa trên context retrieve được.

## Lưu ý an toàn

Đây là prototype Q&A/RAG cho dữ liệu local, không thay thế bác sĩ hoặc tư vấn y tế chuyên môn.
