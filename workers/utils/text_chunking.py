import uuid

def group_images_with_previous_text(content):
    result = []
    current = None
 
    for item in content:
        t = item["text"].strip()
        imgs = item["image"]
        img_txts = item.get("image_texts", [])
 
        if not imgs:  # text only
            if t:
                if current is None or current["image"]:
                    if current:
                        result.append(current)
                    current = {"text": t, "image": []}
                else:
                    current["text"] += "\n" + t
        else:  # image with OCR text
            if current is None:
                current = {"text": "", "image": []}
            current["image"].extend(imgs)
           
            # Append image OCR text to the main text
            for img_txt in img_txts:
                if img_txt:
                    current["text"] += "\n " + img_txt
           
           
 
    if current:
        result.append(current)
 
    return result
 
def chunk_text_with_images(
    text: str,
    images: list,
    max_chars: int = 1200,
    overlap: int = 150
):
    """
    Split text into overlapping chunks.
    Attach images only to the first chunk.
    """
    chunks = []
 
    if not text:
        return [{"text": "", "image": images}]
 
    start = 0
    first = True
 
    while start < len(text):
        end = start + max_chars
        chunk_text = text[start:end]
 
        chunks.append({
            "chunk_id" : f"CHUNK#{str(uuid.uuid4())}",
            "text": chunk_text.strip(),
            "image": images if first else [],
        })
 
        first = False
        start = end - overlap if overlap else end
 
    return chunks
 