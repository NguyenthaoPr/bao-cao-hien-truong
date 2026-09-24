import os, re, base64, time, random
from io import BytesIO
from pathlib import Path
from google import genai
from PIL import Image, ImageOps

BASE_DIR = Path(__file__).resolve().parent.parent
SYSTEM_PROMPT = (Path(__file__).resolve().parent / 'system_prompt.txt').read_text(encoding='utf-8')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY','').strip()
GEMINI_FILE_SEARCH_STORE = os.getenv('GEMINI_FILE_SEARCH_STORE','').strip()
GEMINI_MODEL = os.getenv('GEMINI_MODEL','gemini-3.6-flash').strip()
MAX_IMAGE_BYTES = int(os.getenv('MAX_IMAGE_BYTES', str(10*1024*1024)))


def get_client():
    if not GEMINI_API_KEY:
        raise RuntimeError('Chưa cấu hình GEMINI_API_KEY trên Vercel.')
    return genai.Client(api_key=GEMINI_API_KEY)


def store_name():
    if not GEMINI_FILE_SEARCH_STORE:
        raise RuntimeError('Chưa cấu hình GEMINI_FILE_SEARCH_STORE trên Vercel.')
    return GEMINI_FILE_SEARCH_STORE


def process_image(content: bytes):
    if not content:
        raise ValueError('Ảnh rỗng.')
    if len(content) > MAX_IMAGE_BYTES:
        raise ValueError('Ảnh vượt quá giới hạn 10 MB.')
    try:
        image = Image.open(BytesIO(content))
        image = ImageOps.exif_transpose(image)
        image.thumbnail((1600,1600), Image.Resampling.LANCZOS)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        out = BytesIO()
        image.save(out, format='JPEG', quality=75, optimize=True)
        return out.getvalue()
    except Exception as e:
        raise ValueError('Không thể xử lý ảnh.') from e


def extract_answer_and_sources(result):
    answer = (getattr(result, 'output_text', None) or '').strip()
    sources=[]; seen=set()
    try:
        for step in getattr(result,'steps',[]) or []:
            if getattr(step,'type',None) != 'model_output':
                continue
            for block in getattr(step,'content',[]) or []:
                if getattr(block,'type',None) != 'text':
                    continue
                if not answer:
                    answer += (getattr(block,'text',None) or '')
                for ann in getattr(block,'annotations',[]) or []:
                    if getattr(ann,'type',None) != 'file_citation':
                        continue
                    item={
                        'file_name': getattr(ann,'file_name',None) or 'Tài liệu THỦY LỢI AI',
                        'page_number': getattr(ann,'page_number',None),
                        'source': getattr(ann,'source',None),
                    }
                    key=tuple(str(item.get(k,'')) for k in ('file_name','page_number','source'))
                    if key not in seen:
                        seen.add(key); sources.append(item)
    except Exception:
        pass
    if not answer:
        raise RuntimeError('Gemini không trả về nội dung.')
    return answer.strip(), sources


def gemini_with_file_search(prompt: str, image_bytes: bytes | None = None):
    client=get_client()
    tools=[]
    if GEMINI_FILE_SEARCH_STORE:
        tools=[{'type':'file_search','file_search_store_names':[store_name()]}]
    inp=[{'type':'text','text':prompt}]
    if image_bytes:
        inp.append({'type':'image','data':base64.b64encode(image_bytes).decode('utf-8'),'mime_type':'image/jpeg'})
    last=None
    for attempt in range(2):
        try:
            result=client.interactions.create(
                model=GEMINI_MODEL,
                system_instruction=SYSTEM_PROMPT,
                input=inp,
                tools=tools or None,
            )
            return extract_answer_and_sources(result)
        except Exception as e:
            last=e
            text=str(e).lower()
            if attempt==0 and any(x in text for x in ('429','500','502','503','504','timeout','unavailable','resource exhausted')):
                time.sleep(1.5)
                continue
            break
    raise last


def clean_answer(answer: str):
    lines=answer.split('\n'); cleaned=[]; skip=True
    for line in lines:
        s=line.strip()
        if skip:
            if re.match(r'^(Chào|Xin chào|Kính chào|Hello|Hi)\s',s,re.I): continue
            if re.match(r'^Dựa trên hình ảnh|^Theo yêu cầu|^Tôi sẽ',s,re.I): continue
            if re.match(r'^#{1,4}\s+',s) or re.match(r'^(\d+[.)]\s+|[-*•]\s+)',s): skip=False
            if s and not re.match(r'^(Chào|Xin chào|Kính chào|Hello|Hi)\s',s,re.I): skip=False
        cleaned.append(line)
    answer='\n'.join(cleaned)
    answer=re.sub(r'(?m)^\s*#{1,6}\s*','',answer)
    answer=re.sub(r'\n{3,}','\n\n',answer)
    return answer.strip()
