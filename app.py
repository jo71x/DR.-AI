import streamlit as st
import google.generativeai as genai
from PIL import Image
import datetime
from io import BytesIO
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN

# ==========================================
# 🔑 إعدادات النموذج والأمان
# ==========================================
if "GEMINI_API_KEY" not in st.secrets:
    st.error("⚠️ مفتاح API غير موجود في Secrets.")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# تعليمات النظام "الحديدية" مع أمثلة للرفض
# تعليمات النظام "الحديدية" مع أمثلة للرفض
STRICT_SYSTEM_INSTRUCTIONS = (
    "أنت نظام طبي مغلق وصارم جداً. وظيفتك الوحيدة والنهائية هي الطب والصحة."
    "\nقوانينك التي لا يمكن كسرها:"
    "\n1. إذا كان السؤال طبياً (أعراض، أدوية، تشخيص، نصائح صحية)، أجب بدقة."
    "\n2. إذا كان السؤال غير طبي (سياسة، طبخ، رياضة، برمجة، نكت، أو أي شيء آخر)، ارفض الإجابة فوراً."
    "\n3. لا تقم بالدردشة العامة أو التحية المطولة خارج السياق الطبي."
    
    "\n\nأمثلة لكيفية التصرف:"
    "\n- المستخدم: 'كيف أطبخ المندي؟' -> ردك: 'عذراً، أنا مبرمج للطب فقط.'"
    "\n- المستخدم: 'من فاز بالدوري؟' -> ردك: 'عذراً، تخصصي هو الاستشارات الطبية فقط.'"
    "\n- المستخدم: 'اكتب لي كود برمجي' -> ردك: 'لا يمكنني مساعدتك، أنا مساعد طبي فقط.'"
)

# تعريف النموذج
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=STRICT_SYSTEM_INSTRUCTIONS
)

# عند طلب الإجابة (تعديل دالة التوليد)
# ابحث عن السطر الذي يحتوي على model.generate_content وحدثه هكذا:
response = model.generate_content(
    input_data, 
    generation_config=genai.types.GenerationConfig(
        temperature=0.0,  # تصفير الحرارة يمنع الهلوسة والخروج عن النص
        top_p=0.1,
        max_output_tokens=1000,
    )
)
# ==========================================
# 🎨 إعداد الصفحة والتنسيق
# ==========================================
st.set_page_config(
    page_title="العيادة الذكية (Dr. AI)",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp {direction: rtl; text-align: right;}
    .user-bubble {background-color: #2E86C1; color: white !important; padding: 15px; border-radius: 15px 15px 0 15px; margin: 10px 0; font-size: 18px;}
    .bot-bubble {background-color: #ffffff; color: black !important; padding: 15px; border-radius: 15px 15px 15px 0; margin: 10px 0; border: 2px solid #e0e0e0; font-size: 18px;}
    .emergency-btn {background-color: #d32f2f; color: white !important; padding: 12px; text-align: center; border-radius: 8px; font-weight: bold; text-decoration: none; display: block; margin-top: 15px;}
</style>
""", unsafe_allow_html=True)

# --- دالة إضافة شريحة نصية ---
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

# --- دالة إنشاء ملف PPTX ---
def create_pptx_report(diagnosis_text, user_input_summary):
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "Medical Report (Dr. AI)"
    slide.placeholders[1].text = f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\nSmart Medical Systems"
    
    paragraphs = diagnosis_text.split('\n')
    current_chunk = ""
    slide_count = 1
    for para in paragraphs:
        if len(current_chunk) + len(para) > 800:
            add_text_slide(prs, f"Diagnosis Result ({slide_count})", current_chunk)
            current_chunk = para + "\n"
            slide_count += 1
        else:
            current_chunk += para + "\n"
    if current_chunk:
        add_text_slide(prs, f"Diagnosis Result ({slide_count})", current_chunk)
    
    binary_output = BytesIO()
    prs.save(binary_output)
    binary_output.seek(0)
    return binary_output

# --- القائمة الجانبية ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3774/3774299.png", width=120)
    st.title("لوحة التحكم")
    st.markdown('<a href="https://www.google.com/maps/search/hospital" target="_blank" class="emergency-btn">🚨 أقرب مستشفى</a>', unsafe_allow_html=True)
    if st.button("🗑️ مسح المحادثة"):
        st.session_state.messages = []
        st.rerun()

# --- المتن الرئيسي ---
st.title("🩺 العيادة الذكية المتكاملة")
st.markdown("---")

if "messages" not in st.session_state:
    st.session_state.messages = []

# عرض المحادثة
for msg in st.session_state.messages:
    role_class = "user-bubble" if msg["role"] == "user" else "bot-bubble"
    sender = "👤 أنت" if msg["role"] == "user" else "🩺 Dr. AI"
    st.markdown(f'<div class="{role_class}"><b>{sender}:</b><br>{msg["content"]}</div>', unsafe_allow_html=True)

st.markdown("### 📝 أدخل تفاصيل الحالة:")
col1, col2 = st.columns(2)
with col1:
    audio_val = st.audio_input("🎤 سجل وصف الحالة صوتياً")
with col2:
    uploaded_file = st.file_uploader("📸 ارفع صورة (أشعة/تحليل)", type=["jpg", "png", "jpeg"])

user_text = st.chat_input("اكتب أعراضك هنا...")

# معالجة المدخلات
if user_text or audio_val or uploaded_file:
    input_data = []
    user_display = ""

    if audio_val:
        audio_blob = {"mime_type": audio_val.type, "data": audio_val.getvalue()}
        input_data.append(audio_blob)
        user_display += "🎤 [رسالة صوتية] "
    
    if uploaded_file:
        img = Image.open(uploaded_file)
        input_data.append(img)
        user_display += "📸 [صورة مرفقة] "
    
    if user_text:
        input_data.append(user_text)
        user_display += user_text

    # عرض رسالة المستخدم
    st.session_state.messages.append({"role": "user", "content": user_display})
    st.markdown(f'<div class="user-bubble">👤 <b>أنت:</b><br>{user_display}</div>', unsafe_allow_html=True)

    # طلب الرد من الذكاء الاصطناعي
    with st.spinner('جاري التحليل الطبي...'):
        try:
            # نرسل البيانات مباشرة، تعليمات النظام (System Instruction) ستقوم بالفلترة
            response = model.generate_content(input_data)
            bot_reply = response.text

            st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            st.markdown(f'<div class="bot-bubble">🩺 <b>Dr. AI:</b><br>{bot_reply}</div>', unsafe_allow_html=True)

            # زر تحميل التقرير
            pptx_file = create_pptx_report(bot_reply, user_display)
            st.download_button("📊 تحميل التقرير الطبي (PPTX)", pptx_file, "Medical_Report.pptx")

        except Exception as e:
            st.error(f"حدث خطأ أثناء الاتصال بالخادم: {e}")



