from uuid import UUID, uuid4
from fastapi import HTTPException
from typing import List, Dict, Any
import asyncio
import numpy as np
from core.config import settings
from core.embeddings import embed_text


from chat_stream.utils.user_message_analyzer import analyze_user_message
from chat_stream.utils.prompt_template import getPromptTemplate
from chat_stream.utils.modes import get_interation_mode, get_policy_by_decision_mode
from chat_stream.utils.generate_title import generate_chat_title
from chat_stream.utils.steps_snippet import get_step_details
from datetime import datetime
from core.config import Settings

from qdrant_client.models import Filter, FieldCondition, MatchValue
from workers.qdrnt_vector import get_qdrant_client, QDRANT_COLLECTION
from qdrant_client.models import NamedVector

class RagService:

    def __init__(
        self,
        course_repo,
        feedback_repo,
        conversation_service

    ):
        
        self.qdrant = get_qdrant_client()
        self.course_repository = course_repo
        self.conversation_service = conversation_service
        self.feedback_repo = feedback_repo
        self.s3_base_url = settings.S3_BUCKET_NAME

        self.QDRANT_URL        = settings.QDRANT_URL
        self.QDRANT_API_KEY    = settings.QDRANT_API_KEY   
        self.QDRANT_COLLECTION = settings.QDRANT_COLLECTION
        self.VECTOR_DIM        = 1024  


    # ENTRY POINT
    async def execute(self, user: str,data: dict) -> Dict:
        user_message = data["active_message"]
        course_id = data["course_id"]
        course_name = data["course_name"]
        coach_mode = data["coach_mode"]
        voice_mode = data["voice_mode"]
        initial_message = data["initial_message"]
        organization_id = data["orgid"]
        node_id = data["ndid"]
        node_type = data["ndty"]
        user_id = user['sub']
        user_name= user['username']
        conversation_id = data["chat_id"]
        checkboxed_message = data["active_message_checkbox"]
        step = None
        step_description=None
        next_step=None
        if not conversation_id:
            conversation_id = uuid4()
            step = self._get_step_mode(coach_mode, voice_mode, user_message)

            chat_title = await generate_chat_title(user_message, initial_message)

            await self.conversation_service.get_or_create_conversation(conversation_id, user_id, node_id, course_id, chat_title["chat_title"], user_id, "ACTIVE", step)

            message = await self.conversation_service.add_message(
                conversation_id,
                user_id,
                'BOT',
                initial_message,
            )
        if step not in ['done']:
            conversation = await self.conversation_service.get_conversation(conversation_id)
            step = conversation.step
        if checkboxed_message:
            await self.conversation_service.update_message(checkboxed_message.get("html"), checkboxed_message.get("key"), user_id)

        chat_history = await self.get_context_history(conversation_id, user_id)
        
        context_history = self._build_context(chat_history, coach_mode, voice_mode)

        analysis = await analyze_user_message(user_message,context_history,coach_mode,step,voice_mode)

        intent = analysis.get("intent")
        
        decision_mode = analysis.get("decision_mode")
        
        query = analysis.get("search_query", user_message)

        if coach_mode and step not in ['done']:
            step_description, next_step = self._get_step_context(step, coach_mode, voice_mode)

        top_k = self._get_top_k(intent, coach_mode, voice_mode, step)

        docs_task = self.retrieve_relevant_docs(organization_id, query, course_id, top_k)
        
        feedback = await self.feedback_repo.get_top_feedbacks(organization_id, course_id)

        docs = await docs_task
        package_name = self._extract_package_name(docs)

        stringified_docs = self._build_rag_context(docs)

        citation_html = self._build_citation_html(docs, package_name)

        interaction_mode = self._get_intent_mode(intent)

        core_principle = self._get_policy_by_decision_mode(decision_mode)

        step_override = self._handle_step_override(intent, step, voice_mode)
        message = await self.conversation_service.add_message(conversation_id,user_id,'USER',user_message,)
        await self.conversation_service.get_or_create_conversation(conversation_id, user_id, node_id, course_id, None, user_id, "ACTIVE", step)

        await self.conversation_service.save_message_cache(conversation_id, user_id, 'USER', user_message,)

        prompt = getPromptTemplate(
            coach_mode=coach_mode,
            voice_mode=voice_mode,
            context_history=context_history,
            stringified_docs = stringified_docs,
            user_message=user_message,
            citation_html = citation_html,
            user_name=user_name,
            core_principle = core_principle,
            interaction_mode = interaction_mode,
            feedback_string=feedback,
            step_description=step_description,
            step = step_override
        )

        return {
            "streaming_metadata": {
                "prompt": prompt,
                "user_message": user_message,
                "voice_mode": voice_mode
            },
            "storage_metadata": {
                "organization_id": organization_id,
                "node_id": node_id,
                "node_type": node_type,
                "user_id": user_id,
                "course_id": course_id,
                "chat_id": conversation_id,
                "course_name": course_name,
                "next_step": next_step,
                "message_id": message.id
            }
        }

    # save
    async def save(self, user: str, data: dict) -> Dict:
        full_response = data.get("full_response")
        conversation_id = data.get("chat_id")
        user_id = user['sub']
        step = data.get("next_step") or "done"
        if not full_response:
            raise HTTPException(status_code=400, detail="Missing full_response")

        message = await self.conversation_service.add_message(conversation_id, user_id, 'BOT', full_response,)
        await self.conversation_service.update_step(conversation_id, step),
        await self.conversation_service.save_message_cache(conversation_id, user_id, 'BOT', full_response,)


        return {"message": "saved success"}
    
    def _build_context(self, chat_history, coach_mode, voice_mode):
        max_history = 20 if coach_mode and not voice_mode else 4
        history_list = list(chat_history) if chat_history else []
        recent = history_list[-max_history:] if history_list else []        
        
        return "\n".join([
            f"{m.sender}: {m.msgtxt}"
            for m in recent
        ])

    async def get_context_history(self, conversation_id, user_id, limit: int = 20,) -> str:
        messages = await self.conversation_service.get_context(conversation_id, user_id)
        return messages or []

    async def _generate_embedding(self,text: str,) -> list[float]:
        return await asyncio.to_thread(embed_text, text)
    
    async def _normalize_vector(self, vec):
        """L2-normalize a vector so its magnitude becomes 1"""
        if not vec:
            raise ValueError("Empty vector cannot be normalized")

        arr = np.array(vec, dtype=np.float32)
        norm = np.linalg.norm(arr)
        if norm == 0:
            return arr.tolist()
        return (arr / norm).tolist()

    async def retrieve_relevant_docs(self, orgid: str, query: str, course_id: str, k: int) -> list[dict]:

        try:
            embedding = await self._generate_embedding(query)

            if not embedding:
                return []

            # collection_info = self.qdrant.get_collection(QDRANT_COLLECTION)

            results = self.qdrant.query_points(
                collection_name=QDRANT_COLLECTION,
                limit=k,
                query= await self._normalize_vector(embedding),
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="course_id",
                            match=MatchValue(value=str(course_id))
                        )
                    ]
                ),
                with_payload=True,
            )

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Vector search failed: {str(e)}"
            )

        chunk_ids = []

        for match in results.points:
            metadata = match.payload or {}

            chunk_id = metadata.get("chunk_id")

            if chunk_id:
                chunk_ids.append(UUID(chunk_id))

        if not chunk_ids:
            return []

        docs = await self.course_repository.get_chunk_context(
            chunk_ids
        )

        return [
            {
                "chunk_id": doc["chunk_id"],
                "relevant_text": doc["chunk_text"],
                "image_keys": doc["image_keys"],
                "module_id": doc["module_id"],
                "module_name": doc["module_name"],
                "module_type": doc["module_type"],
                "course_id": doc["course_id"],
                "course_name": doc["course_name"],
            }
            for doc in docs
        ]

    def _handle_step_override(self,intent: str,step: str,voice_mode: bool) -> str:
        """
        Handles special step transitions like redo_assessment.
        """

        if intent in ["redo_assessment"] and not voice_mode and step == "done":
            return "assessment"

        return step

    def _get_step_mode(self, coach_mode, voice_mode, user_message):
        if coach_mode and not voice_mode and user_message in ["Guided Journey"]:
            return "assessment"
        else:
            return "done"

    def _get_step_context(self, step: str, coach_mode: bool, voice_mode: bool,):
        """
        Builds step instruction + next step metadata.
        """
        if step in ["done"] or not coach_mode or voice_mode:
            return None, None

        step_details = get_step_details(step)

        if not step_details:
            return None, None

        return (
            step_details.get("instruction", ""),
            step_details.get("next_step", None),
        )

    def _get_top_k(self,intent: str | None,coach_mode: bool,voice_mode: bool,step: str) -> int:
        """
        Determines retrieval depth dynamically.
        """

        low_intents = {"chit_chat", "out_of_scope"}

        if step == "assessment" and coach_mode and not voice_mode:
            return 15

        if intent in low_intents:
            return 2

        if coach_mode and not voice_mode:
            return 7

        return 4

    def _extract_package_name(self,docs: list[dict]) -> str | None:
        """
        Extract package/course name from retrieved docs.
        """

        if not docs:
            return None

        return docs[0].get("package_name")

    def _build_image_urls(self, doc: dict, organization_id: str, course_id: str) -> list[str]:
        """
        Builds S3 image URLs for a document.
        """

        image_keys = doc.get("imageKeys") or []
        extension = (doc.get("fileName") or "").split(".")[-1]

        if not image_keys:
            return []

        course_id_clean = course_id.replace("COURSE#", "")
        document_id_clean = (doc.get("document_id") or "").replace("DOC#", "")

        image_tags = []

        for img in image_keys:
            full_path = (
                f"{self.s3_base_url}/material/"
                f"{organization_id}/{extension}/"
                f"{course_id_clean}/{document_id_clean}/images/{img}"
            )
            image_tags.append(full_path)

        return image_tags

    def _build_rag_context(self, docs: list[dict]) -> str:
        """
        Converts retrieved docs into LLM-readable context block.
        """

        if not docs:
            return ""

        stringified_doc_list = []

        for doc in docs:
            block = f"""
                SOURCE
                Document: {doc.get('fileName')}
                Document_Description: {doc.get('description', '')}
                Text: {doc.get('relevant_text', '')}
            """
            # Page: {doc.get('slide_index')}
            # Title: {doc.get('slide_title')}

            images = self._build_image_urls(
                doc,
                doc.get("organization_id", ""),
                doc.get("course_id", "")
            )

            if images:
                block += "\nImages:\n" + "\n".join(images)
            else:
                block += "\n\n Image URLs: \n" + f"\n [No images found for this slide (...)]."

            stringified_doc_list.append(block)

        return "\n\n".join(stringified_doc_list)
    
    def _build_citation_html(self,docs: list[dict],package_name: str | None) -> str:
        """
        Builds HTML citation block from retrieved documents.
        """

        if not docs or not package_name:
            return ""

        file_citations = {}

        for doc in docs:
            file_name = doc.get("fileName")
            if not file_name:
                continue

            entry = file_citations.setdefault(file_name, {
                "file_url": f"{self.s3_base_url}/{doc.get('s3Location')}",
                "pages": set(),
                "modules": set(),
            })

            if doc.get("slide_index"):
                entry["pages"].add(int(doc["slide_index"]))

            if doc.get("slide_title"):
                entry["modules"].add(doc["slide_title"])

        citation_blocks = []

        for file_name, entry in file_citations.items():

            final_url = entry["file_url"]

            pages = sorted(entry["pages"])
            modules = sorted(entry["modules"])

            if pages:
                final_url = f"{final_url}#page={pages[0]}"

            details = ""

            if modules:
                details = f"Modules: {', '.join(modules)}"
            elif pages:
                details = f"Pages: {', '.join(map(str, pages))}"

            citation_blocks.append(f"""
                    <strong>File:</strong>
                    <a href="{final_url}" target="_blank">{file_name}</a><br/>
                    {details}
                """)

        return f"""
            <div class="citations" style="margin-top:10px;font-size:small;font-style:italic;">
            <em>Information taken from {package_name}</em><br/><br/>
            {"<br/><br/>".join(citation_blocks)}
            </div>
        """
 
    def _get_intent_mode(self, intent):
        return get_interation_mode(intent) if intent else None
    
    def _get_policy_by_decision_mode(self, decision_mode):
        return get_policy_by_decision_mode(decision_mode) if decision_mode else None
