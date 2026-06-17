"""
Embedding A/B/C evaluation harness.

Runs a fixed question set through the real retrieval + answer path and captures, per
question: the top-k retrieved chunks with Qdrant similarity scores AND the generated
answer (llama3.1:8b). The LLM and prompt are held constant so the only variable is the
embedding configuration.

Cases (ingestion / query embedding model):
  1: bge   / bge
  2: titan / bge     (mismatched vector spaces — expected to retrieve poorly)
  3: titan / titan

The INGESTION model is whatever the collection was last built with, so RE-INDEX FIRST
when it changes (see scripts/reindex_embeddings.py). This script controls the QUERY
embedding per --case and never re-indexes.

Usage:
    # Case 1
    set INGEST_EMBED_PROVIDER=bge & python -m scripts.reindex_embeddings
    python -m scripts.embed_eval --case 1 --course-id <uuid>

    # Case 3
    set INGEST_EMBED_PROVIDER=titan & python -m scripts.reindex_embeddings
    python -m scripts.embed_eval --case 3 --course-id <uuid>

    # Case 2 (reuse the Case 3 / titan index — no re-index)
    python -m scripts.embed_eval --case 2 --course-id <uuid>
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path
from uuid import UUID

# Windows: async psycopg needs the selector loop, not the default proactor loop.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from qdrant_client.models import Filter, FieldCondition, MatchValue

from core.config import settings
from core.embeddings import embed_query
from core.llm import generate
from core.db import AsyncSessionLocal
from workers.qdrnt_vector import get_qdrant_client, QDRANT_COLLECTION, normalize_vector
from chat_stream.repositories.postgres.course_repository import PostgresCourseRepository
from chat_stream.prompt_template import getPromptTemplate

TOP_K = 4
QUESTIONS_FILE = Path(__file__).parent / "eval_questions.json"

# (ingestion provider, query provider) per case — ingestion is informational here
# (the collection must already be built with it); query is applied at runtime.
CASE_PROVIDERS = {
    1: ("bge", "bge"),
    2: ("titan", "bge"),
    3: ("titan", "titan"),
}


async def retrieve(question: str, course_id: str, db):
    embedding = await asyncio.to_thread(embed_query, question)
    resp = await asyncio.to_thread(
        get_qdrant_client().query_points,
        collection_name=QDRANT_COLLECTION,
        query=normalize_vector(embedding),
        limit=TOP_K,
        query_filter=Filter(
            must=[FieldCondition(key="course_id", match=MatchValue(value=str(course_id)))]
        ),
        with_payload=True,
    )

    scores: dict[str, float] = {}
    chunk_ids: list[UUID] = []
    for p in resp.points:
        cid = (p.payload or {}).get("chunk_id")
        if cid:
            scores[cid] = p.score
            chunk_ids.append(UUID(cid))

    if not chunk_ids:
        return [], scores

    repo = PostgresCourseRepository(db)
    docs = await repo.get_chunk_context(chunk_ids)
    docs = sorted(docs, key=lambda d: scores.get(str(d["chunk_id"]), 0.0), reverse=True)
    return docs, scores


def build_context(docs: list[dict]) -> str:
    return "\n\n".join(
        f"Module: {d.get('module_name')}\nText: {d.get('chunk_text', '')}" for d in docs
    )


async def answer(question: str, context: str) -> str:
    prompt = getPromptTemplate(
        coach_mode=False,
        voice_mode=False,
        context_history="",
        stringified_docs=context,
        user_message=question,
        citation_html="",
        user_name="Tester",
        core_principle=None,
        interaction_mode=None,
        feedback_string="",
        step_description=None,
        step="done",
    )
    # Mirror production: instructions/context in system, the question as the user turn.
    return await generate(prompt=question, system=prompt, max_tokens=2048, temperature=0.4)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", type=int, choices=[1, 2, 3], required=True)
    parser.add_argument("--course-id", required=True)
    args = parser.parse_args()

    ingest_p, query_p = CASE_PROVIDERS[args.case]
    settings.QUERY_EMBED_PROVIDER = query_p  # applied to embed_query at runtime

    questions = json.loads(QUESTIONS_FILE.read_text(encoding="utf-8"))

    print(f"Case {args.case}: ingestion={ingest_p}, query={query_p}, course={args.course_id}")
    print(f"Running {len(questions)} questions...")

    lines = [
        f"# Embedding Eval — Case {args.case}",
        "",
        f"- **Ingestion model:** {ingest_p}",
        f"- **Query model:** {query_p}",
        f"- **Course:** `{args.course_id}`",
        f"- **top_k:** {TOP_K}  |  **LLM:** {settings.OLLAMA_MODEL}",
        "",
    ]

    top1_scores = []
    hits = 0

    async with AsyncSessionLocal() as db:
        for i, q in enumerate(questions, 1):
            print(f"  Q{i}: {q[:60]}...")
            docs, scores = await retrieve(q, args.course_id, db)
            lines.append(f"## Q{i}: {q}")

            if not docs:
                lines.append("\n_No chunks retrieved._\n")
                ans = await answer(q, "")
            else:
                hits += 1
                top1_scores.append(max(scores.values()))
                lines.append("")
                lines.append("| rank | score | module | snippet |")
                lines.append("|------|-------|--------|---------|")
                for rank, d in enumerate(docs, 1):
                    sc = scores.get(str(d["chunk_id"]), 0.0)
                    snip = (d.get("chunk_text") or "")[:120].replace("\n", " ").replace("|", "\\|")
                    lines.append(f"| {rank} | {sc:.4f} | {d.get('module_name')} | {snip} |")
                ans = await answer(q, build_context(docs))

            lines.append("\n**Answer:**\n")
            lines.append(str(ans))
            lines.append("\n---\n")

    avg_top1 = sum(top1_scores) / len(top1_scores) if top1_scores else 0.0
    summary = (
        f"\n## Summary\n"
        f"- Questions: {len(questions)}\n"
        f"- With ≥1 retrieved chunk: {hits}\n"
        f"- Avg top-1 score: {avg_top1:.4f}\n"
    )
    lines.insert(7, summary)  # place summary near the top, after the header block

    out = Path(__file__).parent / f"eval_results_case{args.case}.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Done. Wrote {out}")


if __name__ == "__main__":
    asyncio.run(main())
