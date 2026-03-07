# 🚗 Profesyonel APP Plaka Analizörü (AI Powered)

Bu uygulama, **Google Gemini AI** (2.0 Flash, 1.5 Pro vb.) vizyon modellerini kullanarak araç plakalarının Türkiye standartlarına uygun olup olmadığını analiz eder. Özellikle yasadışı "APP Plaka" tespitinde uzmanlaşmış bir prompt mühendisliği ile çalışır.

## ✨ Öne Çıkan Özellikler

*   🛡️ **Güvenli Giriş:** `smtplib` tabanlı gerçek e-posta doğrulama (OTP) sistemi.
*   🧠 **Gelişmiş Analiz:** Font kalınlığı, çerçeve genişliği, karakter aralığı ve mühür kontrolü yapan uzman AI komutları.
*   🔄 **Akıllı API Yönetimi:** Sistem kotaları dolduğunda otomatik yedek anahtara geçiş (Fail-over).
*   🎫 **Kullanıcı Kotası:** Her kullanıcıya 1 adet ücretsiz sorgu hakkı (Sorgu sonrası kendi API Key'i ile devam edebilir).
*   🤖 **Çoklu Model Desteği:** Gemini 2.0 Flash, 1.5 Flash ve 1.5 Pro modelleri arasında seçim yapabilme.
*   📱 **Kamera Entegrasyonu:** Mobil cihazlardan doğrudan fotoğraf çekerek analiz başlatma.

## 🚀 Hızlı Kurulum

1.  **Repo'yu Klonlayın:**
    ```bash
    git clone https://github.com/kullaniciadin/app-plaka-detektoru.git
    cd app-plaka-detektoru
    ```

2.  **Bağımlılıkları Yükleyin:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Çevresel Değişkenleri (.env) Ayarlayın:**
    `.env` dosyanızı oluşturun ve şu bilgileri girin:
    ```env
    GEMINI_API_KEY="anahtar1,anahtar2" # Virgülle birden fazla eklenebilir
    SENDER_EMAIL="gonderici@gmail.com"
    SENDER_PASSWORD="abcd efgh ijkl mnop" # Gmail Uygulama Şifresi
    ```

4.  **Çalıştırın:**
    ```bash
    streamlit run app.py
    ```

## 📄 Kullanım Notları
*   Bu uygulama bir **tahmin aracıdır** ve yasal bir hükmü yoktur.
*   Gmail üzerinden OTP gönderebilmek için Google hesabınızda `2 Adımlı Doğrulama` açık ve `Uygulama Şifresi` oluşturulmuş olmalıdır.
