from workers.extractors.docx import chunk_and_embed_docx
from workers.extractors.pdf import  chunk_and_embed_pdf
import os
import boto3

S3_BUCKET = os.environ.get("S3_BUCKET_NAME")
REGION = os.environ.get("REGION")
s3_client = boto3.client("s3", region_name=REGION)


async def process_document_internal(payload: dict):
    org_id = payload["organization_id"]
    course_id = payload["course_id"]
    course_name = payload["course_name"]
    document_id = payload["module_id"]
    s3_key = payload["s3_key"]
    db = payload["db"]
    # Read file from S3
    obj = s3_client.get_object(Bucket=S3_BUCKET, Key=s3_key)
    file_bytes = obj["Body"].read()

    print(f"Processing file from S3: {s3_key}")

    # if s3_key.endswith(".zip"):
    #     return handle_zip_file(org_id, course_id, course_name, document_id, file_bytes,S3_BUCKET)

    if s3_key.endswith(".pdf"):
       content_objects_json = await chunk_and_embed_pdf(file_bytes, document_id, course_id,org_id,course_name, db)
       print(content_objects_json, 'content_objects_jsoncontent_objects_json')
    
    # elif s3_key.endswith(".pptx"):
    #     pptimages(file_bytes=file_bytes,document_id=document_id,course_id=course_id,org_id=org_id,course_name=course_name,S3_BUCKET=S3_BUCKET)

    elif  s3_key.endswith(".docx"):
        return await chunk_and_embed_docx(file_bytes, org_id, course_id, course_name, document_id, db)

    # elif  s3_key.endswith(".txt"):
    #     txt_json = extract_txt_pages(file_bytes)
    #     return chunk_and_embed_text_document(txt_json, org_id, course_id, course_name, document_id)



    else:
        raise ValueError("Unsupported file type")
    