import streamlit as st
import pandas as pd
from database import init_db, get_stock_valuation, save_report, get_stock_pillars, delete_reports_by_ids
from ai_processor import extract_text_from_pdf, analyze_with_gemini

st.set_page_config(page_title="Project II", layout="wide")
init_db()

st.title("TỔNG HỢP BÁO CÁO CỔ PHIẾU")

# Xử lý báo cáo
with st.sidebar:
    st.markdown("<h3 style='text-align: center;'>Xử Lý Báo Cáo</h3>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader("Tải lên file PDF:", type=["pdf"], accept_multiple_files=True)
    
    if st.button("Lưu trữ"):
        if uploaded_files:
            for file in uploaded_files:
                with st.spinner(f"Đang xử lý: {file.name}..."):
                    try:
                        text = extract_text_from_pdf(file)
                        data = analyze_with_gemini(text)
                        
                        if not data.get("current_price_at_report"):
                            data["current_price_at_report"] = 1.0
                            
                        status = save_report(data)
                        if status == "success":
                            st.success(f"Nạp thành công mã: {data.get('ticker')}")
                    except Exception as e:
                        st.error(f"Lỗi file {file.name}: {str(e)}")
        else:
            st.warning("Tải file báo cáo!")

# Xóa báo cáo
    st.markdown("---")
    st.markdown("<h3 style='text-align: center;'>Xóa Báo Cáo</h3>", unsafe_allow_html=True)

    id_input = st.text_input(
        "Nhập ID các báo cáo muốn xóa:", 
        placeholder="Ví dụ: 1, 2, 3", 
        key="delete_id_input"
    )
    delete_clicked = st.button("Xóa báo cáo")

    if delete_clicked:
        if id_input.strip():
            try:
                list_ids = [int(i.strip()) for i in id_input.split(",") if i.strip().isdigit()]
                
                if list_ids:
                    if delete_reports_by_ids(list_ids):
                        st.success(f"Đã xóa thành công: {list_ids}")
                        st.rerun()
            except Exception as e:
                st.error(f"Có lỗi xảy ra: {str(e)}")

# Tra cứu
st.markdown("---")
user_query = st.text_input("Nhập mã cổ phiếu:", placeholder="Gõ mã cổ phiếu và nhấn Enter")

if user_query:
    ticker = user_query.upper().strip()
    valuation_data = get_stock_valuation(ticker)
    pillars_data = get_stock_pillars(ticker)
    if valuation_data:
        st.subheader(f"Dữ liệu Định giá & Khuyến nghị: {ticker}")
        
        df = pd.DataFrame(valuation_data, columns=[
            "ID","CTCK phát hành", "Ngày phát hành", "Khuyến nghị", 
            "Mức giá trong báo cáo", "Mức giá kỳ vọng", "Upside (%)"
        ])
        
        display_df = df[["ID","CTCK phát hành", "Ngày phát hành", "Khuyến nghị", "Mức giá trong báo cáo", "Mức giá kỳ vọng", "Upside (%)"]]
        
        def color_upside(val):
            color = 'green' if val > 0 else 'red' if val < 0 else 'gray'
            return f'color: {color}; font-weight: bold'
            
        styled_df = (display_df.style
             .map(color_upside, subset=['Upside (%)'])
             .format({
                 "Mức giá trong báo cáo": "{:.0f}",
                 "Mức giá kỳ vọng": "{:.0f}",
                 "Upside (%)": "{:.2f}"
             }))
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Nhận Định Chuyên Sâu")
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Kết quả kinh doanh", 
            "Triển vọng kinh doanh", 
            "Dự báo kết quả kinh doanh", 
            "Rủi ro", 
            "Luận điểm đầu tư"
        ])
        
        pillars_mapping = [
            (tab1, 1, "Không có dữ liệu."),
            (tab2, 2, "Không có dữ liệu."),
            (tab3, 3, "Không có dữ liệu."),
            (tab4, 4, "Không có dữ liệu."),
            (tab5, 5, "Không có dữ liệu.")
        ]
        
        for tab, idx, empty_msg in pillars_mapping:
            with tab:
                combined_text = ""
                for row in pillars_data:
                    ctck_name = row[0]
                    content = row[idx]
                    if content and str(content).strip() and str(content).strip() != "None":
                        combined_text += f"**{ctck_name}:**\n\n{content}\n\n"
                
                if combined_text:
                    st.markdown(combined_text)
                else:
                    st.info(empty_msg)
    else:
        st.info(f"Chưa có dữ liệu")