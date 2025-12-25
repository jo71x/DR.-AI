import streamlit as st
import google.generativeai as genai
from PIL import Image
import datetime
from io import BytesIO
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN

# ==========================================
# 🔑 إعدادات الأمان والنموذج
# ==========================================
# ملاحظة: يُفضل استخدام st.secrets["GEMINI_API_KEY"] عند الرفع للموقع العام
api_key = "AIzaSyAYNxEEBXwfgkr99ywxVs2PheIOtmfA080" 

# تعليمات النظام "الحديدية" (مع التهديد التقني)
STRICT_SYSTEM_INSTRUCTIONS = (
    "تحذير للنظام: أنت تعمل في وضع 'الحماية الطبية الصارمة'. "
    "مهمتك هي الإجابة على الأسئلة الطبية فقط. "
    "أي إجابة خارج الطب تعتبر خرقاً أمنياً وتؤدي لفشل الجلسة. "
    "لا تدردش، لا تطبخ، لا تبرمج. "
    "إذا سُئلت عن شيء غير طبي، رد بـ: 'خطأ: تم حظر الوصول. أنا مخصص للطب فقط'."
)

if not api_key:
    st.error("⚠️ يرجى وضع مفتاح API.")
    st.stop()

genai.configure(api_key=api_key)

# تعريف النموذج (مرة واحدة فقط وبشكل صحيح)
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash", 
    system_instruction=STRICT_SYSTEM_INSTRUCTIONS
)

# ==========================================
# 🎨 إعداد الصفحة والتنسيق (CSS)
# ==========================================
st.set_page_config(page_title="العيادة الذكية (Dr. AI)", page_icon="🩺", layout="wide")

st.markdown("""
<style>
    .stApp {direction: rtl; text-align: right;}
    .user-bubble {background-color: #2E86C1; color: white !important; padding: 15px; border-radius: 15px 15px 0 15px; margin: 10px 0; font-size: 18px;}
    .bot-bubble {background-color: #ffffff; color: black !important; padding: 15px; border-radius: 15px 15px 15px 0; margin: 10px 0; border: 2px solid #e0e0e0; font-size: 18px;}
    .emergency-btn {background-color: #d32f2f; color: white !important; padding: 12px; text-align: center; border-radius: 8px; font-weight: bold; text-decoration: none; display: block; margin-top: 15px;}
</style>
""", unsafe_allow_html=True)

# --- دالات التقرير (PPTX) ---
def add_text_slide(prs, title_text, content_text):
    slide_layout = prs.slide_layouts[1]
    slide = prs.slides.add_slide(slide_layout)
    slide.shapes.title.text = title_text
    body = slide.placeholders[1]
    tf = body.text_frame
    tf.text = content_text
    for paragraph in tf.paragraphs:
        paragraph.font.size = Pt(18)
        paragraph.alignment = PP_ALIGN.RIGHT

def create_pptx_report(diagnosis_text):
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "Medical Report (Dr. AI)"
    slide.placeholders[1].text = f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    paragraphs = diagnosis_text.split('\n')
    current_chunk = ""
    slide_count = 1
    for para in paragraphs:
        if len(current_chunk) + len(para) > 800:
            add_text_slide(prs, f"Diagnosis ({slide_count})", current_chunk)
            current_chunk = para + "\n"
            slide_count += 1
        else:
            current_chunk += para + "\n"
    if current_chunk:
        add_text_slide(prs, f"Diagnosis ({slide_count})", current_chunk)
    
    output = BytesIO()
    prs.save(output)
    output.seek(0)
    return output

# --- القائمة الجانبية ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3774/3774299.png", width=120)
    st.title("لوحة التحكم")
    st.markdown('<a href="http://google.com/maps?q=hospital" target="_blank" class="emergency-btn">🚨 أقرب مستشفى</a>', unsafe_allow_html=True)
    if st.button("🗑️ مسح المحادثة"):
        st.session_state.messages = []
        st.rerun()

# --- واجهة الدردشة ---
st.title("🩺 العيادة الذكية المتكاملة")
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    role_class = "user-bubble" if msg["role"] == "user" else "bot-bubble"
    sender = "👤 أنت" if msg["role"] == "user" else "🩺 Dr. AI"
    st.markdown(f'<div class="{role_class}"><b>{sender}:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)

# المدخلات
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    audio_val = st.audio_input("🎤 تسجيل صوتي")
with col2:
    uploaded_file = st.file_uploader("📸 صورة أشعة/تحليل", type=["jpg", "png", "jpeg"])

user_text = st.chat_input("اكتب أعراضك هنا...")

# معالجة الطلب
if user_text or audio_val or uploaded_file:
    input_data = []
    display_text = ""

    if audio_val:
        input_data.append({"mime_type": audio_val.type, "data": audio_val.getvalue()})
        display_text += "🎤 [صوت] "
    if uploaded_file:
        input_data.append(Image.open(uploaded_file))
        display_text += "📸 [صورة] "
    if user_text:
        input_data.append(user_text)
        display_text += user_text

    st.session_state.messages.append({"role": "user", "content": display_text})
    st.markdown(f'<div class="user-bubble">👤 <b>أنت:</b><br>{display_text}</div>', unsafe_allow_html=True)

    with st.spinner('جاري التحليل الطبي...'):
        try:
            # استخدام حرارة صفر لضمان الالتزام بالتعليمات
            response = model.generate_content(
                input_data, 
                generation_config=genai.types.GenerationConfig(temperature=0.0)
            )
            bot_reply = response.text
            
            st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            st.markdown(f'<div class="bot-bubble">🩺 <b>Dr. AI:</b><br>{bot_reply}</div>', unsafe_allow_html=True)
            
            report = create_pptx_report(bot_reply)
            st.download_button("📊 تحميل التقرير (PPTX)", report, "Medical_Report.pptx")
        except Exception as e:
            st.error(f"خطأ: {e}")
