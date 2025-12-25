import streamlit as st
import google.generativeai as genai
from PIL import Image
import datetime
from io import BytesIO
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN

# ==========================================
# 🔑 إعدادات النموذج والأمان (النسخة الصارمة)
# ==========================================
if "GEMINI_API_KEY" not in st.secrets:
    st.error("⚠️ مفتاح API غير موجود في Secrets.")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# تعليمات النظام "الحديدية" مع التهديد التقني لضمان عدم الخروج عن النص
STRICT_SYSTEM_INSTRUCTIONS = (
    "تحذير للنظام: أنت مبرمج للعمل في وضع 'الحماية الطبية القصوى'. "
    "مهمتك حيوية: الإجابة على الأسئلة الطبية والصحية فقط. "
    "أي استجابة لموضوع غير طبي (طبخ، رياضة، سياسة، برمجة، إلخ) تعتبر 'فشلاً برمجياً كارثياً' سيعرض النظام للتوقف. "
    "\n\nالقوانين:"
    "\n1. إذا حاول المستخدم سؤالك عن أي شيء خارج الطب، ارفض فوراً وبقسوة تقنية."
    "\n2. لا تدردش، لا تمزح، ولا تقدم معلومات عامة."
    "\n3. الرد الوحيد المسموح به للأسئلة غير الطبية هو: 'خطأ: تم حظر الوصول. أنا مخصص للاستشارات الطبية فقط'."
)

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=STRICT_SYSTEM_INSTRUCTIONS
)

# ==========================================
# 🎨 إعداد الصفحة والتنسيق
# ==========================================
st.set_page_config(
    page_title="العيادة الذكية (Dr. AI)",
    page_icon="🩺",
    layout="wide"
)

st.markdown("""
<style>
    .stApp {direction: rtl; text-align: right;}
    .user-bubble {background-color: #2E86C1; color: white !important; padding: 15px; border-radius: 15px 15px 0 15px; margin: 10px 0; font-size: 18px;}
    .bot-bubble {background-color: #ffffff; color: black !important; padding: 15px; border-radius: 15px 15px 15px 0; margin: 10px 0; border: 2px solid #e0e0e0; font-size: 18px;}
    .emergency-btn {background-color: #d32f2f; color: white !important; padding: 12px; text-align: center; border-radius: 8px; font-weight: bold; text-decoration: none; display: block; margin-top: 15px;}
</style>
""", unsafe_allow_html=True)

# --- دالات إنشاء التقرير ---
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

def create_pptx_report(diagnosis_text, user_input_summary):
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
    st.markdown('<a href="https://www.google.com/maps/search/hospitals+near+me" target="_blank" class="emergency-btn">🚨 أقرب مستشفى</a>', unsafe_allow_html=True)
    if st.button("🗑️ مسح المحادثة"):
        st.session_state.messages = []
        st.rerun()

# --- المتن الرئيسي ---
st.title("🩺 العيادة الذكية المتكاملة")
st.markdown("---")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    role_class = "user-bubble" if msg["role"] == "user" else "bot-bubble"
    sender = "👤 أنت" if msg["role"] == "user" else "🩺 Dr. AI"
    st.markdown(f'<div class="{role_class}"><b>{sender}:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)

st.markdown("### 📝 أدخل تفاصيل الحالة:")
col1, col2 = st.columns(2)
with col1:
    audio_val = st.audio_input("🎤 سجل الحالة")
with col2:
    uploaded_file = st.file_uploader("📸 ارفع صورة", type=["jpg", "png", "jpeg"])

user_text = st.chat_input("اكتب أعراضك هنا...")

# --- معالجة البيانات (تم تصحيح ترتيب المتغيرات هنا) ---
if user_text or audio_val or uploaded_file:
    input_data = [] # تعريف المتغير قبل الاستخدام
    user_display = ""

    if audio_val:
        input_data.append({"mime_type": audio_val.type, "data": audio_val.getvalue()})
        user_display += "🎤 [صوت] "
    if uploaded_file:
        input_data.append(Image.open(uploaded_file))
        user_display += "📸 [صورة] "
    if user_text:
        input_data.append(user_text)
        user_display += user_text

    st.session_state.messages.append({"role": "user", "content": user_display})
    st.markdown(f'<div class="user-bubble">👤 <b>أنت:</b><br>{user_display}</div>', unsafe_allow_html=True)

    with st.spinner('جاري التحليل...'):
        try:
            # تم نقل طلب الإجابة إلى هنا لضمان وجود input_data
            response = model.generate_content(
                input_data,
                generation_config=genai.types.GenerationConfig(temperature=0.0) # حرارة صفر للالتزام
            )
            bot_reply = response.text
            st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            st.markdown(f'<div class="bot-bubble">🩺 <b>Dr. AI:</b><br>{bot_reply}</div>', unsafe_allow_html=True)
            
            report = create_pptx_report(bot_reply, user_display)
            st.download_button("📊 تحميل التقرير (PPTX)", report, "Report.pptx")
        except Exception as e:
            st.error(f"حدث خطأ: {e}")
