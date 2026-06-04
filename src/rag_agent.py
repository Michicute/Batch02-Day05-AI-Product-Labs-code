from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


ROOT = Path(__file__).resolve().parents[1]
QA_PATH = ROOT / "data_clean.csv"
MEDICINE_PATH = ROOT / "medicine_clean.csv"

load_dotenv(ROOT / ".env")


@dataclass(frozen=True)
class Document:
    doc_id: str
    source: str
    title: str
    text: str
    metadata: dict[str, str]


@dataclass(frozen=True)
class RetrievedDocument:
    document: Document
    score: float


def _safe_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def load_documents(
    qa_path: Path = QA_PATH,
    medicine_path: Path = MEDICINE_PATH,
) -> list[Document]:
    documents: list[Document] = []

    qa_df = pd.read_csv(qa_path)
    for idx, row in qa_df.iterrows():
        qtype = _safe_text(row["qtype"])
        question = _safe_text(row["Question"])
        answer = _safe_text(row["Answer"])
        text = (
            f"Question type: {qtype}\n"
            f"Question: {question}\n"
            f"Answer: {answer}"
        )
        documents.append(
            Document(
                doc_id=f"qa-{idx}",
                source="medical_qa",
                title=question,
                text=text,
                metadata={
                    "qtype": qtype,
                    "question": question,
                },
            )
        )

    medicine_df = pd.read_csv(medicine_path)
    for idx, row in medicine_df.iterrows():
        name = _safe_text(row["Medicine Name"])
        composition = _safe_text(row["Composition"])
        uses = _safe_text(row["Uses"])
        side_effects = _safe_text(row["Side_effects"])
        manufacturer = _safe_text(row["Manufacturer"])
        excellent = _safe_text(row["Excellent Review %"])
        average = _safe_text(row["Average Review %"])
        poor = _safe_text(row["Poor Review %"])
        text = (
            f"Medicine: {name}\n"
            f"Composition: {composition}\n"
            f"Uses: {uses}\n"
            f"Side effects: {side_effects}\n"
            f"Manufacturer: {manufacturer}\n"
            f"Reviews: excellent {excellent}%, average {average}%, poor {poor}%"
        )
        documents.append(
            Document(
                doc_id=f"medicine-{idx}",
                source="medicine_catalog",
                title=name,
                text=text,
                metadata={
                    "medicine_name": name,
                    "composition": composition,
                    "uses": uses,
                    "side_effects": side_effects,
                    "manufacturer": manufacturer,
                    "excellent_review_pct": excellent,
                    "average_review_pct": average,
                    "poor_review_pct": poor,
                },
            )
        )

    return documents


class RagAgent:
    def __init__(self, documents: Iterable[Document] | None = None) -> None:
        self.documents = list(documents or load_documents())
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95,
            sublinear_tf=True,
            strip_accents="unicode",
        )
        self.matrix = self.vectorizer.fit_transform(
            f"{doc.title}\n{doc.text}" for doc in self.documents
        )

    def retrieve(
        self,
        question: str,
        top_k: int = 5,
        source_filter: str | None = None,
    ) -> list[RetrievedDocument]:
        query_vector = self.vectorizer.transform([question])
        scores = cosine_similarity(query_vector, self.matrix).ravel()
        source_filter = source_filter or self._auto_source_filter(question)
        if source_filter:
            for idx, doc in enumerate(self.documents):
                if doc.source != source_filter:
                    scores[idx] = -1

        candidate_indices = scores.argsort()[::-1][: max(top_k * 8, top_k)]
        retrieved: list[RetrievedDocument] = []
        seen_medicine_titles: set[str] = set()
        for i in candidate_indices:
            if scores[i] <= 0:
                continue
            doc = self.documents[i]
            if doc.source == "medicine_catalog":
                title_key = doc.title.lower()
                if title_key in seen_medicine_titles:
                    continue
                seen_medicine_titles.add(title_key)
            retrieved.append(RetrievedDocument(document=doc, score=float(scores[i])))
            if len(retrieved) >= top_k:
                break
        return retrieved

    def answer(
        self,
        question: str,
        top_k: int = 5,
        use_llm: bool | None = None,
        model: str | None = None,
        source_filter: str | None = None,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> dict[str, object]:
        retrieval_question = self._contextualized_question(question, conversation_history)
        retrieved = self.retrieve(
            retrieval_question,
            top_k=top_k,
            source_filter=source_filter,
        )
        if use_llm is None:
            use_llm = bool(os.environ.get("OPENAI_API_KEY"))

        if use_llm:
            answer_text = self._llm_answer(
                question=question,
                retrieved=retrieved,
                model=model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
                conversation_history=conversation_history,
            )
        else:
            answer_text = self._extractive_answer(question, retrieved)

        return {
            "question": question,
            "retrieval_question": retrieval_question,
            "answer": answer_text,
            "sources": [
                {
                    "doc_id": item.document.doc_id,
                    "source": item.document.source,
                    "title": item.document.title,
                    "score": round(item.score, 4),
                    "metadata": item.document.metadata,
                }
                for item in retrieved
            ],
        }

    def _auto_source_filter(self, question: str) -> str | None:
        q = question.lower()
        medicine_markers = [
            "medicine",
            "medicines",
            "drug",
            "drugs",
            "tablet",
            "syrup",
            "injection",
            "capsule",
            "composition",
            "thành phần",
            "hoạt chất",
            "manufacturer",
            "nhà sản xuất",
            "side effect",
            "side effects",
            "tác dụng phụ",
            "review",
            "used for",
        ]
        if any(marker in q for marker in medicine_markers):
            return "medicine_catalog"
        return None

    def _recent_user_questions(
        self,
        conversation_history: list[dict[str, str]],
    ) -> list[str]:
        return [
            turn.get("content", "")
            for turn in conversation_history[-8:]
            if turn.get("role") == "user" and turn.get("content")
        ]

    def _contextualized_question(
        self,
        question: str,
        conversation_history: list[dict[str, str]] | None,
    ) -> str:
        if not conversation_history:
            return question

        if not self._looks_like_follow_up(question):
            return question

        recent_turns = conversation_history[-6:]
        context_lines = []
        for turn in recent_turns:
            role = turn.get("role", "").strip()
            content = turn.get("content", "").strip()
            if role != "user":
                continue
            if not role or not content:
                continue
            if len(content) > 900:
                content = content[:900].rstrip() + "..."
            context_lines.append(f"{role}: {content}")

        if not context_lines:
            return question

        return (
            "Conversation context:\n"
            f"{chr(10).join(context_lines)}\n\n"
            f"Current question: {question}"
        )

    def _looks_like_follow_up(self, question: str) -> bool:
        q = question.lower().strip()
        follow_up_markers = [
            "nó",
            "đó",
            "cái đó",
            "cái này",
            "thuốc này",
            "bệnh này",
            "triệu chứng này",
            "vậy",
            "còn",
            "tiếp",
            "so sánh",
            "liều dùng",
            "liều",
            "mấy tuổi",
            "bao nhiêu tuổi",
            "độ tuổi",
            "tuổi nào",
            "trẻ mấy tuổi",
            "dùng được không",
            "dùng được",
            "có dùng được",
            "được dùng",
            "tác dụng phụ",
            "nguy hiểm không",
            "how about",
            "what about",
            "that",
            "this",
            "it",
        ]
        if any(marker in q for marker in follow_up_markers):
            return True

        words = q.split()
        return len(words) <= 5 and q.endswith("?")

    def _extractive_answer(
        self,
        question: str,
        retrieved: list[RetrievedDocument],
    ) -> str:
        if not retrieved:
            return (
                "Mình chưa tìm thấy nguồn phù hợp trong hai bộ dữ liệu đã làm sạch. "
                "Bạn có thể hỏi cụ thể hơn bằng tên thuốc, tên bệnh, triệu chứng, "
                "hướng điều trị, thành phần hoặc nhà sản xuất."
            )

        lines = [
            "Mình tìm thấy các bản ghi liên quan trong dữ liệu cục bộ:",
        ]
        for idx, item in enumerate(retrieved[:3], start=1):
            doc = item.document
            preview = doc.text.replace("\n", " ")
            if len(preview) > 650:
                preview = preview[:650].rstrip() + "..."
            lines.append(
                f"\n{idx}. [{doc.source}] {doc.title} "
                f"(score: {item.score:.3f})\n{preview}"
            )
        return "\n".join(lines)

    def _llm_answer(
        self,
        question: str,
        retrieved: list[RetrievedDocument],
        model: str,
        conversation_history: list[dict[str, str]] | None = None,
    ) -> str:
        from openai import OpenAI

        context_blocks = []
        for idx, item in enumerate(retrieved, start=1):
            context_blocks.append(
                f"[{idx}] source={item.document.source}; title={item.document.title}; "
                f"score={item.score:.4f}\n{item.document.text}"
            )
        context = "\n\n".join(context_blocks) or "No retrieved context."
        history = self._format_history_for_prompt(conversation_history)
        answer_language = self._detect_answer_language(question)

        client = OpenAI()
        response = client.responses.create(
            model=model,
            temperature=0,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are a cautious medical Q&A assistant answering medical questions only. "
                        "Always answer in the requested answer language. "
                        "Prefer the retrieved "
                        "context when it is available, and cite retrieved sources with "
                        "bracket numbers like [1]. If no relevant context is available, "
                        "answer using general medical knowledge, say that no local source "
                        "was found, and do not invent citations. Do not diagnose. "
                        "Encourage professional medical advice for urgent, risky, or "
                        "personal treatment decisions."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Answer language: {answer_language}\n\n"
                        f"Recent conversation:\n{history}\n\n"
                        f"Question: {question}\n\n"
                        f"Retrieved context:\n{context}"
                    ),
                },
            ],
        )
        return response.output_text

    def _detect_answer_language(self, question: str) -> str:
        q = question.lower()
        vietnamese_markers = [
            "ă",
            "â",
            "đ",
            "ê",
            "ô",
            "ơ",
            "ư",
            "á",
            "à",
            "ả",
            "ã",
            "ạ",
            "é",
            "è",
            "ẻ",
            "ẽ",
            "ẹ",
            "í",
            "ì",
            "ỉ",
            "ĩ",
            "ị",
            "ó",
            "ò",
            "ỏ",
            "õ",
            "ọ",
            "ú",
            "ù",
            "ủ",
            "ũ",
            "ụ",
            "ý",
            "ỳ",
            "ỷ",
            "ỹ",
            "ỵ",
            "thuốc",
            "bệnh",
            "thành phần",
            "triệu chứng",
            "điều trị",
        ]
        if any(marker in q for marker in vietnamese_markers):
            return "Vietnamese"
        return "the same language as the user's question"

    def _format_history_for_prompt(
        self,
        conversation_history: list[dict[str, str]] | None,
    ) -> str:
        if not conversation_history:
            return "No previous conversation."

        lines = []
        for turn in conversation_history[-6:]:
            role = turn.get("role", "").strip()
            content = turn.get("content", "").strip()
            if not role or not content:
                continue
            if len(content) > 1200:
                content = content[:1200].rstrip() + "..."
            lines.append(f"{role}: {content}")
        return "\n".join(lines) if lines else "No previous conversation."


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the local medicine + medical QA RAG agent.")
    parser.add_argument("question", nargs="+", help="Question to ask.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of retrieved records.")
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Use OpenAI generation. Requires OPENAI_API_KEY.",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Force extractive answers, even when OPENAI_API_KEY exists.",
    )
    args = parser.parse_args()

    question = " ".join(args.question)
    use_llm = True if args.llm else None
    if args.no_llm:
        use_llm = False

    agent = RagAgent()
    result = agent.answer(question, top_k=args.top_k, use_llm=use_llm)
    print(result["answer"])
    print("\nSources:")
    for source in result["sources"]:
        print(
            f"- {source['doc_id']} | {source['source']} | "
            f"{source['title']} | score={source['score']}"
        )


if __name__ == "__main__":
    main()
