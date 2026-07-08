import os
import json
import time
from pypdf import PdfReader
from google import genai
from google.genai import types
from google.genai.errors import APIError
from dotenv import load_dotenv

load_dotenv()

def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        try:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        except Exception:
            continue
    return text

def analyze_with_gemini(text):
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key= api_key)
    
    final_prompt = f"""
    Bạn là một chuyên gia phân tích tài chính cao cấp. Hãy đọc toàn bộ văn bản báo cáo chứng khoán dưới đây.
    Thực hiện trích xuất thông tin định giá và viết phân tích chuyên sâu cho 5 thông tin quan trọng.
    
    YÊU CẦU ĐẶC BIỆT VỀ ĐỘ DÀI VÀ ĐỘ CHI TIẾT:
    - Đối với mỗi thông tin, viết thành một bài phân tích dài, chi tiết, đầy đủ luận điểm và số liệu dẫn chứng từ báo cáo.
    - TUYỆT ĐỐI KHÔNG viết chung chung, KHÔNG tóm tắt sơ sài chỉ 1-2 câu, KHÔNG viết kiểu gạch đầu dòng ngắn. 
    - Hãy phân tích rõ nguyên nhân, hệ quả, các động lực thúc đẩy kinh doanh hoặc các yếu tố rủi ro cốt lõi một cách mạch lạc.
    - Đảm bảo 'target_price' và 'current_price_at_report' bắt buộc phải là kiểu số (float).
    - Trích dẫn đúng thông tin từ báo cáo, không suy đoán ngoài nội dung đã cho. Nếu thông tin nào không có trong báo cáo, hãy để trống hoặc ghi rõ "Không có dữ liệu".

    Toàn bộ văn bản báo cáo cần xử lý:
    ---------------------------------
    {text}
    ---------------------------------
    """

    json_schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "ticker": types.Schema(type=types.Type.STRING, description="Mã cổ phiếu viết hoa (Ví dụ: HPG)"),
            "source": types.Schema(type=types.Type.STRING, description="Tên công ty chứng khoán phát hành báo cáo (Ví dụ: SSI, VNDIRECT)"),
            "date": types.Schema(type=types.Type.STRING, description="Ngày phát hành báo cáo định dạng DD/MM/YYYY"),
            "recommendation": types.Schema(type=types.Type.STRING, description="Khuyến nghị ngắn gọn, chỉ trả về kết quả Mua/Bán/Theo dõi"),
            "current_price_at_report": types.Schema(type=types.Type.NUMBER, description="Mức giá cổ phiếu tại thời điểm ra báo cáo"),
            "target_price": types.Schema(type=types.Type.NUMBER, description="Mức giá kỳ vọng / Giá mục tiêu trong báo cáo"),
            "business_status": types.Schema(type=types.Type.STRING, description="Bài phân tích dài, cực kỳ chi tiết về Tình hình hiện tại của doanh nghiệp"),
            "business_outlook": types.Schema(type=types.Type.STRING, description="Bài phân tích dài, cực kỳ chi tiết về Triển vọng tương lai và động lực tăng trưởng"),
            "financial_forecast": types.Schema(type=types.Type.STRING, description="Chi tiết các Số liệu dự báo tài chính, doanh thu, lợi nhuận, kế hoạch kinh doanh"),
            "risks": types.Schema(type=types.Type.STRING, description="Bài phân tích chi tiết toàn bộ các rủi ro đi kèm hệ lụy"),
            "investment_thesis": types.Schema(type=types.Type.STRING, description="Luận điểm đầu tư cốt lõi và kết luận chi tiết")
        },
        required=[
            "ticker", "source", "date", "recommendation", 
            "current_price_at_report", "target_price", 
            "business_status", "business_outlook", "financial_forecast", "risks", "investment_thesis"
        ]
    )

    models_to_try = ['gemini-2.5-flash', 'gemini-2.5-pro','gemini-3.5-flash']
    max_retries = 3
    
    for model_name in models_to_try:
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=final_prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        response_mime_type="application/json",
                        response_schema=json_schema,
                    ),
                )
                return json.loads(response.text)
            except APIError as e:
                if e.code in [503, 429]:
                    wait_time = (attempt + 1) * 3
                    time.sleep(wait_time)
                    continue
                raise e
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                raise e
                
    raise Exception("Tất cả các máy chủ của Gemini hiện tại đều đang quá tải. Vui lòng thử lại sau ít phút!")