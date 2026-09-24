from fastapi import FastAPI, UploadFile, File, Form
from common import process_image, gemini_with_file_search, clean_answer, GEMINI_MODEL, GEMINI_FILE_SEARCH_STORE
import json

app = FastAPI(title='THỦY LỢI AI - Báo cáo hiện trường')

REPORT_TYPES = {
    'incident': 'SỰ CỐ CÔNG TRÌNH',
    'corridor': 'KIỂM TRA HÀNH LANG BẢO VỆ CÔNG TRÌNH THỦY LỢI',
    'dry_area': 'KHU VỰC KHÔ / THIẾU NƯỚC',
    'water_level': 'MỰC NƯỚC HỒ / KÊNH',
}

@app.get('/')
def health():
    return {'success': True, 'service': 'field-report', 'file_search_configured': bool(GEMINI_FILE_SEARCH_STORE)}

@app.post('/')
async def field_report(
    file: UploadFile = File(...),
    report_type: str = Form('incident'),
    question: str = Form(''),
    kml_context: str = Form(''),
    capture_time: str = Form(''),
    latitude: str = Form(''),
    longitude: str = Form(''),
):
    try:
        if report_type not in REPORT_TYPES:
            report_type='incident'
        content=await file.read()
        image=process_image(content)
        title=REPORT_TYPES[report_type]
        kml_context=(kml_context or '').strip()
        try:
            kml_text=json.dumps(json.loads(kml_context),ensure_ascii=False,indent=2) if kml_context else 'Chưa có dữ liệu đối chiếu GIS/KML.'
        except Exception:
            kml_text=kml_context or 'Chưa có dữ liệu đối chiếu GIS/KML.'
        location_lines=[]
        if latitude and longitude:
            location_lines.append(f'Tọa độ GPS hiện trường: {latitude}, {longitude}')
        if capture_time:
            location_lines.append(f'Thời gian ghi nhận: {capture_time}')
        location_text='\n'.join(location_lines) if location_lines else 'Chưa có thông tin GPS/thời gian từ thiết bị.'
        prompt=f'''Bạn là THỦY LỢI AI, trợ lý chuyên ngành thủy lợi của Chi nhánh Thủy lợi Vu Gia - Thu Bồn.

Lập DỰ THẢO BÁO CÁO HIỆN TRƯỜNG dựa trên ảnh, thông tin GPS/thời gian và dữ liệu GIS/KML được cung cấp.

LOẠI BÁO CÁO: {title}

THÔNG TIN THIẾT BỊ:
{location_text}

DỮ LIỆU GIS/KML:
{kml_text}

NGUYÊN TẮC BẮT BUỘC:
1. Chỉ mô tả điều có thể quan sát hoặc có căn cứ.
2. Không tự bịa địa điểm, thời gian, diện tích, mực nước, lưu lượng, khoảng cách hay thông số kỹ thuật.
3. Ưu tiên xác định công trình/tuyến từ GPS/GIS/KML nếu dữ liệu đủ căn cứ; không tự suy đoán tên công trình.
4. Phải sử dụng File Search để đối chiếu hồ sơ THỦY LỢI AI khi có liên quan.
5. Phân biệt rõ thông tin quan sát từ ảnh, thông tin từ GIS/GPS, thông tin từ hồ sơ File Search và nhận định/kiến nghị.
6. Nếu không tìm thấy căn cứ trong File Search, ghi rõ: "Chưa tìm thấy căn cứ phù hợp trong hồ sơ."
7. Nếu ảnh không đủ rõ, ghi rõ: "Chưa xác định được từ hình ảnh."
8. Với vi phạm hành lang, không kết luận vi phạm chỉ từ ảnh; chỉ nêu dấu hiệu và căn cứ cần kiểm tra.
9. Với diện tích khô, không tự ước lượng ha nếu không có dữ liệu đo đạc.
10. Với mực nước, chỉ đọc giá trị khi thước/vạch đủ rõ.
11. Đây là DỰ THẢO, không phải kết luận pháp lý hay kết luận kỹ thuật cuối cùng.

CẤU TRÚC BẮT BUỘC:
# BÁO CÁO NHANH HIỆN TRƯỜNG
## 1. Thông tin chung
- Loại báo cáo
- Thời gian
- Địa điểm
- Công trình/tuyến
- Tọa độ GPS (nếu có)
## 2. Hiện trạng quan sát từ hình ảnh
## 3. Đánh giá sơ bộ
## 4. Đối chiếu hồ sơ
## 5. Kiến nghị
## 6. Thông tin cần bổ sung

GHI CHÚ CỦA CÁN BỘ:
{question.strip() or 'Không có.'}
'''
        answer,sources=gemini_with_file_search(prompt,image)
        answer=clean_answer(answer)
        return {'success':True,'status':'draft','report_type':report_type,'report_title':title,'filename':file.filename,'answer':answer,'sources':sources,'engine':'Gemini Vision + File Search','model':GEMINI_MODEL,'file_search':bool(GEMINI_FILE_SEARCH_STORE),'next_step':'review'}
    except Exception as e:
        return {'success':False,'status':'error','error':str(e)}
