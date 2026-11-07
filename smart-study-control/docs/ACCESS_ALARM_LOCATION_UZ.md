# SMART STUDY CONTROL v0.3 — kirish, budilnik va joylashuv

2026-11-05. Bu qo‘llanma yangi haqiqiy funksiyalar va sozlash chegaralarini tushuntiradi. Android APK alohida ishlayotgan backendga ulanadi; arxiv hosted server o‘rnini bosmaydi. Oldingi PDF, vazifa, mukofot va Device Owner oqimlari saqlangan.

## Super admin va xodimlar

Super admin loginini serverdagi `BOOTSTRAP_SUPERADMIN_LOGIN` orqali belgilang. Dastlabki parol `BOOTSTRAP_SUPERADMIN_PASSWORD`dan olinadi. Haqiqiy parollar va API kalitlari arxiv/APK/manba kodiga qo‘shilmagan. `.env` maxfiy server fayli, uni boshqa kishiga yubormang yoki gitga qo‘shmang.

1. `python scripts/configure.py` bilan `.env` yarating. `BOOTSTRAP_SUPERADMIN_LOGIN`ga o‘zingiz tanlagan login va serverdagi `BOOTSTRAP_SUPERADMIN_PASSWORD`ga maxfiy vaqtinchalik parol kiriting; kamida 12 belgi tavsiya qilinadi. Kirishdan keyin parolni almashtirish majburiy.
2. Migratsiya: `alembic upgrade head`; keyin `python -m app.bootstrap`. Takror ishga tushirish mavjud parolni almashtirmaydi. Boshqa super admin allaqachon bo‘lsa, yangi nusxa ochmaydi.
3. Kirish uchun Android ilovasidan login va vaqtinchalik paroldan foydalaning; keyin kamida 12 belgili yangi parol o‘rnating. Eski JWT va refresh tokenlari bekor bo‘ladi. Vaqtinchalik parol bilan xodimlar yoki qurilma boshqaruvi APIlari yopiq.
4. Xodim hisoblarini hozircha server CLI orqali vakolatli super admin yaratadi: `python -m app.cli create-user --help`. Yangi xodim ham parolini birinchi kirishda yangilaydi.
5. Hisob yaratish va xodimni to‘xtatish/yoqish faqat super admin vakolatida. Native Android boshqaruv ekranlari to‘liq tugamaguncha bu amallar CLI orqali bajariladi.

Docker entrypoint `.env`da bootstrap login/parol bo‘lsa migratsiyadan keyin bir marta yaratadi. Console uchun `python scripts/run_local.py app.bootstrap` maxfiy `.env`ni jarayon argumentlariga chiqarmay yuklaydi. Lokal helper SQLite uchun `.env` DATABASE_URLni mahalliy yo‘lga, UPLOAD_DIRni mahalliy katalogga o‘zgartiring; production uchun PostgreSQL/Redis/HTTPS kerak.

## Telegramga to‘g‘ridan-to‘g‘ri o‘tish va OTP

Server sozlamalari: `TELEGRAM_BOT_USERNAME`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`. Token bot nomi bilan tekshirildi. Bot xabar yuborishi uchun foydalanuvchi o‘zi botda **Start** bosishi kerak; Telegram username’ni bilish hisobga kirish huquqini bermaydi.

Hisobingizga odatiy kirgach: **Sozlamalar → Telegram va yuz / qurilma kaliti**. Parolni kiriting, **Telegramni bog‘lash**ni bosing. Web yangi oynada, Android esa Telegram ilovasi yoki brauzerda botni ochadi. Start bosgach panelga qaytib bog‘lashni tasdiqlang. Popup bloklansa, shu oynadagi bot havolasi ishlaydi. Bog‘lashni tugatish uchun hisobga kirilgan bo‘lishi va parol qayta tasdiqlanishi kerak.

Keyingi kirish: login → **Telegram orqali kirish** → bot avtomatik ochiladi → Start → 6 xonali kodni ilovaga kiriting. Kod 5 daqiqa, ko‘pi bilan 5 xato urinish va bir martalik. Kodlar bazada faqat server kaliti bilan HMAC ko‘rinishida. Bot havolasi boshqa odamga yuborilsa, boshqa Telegram akkaunti login kodini ololmaydi. Guruh xabarlari OTP uchun qabul qilinmaydi. Kod/kalit loglarga yozilmaydi.

Botning ishlash rejimlaridan bittasini tanlang:

- Mahalliy yoki oddiy server: `docker compose --profile telegram up --build -d`. Yoki backend migratsiyasidan so‘ng `python -m app.workers.telegram_bot`. Bitta polling worker ishlating. U mavjud begona webhookni o‘chirmaydi; webhook bor bo‘lsa tushunarli xato bilan to‘xtaydi.
- HTTPS webhook: Telegram `setWebhook`da o‘zingizning `https://HOST/api/v1/telegram/webhook` manzilingiz, `secret_token` sifatida shu serverdagi `TELEGRAM_WEBHOOK_SECRET` va `allowed_updates=["message"]`ni sozlang. Tokenni brauzer/terminal tarixiga yozmang; serverdagi transport funksiyasidan foydalaning. Polling va webhookni bir vaqtda yoqmang.

Bu muhitda haqiqiy bot `getMe` bilan tekshirildi, real kishiga OTP yuborilmadi. Xabar yuborish va OTP iste’moli avtomatlashtirilgan testlarda transport almashtirilgan holda tekshirildi. O‘zingizning Telegram hisobingizni ishlab turgan serverga bog‘lash — jonli delivery uchun keyingi qadam.

## Yuz, barmoq yoki qurilma kaliti

Web panel **Qurilma kalitini qo‘shish** orqali haqiqiy WebAuthn/passkey ro‘yxatdan o‘tkazadi. Parol va qurilmadagi tasdiqlash talab etiladi. Keyingi login **Yuz / qurilma kaliti bilan kirish** orqali. Biometrik amalni OS bajaradi: qo‘llab-quvvatlasa yuz/barmoq, aks holda ekran kodi/PIN. Server yuz rasmi yoki biometrik shablon saqlamaydi, ochiq kalit va challenge imzosini tekshiradi. Bu kameraga surat tutib shaxsni aniqlash tizimi emas.

`PASSKEY_RP_ID` — domen, masalan `study.example.uz`; `PASSKEY_ORIGIN=https://study.example.uz`. Port bo‘lsa origin ichida bo‘lishi kerak. Lokal kompyuterda `localhost`/`http://localhost:5173` qo‘llanadi. `10.0.2.2` yoki LAN HTTP manzilida passkey brauzer tomonidan bloklanishi mumkin. HTTPS kerak. Har safar server UV (user verification), origin, RP hash, challenge, credential egasi, imzo va counter/replayni tekshiradi. Platform autentifikatori qanday modality ishlatganini server “yuz” deb taxmin qilmaydi.

Androidda xodimlar uchun Telegram OTP kirishi native. Bu relizda alohida web sahifa yoki passkey sozlash ekrani chiqarilmaydi; Android biometric login va native staff management keyingi release vazifalari.

## Foto budilnik

Android → **Budilnik**. Yangi budilnikda **Foto budilnik**ni yoqing va uyingizda mavjud buyumlarni belgilang: kitob, butilka, xona o‘simligi. Ular orasidan har jiringlashda bittasi tasodifiy tanlanadi. Xavfsiz va yaqinda turgan buyumni tanlang; uyda borligi majburan taxmin qilinmaydi.

Bildirishnomani bosib topshiriqni oching → **Hozir rasmga olish**. Kamera orqali olingan rasm telefondagi bundled ML Kit modelida tekshiriladi. 0.80 dan yuqori mos label topilsa budilnik to‘xtaydi va mahalliy tarixga qayd tushadi. Rasm serverga yuborilmaydi yoki saqlanmaydi. Bu tasvirni tanish, uyg‘onganlik yoki rasm yangiligini mutlaq isbotlash emas. Xira yorug‘lik/model xatosi bo‘lsa qayta olish yoki **Yordam / ovozni to‘xtatish** mumkin. Ovoz 5 daqiqada ham cheklanadi; yengib bo‘lmaydigan budilnik yo‘q.

Snooze va oddiy ovozni to‘xtatish saqlangan. Photo match, qo‘lda to‘xtatish va snooze tarixda farqlanadi. Foto tekshiruv AI API kalitisiz va internetsiz ishlaydi. Bildirishnoma va exact-alarm ruxsati, OEM quvvat tejashi va Doze alarm yetib kelishiga ta’sir qilishi mumkin. Haqiqiy telefon kamerasi/modeli sinovi shu muhitda bajarilmagan.

## Rozilik bilan real vaqtdagi joylashuv

O‘qituvchi o‘z sinfidagi o‘quvchini paneldagi **O‘quvchi joylashuvi** bo‘limidan tanlab, sessiya ruxsatini yoqishi mumkin. Bog‘langan vasiy ham **Oilaviy joylashuv** bo‘limidan ruxsat boshqarishi mumkin. Keyin o‘quvchi Androidda **Joylashuvni ulashish**ni ochib, har bir sessiya uchun aniq rozilik beradi va ruxsatlarni beradi. Aniq yoki taxminiy joylashuv qabul qilinadi. Bildirishnoma ruxsatisiz yangi ulashish boshlanmaydi.

**Ulashishni boshlash** — taxminan 30 soniyada oxirgi koordinata serverga, ota-ona paneli esa 5 soniyada yangilanadi. Doim ko‘rinadigan foreground bildirishnomada **To‘xtatish** bor. Ilova yashirin kuzatuv, avtomatik rebootdan qayta yoqish yoki cheksiz tracking qilmaydi. Faqat oxirgi koordinata; marshrut tarixi yo‘q. 90 soniyadan eski signal eskirgan deb belgilanadi va koordinata API javobidan yashiriladi. Stop/rozilikni bekor qilish/muddat tugashi koordinatani tozalaydi. Offline Stop darhol telefon GPSini to‘xtatadi va serverga stop yozuvini WorkManagerda navbatga qo‘yadi; server ulanishsiz darhol tasdiqlay olmaydi.

Faqat o‘quvchi, bog‘langan vakolatli vasiy va aynan shu o‘quvchi ro‘yxatda bor sinf o‘qituvchisi ko‘radi. Boshqa sinf o‘qituvchisi, maktab admini va platforma super admini koordinata ololmaydi. O‘qituvchining har bir ko‘rishi auditga yoziladi. Tashqi xarita foydalanuvchi havolani bosgandagina ochiladi. GPS aniqligi/tarmoq/OEMga bog‘liq; soxta lokatsiyaga qarshi apparat attestatsiyasi va kafolat yo‘q. Tashkilot voyaga yetmaganlar uchun qonuniy vakil roziligini talab qiladigan joylarda, ushbu sessiya ruxsatidan tashqari tegishli vakil roziligini ham olishi shart.

## Ilovalarni cheklash va kitobdan keyin ochish

Ilovalarni tizim darajasida suspend qilish va o‘chirishdan himoya mavjud Device Owner oqimi orqali. Oddiy “boshqa ilovalar ustida ko‘rinish” ruxsati bunday vakolat bermaydi. Yashirin overlay/accessibility/root usullari qo‘shilmagan. Enroll va tiklash: `DEVICE_OWNER_SETUP.md`.

Ota-ona kitob sahifalarini, tekshirilgan darsni, o‘tish foizini va mukofot daqiqalarini belgilaydi. Sahifa ochib turish mukofot bermaydi; tasdiqlangan javob kalitli test natijasi hisoblanadi. Avtomatika uchun ota-ona ruxsati va limitlari kerak. Daqiqa bir marta beriladi; o‘quvchi mukofot ekranida tanlangan ilovaga vaqtli kirishni oladi. Kreditning o‘zi ilovani o‘z-o‘zidan unsuspend qilmaydi; uyqu/study/safety qoidalari hali ustun. Bu limitlarni AI chetlab o‘tmaydi.

## Bildirishnomalar

Super admin yaratgan xodimlar xabar oladi; super admin va maktab admini tanlangan o‘z vakolatidagi xodimga xabar yuborishi mumkin. Web **Bildirishnomalar** sahifasida real yozuvlar, o‘qildi holati va 15 soniyali yangilanish bor. Android SyncWorker yangi xabarlarni OS bildirishnomasiga aylantiradi (ruxsat bilan, davriy background sync odatda kamida 15 daqiqa). Bu FCM yoki millisekundli push deb ko‘rsatilmaydi.

Xodim Telegramni bog‘lab, **Bildirishnomalarni Telegramga ham yuborish**ni alohida yoqishi mumkin. Faqat faol xodimga opt-in’dan keyingi yangi xabarlar yuboriladi. Muvaffaqiyatli yuborish qayta yuborilmaydi, transport xatolari ko‘pi bilan 3 marta uriniladi. Tarmoq javobi yo‘qolsa tashqi xabar nusxalanishi ehtimoli bor. In-app kanalning o‘qildi holati serverda qoladi.

## AI provayderlarining hozirgi holati

| Provayder | Natija (2026-11-05) |
|---|---|
| Groq | Ilovaning HTTP mijozi bilan kalit va modellar ro‘yxati qabul qilindi. `openai/gpt-oss-120b` tutor JSONi, `openai/gpt-oss-safeguard-20b` kirish/chiqish moderatsiyasi, manbali 3 savol/3 tushunchali kitob darsi va 2 mashqli reja jonli sinovdan o‘tdi. Kitob darsi birinchi transient 503dan keyingi qayta urinishda o‘tdi; availability/akademik aniqlik kafolati yo‘q. |
| Hugging Face | Token qabul qilindi; inference 402 qaytardi. Kredit/billing kerak. Adapter saqlangan. |
| DeepSeek | Berilgan kalit rasmiy API tomonidan 401 bilan rad etildi. `deepseek-flash` adapteri mavjud; yangi haqiqiy kalit kerak. |
| Telegram | Bot autentifikatsiyasi `getMe` bilan o‘tdi; foydalanuvchiga jonli OTP delivery hali bajarilmagan. |

`AI_PROVIDER=groq|deepseek|huggingface|compatible`. Har kalit faqat tegishli provayder endpointiga yuboriladi. DeepSeek tanlansa ham kirish/chiqish safety tekshiruvi Groqda bajariladi; buni rozilik/ma’lumot siyosatida hisobga oling. Providerlar orasida yashirin avtomatik fallback yo‘q. Groq strict JSON schema ishlatadi; DeepSeek JSON mode + server Pydantic tekshiruvi. Noto‘g‘ri, xavfli, kvota tugagan yoki tekshirilmagan natija kredit/nashr bermaydi. AI huquq yaratmaydi va ixtiyoriy kod bajarmaydi.

Ochiq chatga yuborilgan barcha parol/tokenlarni tegishli xizmatda almashtiring. Yangi qiymatlarni faqat server `.env`/secret manageriga kiriting. Ishlaydigan real server/HTTPS, qonuniy rozilik va saqlash siyosati, jismoniy telefonlar, real Telegram delivery va to‘liq accessibility tekshiruvi production oldi talablaridir.
