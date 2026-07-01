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
        feedback_repo,
        conversation_service

    ):
        
        self.qdrant = get_qdrant_client()

        self.conversation_service = conversation_service
        self.feedback_repo = feedback_repo
        self.s3_base_url = settings.S3_BUCKET_NAME
        # self.bedrock = boto3.client("bedrock-runtime",region_name=settings.REGION)
        self.S3_FILE_URL = settings.S3_BASE_FILE_URL
        
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
        print('\n---------------course_name--------------\n')
        print(course_name, '\n---------------course_name--------------\n')
        print('\n---------------course_name--------------\n')
        if not conversation_id:
            conversation_id = uuid4()
            step = self._get_step_mode(coach_mode, voice_mode, user_message)

            chat_title = await generate_chat_title(user_message, initial_message)

            await self.conversation_service.get_or_create_conversation(conversation_id, user_id, node_id, course_id, chat_title["chat_title"], user_id, "ACTIVE", step)

            await self.conversation_service.add_message(
                conversation_id,
                user_id,
                'BOT',
                initial_message,
            )
        if step not in ['done']:
            conversation = await self.conversation_service.get_conversation(conversation_id)
            step = conversation.step
        if checkboxed_message:
            await self.conversation_service.update_conversation(conversation_id, user_id, node_id, course_id, None, user_id, "ACTIVE", step,  checkboxed_message.get("html"), checkboxed_message.get("key") )

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
        print('\n---------------docs_task--------------\n')
        print(docs_task, '\n---------------docs_task--------------\n')
        print('\n---------------docs_task--------------\n')
        
        feedback = await self.feedback_repo.get_top_feedbacks(organization_id, course_id)
            
        docs = await docs_task
        package_name = self._extract_package_name(docs)
        print('\n---------------package_name--------------\n')
        print(package_name, '\n---------------package_name--------------\n')

        stringified_docs = self._build_rag_context(docs, coach_mode)

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
            feedback_string=[val for val in feedback if val is not None],
            step_description=step_description,
            step = step_override
        )

        return {
            "streaming_metadata": {
                "prompt": prompt,
                "user_message": user_message,
                "voice_mode": voice_mode,
                "citation_html": citation_html,
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
    print('\n---------------get_context_history--------------\n')
    print('\n---------------get_context_history--------------\n')
    print('\n---------------get_context_history--------------\n')

    async def _generate_embedding(self,text: str,) -> list[float]:
        return await asyncio.to_thread(embed_text, text)
    print('\n---------------_generate_embedding--------------\n')
    print('\n---------------_generate_embedding--------------\n')

    
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

            print(f"Querying Qdrant for orgid: {orgid}, course_id: {course_id}, query: {query}")
            # collection_info = self.qdrant.get_collection(QDRANT_COLLECTION)

            results = self.qdrant.query_points(
                collection_name=QDRANT_COLLECTION,
                limit=k,
                query=await self._normalize_vector(embedding),
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="course_id",
                            match=MatchValue(value=str(course_id))
                        )
                    ]
                ),
                
                with_payload=True,
                # Remove: projection={"vector": NamedVector(name="embedding")}
                # Your collection uses Default vector (unnamed), and you don't need
                # vectors returned since you only use match.payload below
            )
            print("\n---------------Qdrant query results--------------\n")
            print(f"Qdrant query results: {results.points if results else 'No results'}")

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
                try:
                    chunk_ids.append(UUID(chunk_id))
                except Exception:
                    continue

        if not chunk_ids:
            return []

        docs = await self.conversation_service.get_chunk_context(
            chunk_ids
        )
        
        if not docs:
            return []

        relevant_docs = []

        for doc in docs:
            text = doc.get("chunk_text")
            if not text or not text.strip():
                continue

            relevant_docs.append({
                "relevant_text": text,
                "imageKeys": doc.get("image_keys") or [],
                "fileName": doc.get("fileName"),
                "s3Location": doc.get("s3Location"),
                "description": doc.get("description") or "",
                "slide_index": doc.get("slideindex"),
                "slide_title": doc.get("slidetitle") or "",
                "document_id": doc.get("module_id"),
                "package_name": doc.get("course_name"),
                "chunk_id": doc.get("chunk_id"),
                "course_id": doc.get("course_id"),
            })

        return relevant_docs



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

        document_id_clean = doc.get("document_id") or ""

        image_tags = []

        for img in image_keys:
            full_path = (
                f"{self.S3_FILE_URL}/material/"
                f"{organization_id}/{extension}/"
                f"{course_id}/{document_id_clean}/images/{img}"
            )
            image_tags.append(full_path)

        return image_tags

    def _build_rag_context(self, docs: list[dict], coach_mode: bool) -> str:
        """
        Converts retrieved docs into LLM-readable context block.
        """

        if not docs:
            return ""

        stringified_doc_list = []

        for doc in docs:
            file_name = doc.get("fileName") or "Unknown Document"
            description = doc.get("description") or ""
            text = doc.get("relevant_text") or ""
            slide_index = doc.get("slide_index")
            slide_title = doc.get("slide_title") or ""

            if not text.strip():
                continue

            page_str = f"Page: {slide_index}" if slide_index is not None else ""
            title_str = f"Title: {slide_title}" if slide_title else ""

            block = f"""
                SOURCE
                Document: {file_name}
                Document_Description: {description}
                {page_str}
                {title_str}
                {text}
            """

            images = self._build_image_urls(
                doc,
                doc.get("organization_id", ""),
                doc.get("course_id", "")
            )

            if images and coach_mode:
                block += "\n\nImage URLs:\n" + "\n".join(images)
            else:
                block += f"\n\nImage URLs:\n[No images found for this slide de {slide_index if slide_index is not None else ''}"

            stringified_doc_list.append(block.strip())

        return "\n\n".join(stringified_doc_list)
    
    def _build_citation_html(
        self,
        docs: list[dict],
        package_name: str | None,
    ) -> str:
        if not docs or not package_name:
            return ""

        file_citations: dict[str, dict] = {}
        print('\n---------------docs--------------\n')
        print(docs, '\n---------------docs--------------\n')
        for doc in docs:
            file_name = doc.get("fileName")
            s3_path = doc.get("s3Location")
            print(f"-----Processing doc--------: file_name={file_name}, s3_path={s3_path}")
            if not file_name or not s3_path:
                continue

            file_name_lower = file_name.lower()

            entry = file_citations.setdefault(
                file_name,
                {
                    "file_url": f"{self.S3_FILE_URL}/{s3_path}",
                    "pages": set(),
                    "modules": set(),
                },
            )

            if file_name_lower.endswith(".zip"):
                slide_title = doc.get("slide_title")
                if slide_title:
                    entry["modules"].add(slide_title)
            else:
                slide_index = doc.get("slide_index")
                if slide_index is not None:
                    entry["pages"].add(int(slide_index))

        citation_blocks = []

        for file_name, entry in file_citations.items():
            file_name_lower = file_name.lower()

            is_pdf = file_name_lower.endswith(".pdf")
            is_docx = file_name_lower.endswith(".docx")
            is_zip = file_name_lower.endswith(".zip")

            final_url = entry["file_url"]

            pages = sorted(entry["pages"])
            modules = sorted(entry["modules"])

            # Add PDF page anchor
            if is_pdf and pages:
                final_url = f"{final_url}#page={pages[0]}"

            # Build details section
            if is_docx:
                details = ""
            elif is_zip:
                details = (
                    f"Modules: {', '.join(modules)}"
                    if modules
                    else ""
                )
            else:
                details = (
                    f"Pages: {', '.join(map(str, pages))}"
                    if pages
                    else ""
                )

            citation_blocks.append(
                f"""
                    <strong>File:</strong>
                    <a href="{final_url}" target="_blank">{file_name}</a><br/>
                    {details if details else ""}
                """
            )
        
        
        if not citation_blocks:
            return ""
        
        cite = f"""
            <div class="citations" style="margin-top:10px;font-size:small;font-style:italic;">
                <em>Information taken from {package_name}</em><br/><br/>
                {"<br/><br/>".join(citation_block for citation_block in citation_blocks)}
            </div>
        """
        print("\n--------------cite----------------\n",cite)
        return cite
    
    def _get_intent_mode(self, intent):
        return get_interation_mode(intent) if intent else None
    
    def _get_policy_by_decision_mode(self, decision_mode):
        return get_policy_by_decision_mode(decision_mode) if decision_mode else None
