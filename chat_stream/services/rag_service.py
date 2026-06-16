from uuid import UUID, uuid4
from fastapi import HTTPException
from typing import List, Dict, Any
import asyncio
from qdrant_client.models import Filter, FieldCondition, MatchValue
from core.config import settings
from core.embeddings import embed_text
from workers.qdrnt_vector import get_qdrant_client, QDRANT_COLLECTION, normalize_vector


from chat_stream.user_message_analyzer import analyze_user_message
from chat_stream.prompt_template import getPromptTemplate
from chat_stream.modes import get_interation_mode, get_policy_by_decision_mode
from chat_stream.generate_title import generate_chat_title
from chat_stream.steps_snippet import get_step_details
from datetime import datetime
from core.config import Settings
class RagService:

    def __init__(
        self,
        course_repo,
        feedback_repo,
        conversation_service

    ):
        self.course_repository = course_repo
        self.conversation_service = conversation_service
        self.feedback_repo = feedback_repo
        self.s3_base_url = settings.S3_BUCKET_NAME

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
            # Guard against an unknown/stale chat_id: if the conversation doesn't
            # exist, fall back to deriving the step instead of crashing on None.
            step = conversation.step if conversation else self._get_step_mode(
                coach_mode, voice_mode, user_message
            )

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
        
        feedback_task = self.feedback_repo.get_top_feedbacks(organization_id, course_id)

        docs, feedback = await asyncio.gather(docs_task, feedback_task)

        package_name = self._extract_package_name(docs)

        stringified_docs = self._build_rag_context(docs)

        citation_html = self._build_citation_html(docs, package_name)

        interaction_mode = self._get_intent_mode(intent)

        core_principle = self._get_policy_by_decision_mode(decision_mode)

        step_override = self._handle_step_override(intent, step, voice_mode)
        
        course = await self.course_repository.get_course(course_id)

        await self.conversation_service.get_or_create_conversation(conversation_id, user_id, node_id, course_id, None, user_id, "ACTIVE", step)

        message = await self.conversation_service.add_message(
            conversation_id,
            user_id,
            'USER',
            user_message,
        )


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

        obj = {
            "streaming_metadata": {
                "prompt": prompt,
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


        return obj

    # save
    async def save(self, user: str, data: dict) -> Dict:
        full_response = data.get("full_response")
        conversation_id = data.get("chat_id")
        user_id = user['sub']
        step = data.get("next_step") or "done"
        if not full_response:
            raise HTTPException(status_code=400, detail="Missing full_response")

        message = await self.conversation_service.add_message(
            conversation_id,
            user_id,
            'BOT',
            full_response,
        )

        await asyncio.gather(
            self.conversation_service.update_step(conversation_id, step),
            self.conversation_service.save_message_cache(conversation_id, user_id, 'BOT', full_response,)
        )


        return {"message": "saved success"}
    
    def _build_context(self, chat_history, coach_mode, voice_mode):
        max_history = 20 if coach_mode and not voice_mode else 4
        history_list = list(chat_history) if chat_history else []
        recent = history_list[-max_history:]if history_list else []        
        
        return "\n".join([
            f"{m.sender}: {m.msgtxt}"
            for m in recent
        ])


    async def get_context_history(self, conversation_id, user_id, limit: int = 20,) -> str:
        messages = await self.conversation_service.get_context(conversation_id, user_id)
        return messages or []


    async def _generate_embedding(self,text: str,) -> list[float]:
        return await asyncio.to_thread(embed_text, text)

    async def retrieve_relevant_docs(self, orgid: str, query: str, course_id: str, k: int) -> list[dict]:

        try:
            embedding = await self._generate_embedding(query)

            if not embedding:
                return []

            response = await asyncio.to_thread(
                get_qdrant_client().query_points,
                collection_name=QDRANT_COLLECTION,
                query=normalize_vector(embedding),
                limit=k,
                query_filter=Filter(
                    must=[FieldCondition(
                        key="course_id",
                        match=MatchValue(value=str(course_id)),
                    )]
                ),
                with_payload=True,
            )
            results = response.points
            print(f"Vector search results for query '{query}': {results}")


        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Vector search failed: {str(e)}"
            )

        if not results:
            return []

        chunk_ids = []

        for point in results:
            payload = point.payload or {}

            chunk_id = payload.get("chunk_id")

            if chunk_id:
                chunk_ids.append(UUID(chunk_id))

        if not chunk_ids:
            return []

        docs = await self.course_repository.get_chunk_context(
            chunk_ids
        )
        print(f"Retrieved documents for chunk IDs {chunk_ids}: {docs}")

        data = [
            {
                "chunk_id": doc["chunk_id"],
                "relevant_text": doc["chunk_text"],
                "image_keys": doc["image_keys"],
                "module_id": doc["module_id"],
                "module_name": doc["module_name"],
                "module_type": doc["module_type"],
                "module_loc": doc["module_loc"],
                "course_id": doc["course_id"],
                "course_name": doc["course_name"],
                "organization_id": orgid,
            }
            for doc in docs
        ]
        print(f"Retrieved documents for query '{query}': {data}")
        return data

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

        # The course acts as the "package" the retrieved material belongs to.
        return docs[0].get("course_name")

    def _build_image_urls(self, doc: dict) -> list[str]:
        """
        Build S3 image URLs for a chunk, mirroring the ingestion layout:
            material/{org}/{type}/{course}/{module}/images/{key}
        (see workers/extractors/*.py). image_keys come from Chunk.imgkeys.
        """

        image_keys = doc.get("image_keys") or []
        if not image_keys:
            return []

        org_id = doc.get("organization_id", "")
        course_id = str(doc.get("course_id", ""))
        module_id = str(doc.get("module_id", ""))
        module_type = (doc.get("module_type") or "").lower()

        return [
            f"{self.s3_base_url}/material/{org_id}/{module_type}/"
            f"{course_id}/{module_id}/images/{img}"
            for img in image_keys
        ]

    def _build_rag_context(self, docs: list[dict]) -> str:
        """
        Converts retrieved docs into an LLM-readable context block using the
        fields actually available from Postgres (module + course + chunk text).
        """

        if not docs:
            return ""

        stringified_doc_list = []

        for doc in docs:
            block = f"""
                SOURCE
                Module: {doc.get('module_name')}
                Type: {doc.get('module_type')}
                Course: {doc.get('course_name')}
                Text: {doc.get('relevant_text', '')}
            """

            images = self._build_image_urls(doc)
            if images:
                block += "\nImages:\n" + "\n".join(images)

            stringified_doc_list.append(block)

        return "\n\n".join(stringified_doc_list)

    def _build_citation_html(self, docs: list[dict], package_name: str | None) -> str:
        """
        Builds an HTML citation block from retrieved documents, grouped by module.
        Links to the module's stored location (Module.loc) when available.
        """

        if not docs:
            return ""

        # Group by module name, keeping the first known location for each.
        modules: dict[str, str | None] = {}
        for doc in docs:
            name = doc.get("module_name")
            if not name:
                continue
            modules.setdefault(name, doc.get("module_loc"))

        if not modules:
            return ""

        citation_blocks = []
        for name, loc in modules.items():
            if loc:
                citation_blocks.append(
                    f'<strong>File:</strong> '
                    f'<a href="{loc}" target="_blank">{name}</a>'
                )
            else:
                citation_blocks.append(f"<strong>File:</strong> {name}")

        package_line = (
            f"<em>Information taken from {package_name}</em><br/><br/>"
            if package_name else ""
        )

        return f"""
            <div class="citations" style="margin-top:10px;font-size:small;font-style:italic;">
            {package_line}{"<br/><br/>".join(citation_blocks)}
            </div>
        """
 
    def _get_intent_mode(self, intent):
        return get_interation_mode(intent) if intent else None
    
    def _get_policy_by_decision_mode(self, decision_mode):
        return get_policy_by_decision_mode(decision_mode) if decision_mode else None
