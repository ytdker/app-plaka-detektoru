import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
from PIL import Image
import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
import random
import re
import base64
from io import BytesIO

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# .env yükle
load_dotenv()

# Ayarlar
API_KEYS_STRING = os.getenv("GEMINI_API_KEY", "")
API_KEYS_LIST = [key.strip() for key in API_KEYS_STRING.split(",")] if API_KEYS_STRING else []
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")

st.set_page_config(page_title="🛡️ APP Plaka Dedektörü", page_icon="🚗", layout="centered")

# --- GOOGLE ADSENSE ONAY KODU (BURAYA PUB- KEY YAPIŞTIRILACAK) ---
# Lütfen ca-pub-XXXXXXXXXXXX kısmını kendi AdSense ID'nizle değiştirin.
adsense_verification = """
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3526282702329383"
     crossorigin="anonymous"></script>
"""
components.html(adsense_verification, height=0)

# --- SESSION STATE BAŞLATMA ---
if "init" not in st.session_state:
    st.session_state.init = True
    st.session_state.user_email = ""
    st.session_state.otp_sent = False
    st.session_state.otp_code = ""
    st.session_state.otp_email = ""
    st.session_state.current_key_index = 0
    st.session_state.quota_exceeded_for_all = False
    st.session_state.user_provided_key = ""
    st.session_state.user_api_provider = "Gemini"
    st.session_state.ai_model_selection = "gemini-2.0-flash"
    st.session_state.analysis_result = None
    st.session_state.analysis_error = None

# Sidebar Navigasyon
page = st.sidebar.radio("📚 Menü", ["🚗 Plaka Analizi", "📖 Hakkımızda", "⚖️ Gizlilik Politikası"])

if st.session_state.user_email:
    st.sidebar.markdown(f"👤 Aktif Kullanıcı:\n**{st.session_state.user_email}**")
    if st.sidebar.button("🚪 Çıkış Yap"):
        st.session_state.user_email = ""
        st.session_state.otp_sent = False
        st.session_state.analysis_result = None
        st.rerun()

# --- SIDEBAR GERÇEK REKLAM ALANI ---
# data-ad-slot kısmını AdSense panelinden aldığınız numara ile değiştirin.
adsense_sidebar = """
<div style="text-align:center;">
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3526282702329383"
     crossorigin="anonymous"></script>
    <ins class="adsbygoogle"
         style="display:inline-block;width:300px;height:250px"
         data-ad-client="ca-pub-3526282702329383"
         data-ad-slot="1111111111"></ins>
    <script>
         target_node = document.currentScript.previousElementSibling;
         (adsbygoogle = window.adsbygoogle || []).push({});
    </script>
</div>
"""
with st.sidebar:
    st.divider()
    components.html(adsense_sidebar, height=260)

# Sayfa İçerikleri
if page == "📖 Hakkımızda":
    st.title("📖 Hakkımızda")
    st.markdown("""
    **APP Plaka Dedektörü**, araç sahiplerinin ve eksperlerin plakalarının yasal standartlara uygunluğunu hızlıca test edebilmeleri için geliştirilmiş yapay zeka tabanlı bir araçtır. 
    
    Yüksek doğruluk payına sahip Gemini AI vizyon modellerini kullanarak plakalardaki font kalınlığı, çerçeve yapısı ve sac kalitesi gibi detayları analiz ederiz. 
    
    *Amacımız, trafik güvenliğine ve yasal standartlara uyuma teknolojinin gücüyle katkıda bulunmaktır.*
    """)
    if st.button("⬅️ Analize Dön"): st.rerun()
    st.stop()

elif page == "⚖️ Gizlilik Politikası":
    st.title("⚖️ Gizlilik ve KVKK")
    st.markdown("""
    **Veri İşleme İlkelerimiz:**
    1. **Fotoğraflar:** Yüklediğiniz plaka fotoğrafları sadece analiz anında kullanılır ve sunucularımızda kalıcı olarak saklanmaz.
    2. **E-postalar:** E-posta adresiniz sadece OTP doğrulama ve analiz kotanızın takibi için kullanılır. 
    3. **Üçüncü Taraflar:** Verileriniz reklam sağlayıcıları (Google AdSense) dışında hiçbir kurumla paylaşılmaz.
    
    *İletişim ve veri talepleri için: **appplakadetektoru@gmail.com***
    
    *Bu uygulama bir tahmin aracıdır. Sonuçlar resmi bağlayıcılık taşımaz.*
    """)
    if st.button("⬅️ Analize Dön"): st.rerun()
    st.stop()

elif page == "🚗 Plaka Analizi":
    # Başlıklar
    st.title("🛡️ APP Plaka Dedektörü")
    st.markdown("Plakanız yasal standartlara uygun mu? Yapay zeka ile hemen analiz edin.")
    st.error("🚨 **YASAL UYARI: BU BİR TAHMİNDİR!**\nSonuçlar resmi bağlayıcılık taşımaz. Sorumluluk kullanıcıya aittir.")

    # --- 1. FOTOĞRAF GİRİŞİ ---
    tab1, tab2 = st.tabs(["📁 Galeriden Yüklü", "📸 Kamerayla Çek"])
    with tab1:
        up_file = st.file_uploader("Fotoğraf seçin", type=["jpg", "jpeg", "png"], key="uploader")
    with tab2:
        cam_file = st.camera_input("Fotoğraf çekin", key="camera")

    image_source = up_file if up_file else cam_file

    if image_source:
        image = Image.open(image_source)
        st.image(image, caption="Analiz Edilecek Fotoğraf", use_container_width=True)

        # --- 2. DOĞRULAMA AKIŞI ---
        if not st.session_state.user_email:
            st.info("🔎 **Analize başlamak için e-posta doğrulaması gereklidir.**")
            if not st.session_state.otp_sent:
                e_input = st.text_input("E-posta Adresiniz:", key="email_field")
                if st.button("🚀 Doğrulama Kodu Gönder"):
                    if re.match(r"[^@]+@[^@]+\.[^@]+", e_input):
                        try:
                            # Çevresel değişken (Secrets) kontrolü
                            if not SENDER_EMAIL or not SENDER_PASSWORD:
                                st.error("🔑 **Sistem Hatası:** E-posta veya şifre (Secrets) tanımlanmamış!")
                                st.info("Streamlit Dashboard -> Settings -> Secrets alanından SENDER_EMAIL ve SENDER_PASSWORD bilgilerini girdiğinizden emin olun.")
                                st.stop()

                            code = str(random.randint(100000, 999999))
                            msg = MIMEText(f"APP Plaka giriş kodunuz: {code}")
                            msg['Subject'] = 'Giriş Kodu'; msg['From'] = SENDER_EMAIL; msg['To'] = e_input
                            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as srv:
                                srv.login(SENDER_EMAIL, SENDER_PASSWORD); srv.send_message(msg)
                            st.session_state.otp_code = code; st.session_state.otp_email = e_input; st.session_state.otp_sent = True; st.rerun()
                        except Exception as e: 
                            st.error(f"Mail gönderilemedi: {e}")
                            if "535" in str(e):
                                st.warning("💡 **Çözüm:** Google hesabınızdan 'Uygulama Şifresi' (App Password) oluşturmanız ve bunu Secrets'a eklemeniz gerekmektedir. Gmail normal şifrenizi güvenlik nedeniyle kabul etmiyor.")
                    else: st.error("Geçerli e-posta girin.")
            else:
                v_input = st.text_input("6 Haneli Kod:", key="otp_field")
                if st.button("✅ Doğrula ve Başla"):
                    if v_input == st.session_state.otp_code:
                        st.session_state.user_email = st.session_state.otp_email; st.session_state.otp_sent = False; st.rerun()
                    else: st.error("Hatalı kod!")
                if st.button("🔄 Geri Dön"): st.session_state.otp_sent = False; st.rerun()
            st.stop()

        # --- 3. ANALİZ SONUCU GÖSTERİMİ ---
        if st.session_state.analysis_result:
            st.divider()
            res = st.session_state.analysis_result
            if "APP Plaka Tespit Edildi" in res or "🚨" in res:
                st.error("🚨 **APP PLAKA TESPİT EDİLDİ!**")
            else:
                st.success("✅ **PLAKA STANDARTLARA UYGUN.**")
            st.info(res)
            if st.button("🗑️ Yeni Analiz Yap"):
                st.session_state.analysis_result = None
                st.rerun()
            st.stop() # Sonuç varken butonu gösterme

        if st.session_state.analysis_error:
            st.warning(f"⚠️ {st.session_state.analysis_error}")

        # --- 4. ANALİZ BUTONU VE KOTA YÖNETİMİ ---
        st.divider()
        
        # Kullanıcı kendi anahtarını vermiş mi?
        active_key = ""
        is_user_key = False
        
        if st.session_state.user_provided_key:
            active_key = st.session_state.user_provided_key
            is_user_key = True
        elif API_KEYS_LIST and not st.session_state.quota_exceeded_for_all:
            active_key = API_KEYS_LIST[st.session_state.current_key_index]
        
        # EĞER SİSTEM KOTASI DOLUYSA PANELİ GÖSTER
        if not active_key or st.session_state.quota_exceeded_for_all:
            st.error("🚨 **Sistem Kotası Şu An Yoğun.**")
            st.info("Kesintisiz ve sınırsız analiz için kendi ücretsiz API anahtarınızı tanımlayabilirsiniz.")
            
            with st.expander("🛠️ Kendi API Anahtarımı Gir (Hızlı ve Ücretsiz)", expanded=True):
                st.markdown("""
                **Ücretsiz Anahtar Almak Çok Kolay:**
                [Google AI Studio](https://aistudio.google.com/app/apikey) adresinden saniyeler içinde tamamen ücretsiz anahtar alıp buraya yapıştırabilirsiniz.
                """)
                p_col, m_col = st.columns(2)
                with p_col: pk = st.selectbox("Sağlayıcı:", ["Gemini", "OpenAI"], key="user_p")
                with m_col: mk = st.selectbox("Model:", ["gemini-2.0-flash", "gemini-1.5-pro"] if pk == "Gemini" else ["gpt-4o", "gpt-4o-mini"], key="user_m")
                k_val = st.text_input("API Key:", type="password", key="user_k")
                if st.button("🚀 Kaydet ve Analize Hazırlan"):
                    if k_val:
                        st.session_state.user_provided_key = k_val
                        st.session_state.user_api_provider = pk
                        st.session_state.ai_model_selection = mk
                        st.session_state.quota_exceeded_for_all = False
                        st.success("✅ Anahtar kaydedildi! Lütfen analiz butonuna basın.")
                        st.rerun()
        else:
            # ANA ANALİZ BUTONU (Arka planda tüm yedekleri zorlar)
            if st.button("🔍 Plakayı Analiz Et", use_container_width=True, type="primary"):
                st.session_state.analysis_result = None
                st.session_state.analysis_error = None
                with st.spinner("🧠 Yapay Zeka Uzman Trafik Polisi Analiz Ediyor..."):
                    final_text = None
                    analysis_successful = False
                    
                    # --- AKILLI SİSSTEM ROTASYONU (Döngüsel Deneme) ---
                    for attempt in range(len(API_KEYS_LIST) if not is_user_key else 1):
                        current_key = active_key if is_user_key else API_KEYS_LIST[st.session_state.current_key_index]
                        
                        try:
                            prompt = """
Sen uzman bir trafik polisisin. Fotoğraftaki plakanın yasal ve standart (ince font, 5mm çerçeve) olup olmadığını incele. Harfler çok kalınsa (APP) mutlaka belirt.

## 1. ANA SONUÇ VE KARAR
🚨 BU PLAKANIN DEĞİŞTİRİLMESİ LAZIMDI! (APP Plaka Tespit Edildi)
veyahut
✅ BU PLAKA DOĞRUDUR. (Standart Plaka)

## 2. DETAYLI ANALİZ
Gördüğün harf fontunu ve sac kalitesini açıkla.
"""
                            if (is_user_key and st.session_state.user_api_provider == "Gemini") or (not is_user_key):
                                genai.configure(api_key=current_key)
                                model = genai.GenerativeModel(st.session_state.ai_model_selection)
                                response = model.generate_content([prompt, image])
                                final_text = response.text
                            else:
                                # OpenAI Fallback (Kullanıcı Key verdiyse)
                                client = OpenAI(api_key=current_key)
                                buf = BytesIO(); image.save(buf, format="JPEG"); img_b64 = base64.b64encode(buf.getvalue()).decode()
                                response = client.chat.completions.create(
                                    model=st.session_state.ai_model_selection,
                                    messages=[{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}]}],
                                    max_tokens=1000
                                )
                                final_text = response.choices[0].message.content
                            
                            analysis_successful = True
                            break # Başarı durumunda döngüden çık
                            
                        except Exception as e:
                            err = str(e).lower()
                            if "429" in err or "quota" in err or "limit" in err:
                                if not is_user_key:
                                    # Sistem anahtarı patladı, sessizce sıradakine geç
                                    if st.session_state.current_key_index < len(API_KEYS_LIST) - 1:
                                        st.session_state.current_key_index += 1
                                        continue
                                    else:
                                        st.session_state.quota_exceeded_for_all = True
                                        st.session_state.analysis_error = "⚠️ Sistem kapasitesi şu an dolu. Lütfen kendi anahtarınızla devam edin."
                                        break
                                else:
                                    st.session_state.analysis_error = "⚠️ Kendi API anahtarınızın kotası dolmuş. Lütfen bir süre bekleyin veya yeni bir anahtar tanımlayın."
                                    break
                            elif "api_key" in err or "invalid" in err or "key not found" in err:
                                st.session_state.analysis_error = "🔑 Girdiğiniz API anahtarı geçersiz veya hatalı. Lütfen kontrol edip tekrar deneyin."
                                break
                            else:
                                st.session_state.analysis_error = f"❌ Analiz sırasında teknik bir sorun oluştu. Lütfen fotoğrafı veya bağlantınızı kontrol edip tekrar deneyin."
                                break

                    if analysis_successful:
                        st.session_state.analysis_result = final_text
                        st.session_state.analysis_error = None
                    
                    # Her durumda sayfayı yenile ki state değişiklikleri (sonuç veya hata) görünsün
                    st.rerun()

    # --- ALT GERÇEK REKLAM ALANI (Yatay/Responsive) ---
    st.divider()
    adsense_footer = """
    <div style="text-align:center;">
        <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-3526282702329383"
         crossorigin="anonymous"></script>
        <ins class="adsbygoogle"
             style="display:block"
             data-ad-client="ca-pub-3526282702329383"
             data-ad-slot="2222222222"
             data-ad-format="auto"
             data-full-width-responsive="true"></ins>
        <script>
             (adsbygoogle = window.adsbygoogle || []).push({});
        </script>
        <div style="margin-top:20px; font-size: 0.8em; color:#aaa; font-family: sans-serif;">
            © 2026 APP Plaka Dedektörü | <a href="#" style="color:#aaa; text-decoration:none;">Gizlilik</a> | <a href="#" style="color:#aaa; text-decoration:none;">KVKK</a> 
            <br>💎 İletişim: <b>appplakadetektoru@gmail.com</b>
        </div>
    </div>
    """
    components.html(adsense_footer, height=220)
