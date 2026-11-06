# SMART STUDY CONTROL — ishga tushirish

Bu arxivda Kotlin/Compose Android ilovasi, FastAPI backend, React ota-ona/o‘qituvchi paneli va haqiqiy yig‘ilgan debug APK bor. Bu to‘liq production relizi emas; bajarilgan va qolgan ishlar `IMPLEMENTATION_PROGRESS.md`da yozilgan.

## Backend va panel
1. Arxivni oching, terminalda loyiha papkasiga kiring.
2. `python scripts/configure.py` — yangi `.env`, JWT va baza sirlarini yaratadi. Mavjud `.env`ni o‘zgartirmaydi. `.env`ga bot/AI kalitlarini va `BOOTSTRAP_SUPERADMIN_PASSWORD`ni faqat serverda kiriting.
3. Docker bor kompyuterda: `docker compose --profile telegram up --build -d`.
4. Panel: http://localhost:5173. API hujjati: http://localhost:8000/docs.
5. Android ilovasida PARENT va STUDENT hisoblarini yarating. Student → Oila va sinf → kod olish; ota-ona kod va rozilik bilan farzandini bog‘laydi.
6. O‘qituvchi hisobini vakolatli operator yaratadi: `docker compose exec api python -m app.cli create-user --email teacher@example.test --name O‘qituvchi --role TEACHER`. Parol terminalda yashirin so‘raladi. Namunadagi email haqiqiy foydalanuvchi emas.

Docker bo‘lmasa Python orqali ishga tushirish tartibi `README.md`da bor. Asosiy deployment bazasi PostgreSQL; SQLite lokal ishlab chiqish va shu muhitdagi testlar uchun ishlatildi.

## Android
- Android Studio, to‘liq JDK 17, Android SDK 35 va Build Tools 35.0.0 kerak.
- `android` papkasini oching. `./gradlew testDebugUnitTest :domain:test assembleDebug`.
- Tayyor `artifacts/smart-study-control-debug.apk` — emulatorda backendga `10.0.2.2:8000` orqali ulanadi. Server arxiv ichida alohida ishga tushiriladi; APK mustaqil hosted xizmat emas.
- USB orqali haqiqiy telefon uchun kompyuterda backendni ishga tushiring, `adb reverse tcp:8000 tcp:8000` bajaring va `./gradlew -PDEBUG_API_URL=http://127.0.0.1:8000/api/v1/ assembleDebug` bilan qayta yig‘ing.
- Oddiy o‘rnatishda ilovalarni tizim darajasida bloklash ishlamaydi. Device Owner rejimi uchun vakolatli sozlash va mos sinov qurilmasi kerak; `docs/DEVICE_OWNER_SETUP.md`ni o‘qing. Qurilma sozlamalari yoki ma’lumotlari yashirin o‘zgartirilmaydi.

## Asosiy oqim
Ota-ona vazifa beradi → o‘quvchi javobini topshiradi → vakolatli kattalar tasdiqlaydi → daqiqalar bir marta beriladi → qurilma siyosati ruxsat bersa vaqtli kirish band qilinadi. Internet bo‘lmaganda topshirilgan matn Room navbatida saqlanadi. Budilnik, mahalliy fokus taymeri va yuklangan siyosat offline ishlaydi. Mukofot sarflash uchun server bilan ulanish kerak.

AI kaliti APKga kiritilmagan. AI yoqilmagan bo‘lsa xizmat xatosi ochiq ko‘rsatiladi; soxta javob berilmaydi. Tasdiqlangan javob kaliti asosidagi tekshiruv AI provaydersiz ishlaydi. Subyektiv ishlar kattalar tekshiruviga yuboriladi.

## Yangi: kitoblar, AI test va avtomatika

Panel → **Kitoblar va AI test**: PDF yuklang, 1–5 sahifadan AI yoki qo‘lda dars tuzing, manba/javob kalitlarini tekshirib nashr qiling va o‘quvchiga biriktiring. Vizual tushuncha xaritasi va kartochkalar bor. O‘quvchi test yechadi; sahifa belgilash va test bilan tekshirilgan tushunish alohida ko‘rsatiladi.

Ota-ona → **AI boshqaruv**: avtomatik o‘qish mukofotiga ruxsat, kunlik limit va ixtiyoriy kunlik mashqlar. AI o‘zi qurilma siyosati yoki ruxsatlarni o‘zgartirmaydi. Batafsil sozlash, OCR tillari, cheklovlar va ishlatish: `docs/BOOKS_AND_AI_UZ.md`.

Oldingi v0.1 bazasi bo‘lsa backendni yangilashdan avval backup oling, so‘ng `alembic upgrade head`; Android v0.2 Room migratsiyasi navbatni saqlaydi. APKning debug imzosi kompyuterga bog‘liq: boshqa imzo bilan o‘rnatilgan eski APK ustiga yangisi o‘rnatilmasligi mumkin. Qurilmani tiklash/o‘chirishdan avval vakolatli ma’mur bilan boshqaruvni xavfsiz olib tashlang.

40 backend testi, 8 web testi, 8 Kotlin testi hamda haqiqiy HTTP bilan 13 bosqichli PDF→test→mukofot jarayoni tekshirildi. Debug APK va instrument test APKsi yig‘ildi. Jismoniy Device Owner, budilnik va Room instrument testlari, jonli AI, PostgreSQL/Docker sinovi va to‘liq maktab administratsiyasi hali release oldi ishlaridir. Brauzer jarayoni bu muhit cheklovi sababli ishga tushmadi; real HTTP bilan jsdom UI tekshiruvi bajarildi.


## v0.3: super admin, Telegram, yuz orqali kirish, foto budilnik va joylashuv

Yangi qo‘llanma: `docs/ACCESS_ALARM_LOCATION_UZ.md`. Super admin login `500773209` (bo‘shliqli ko‘rinishi ham ishlaydi); birinchi parol yangilanishi majburiy. Admin va o‘qituvchini **Xodimlar** bo‘limida faqat super admin yaratadi. Hisobni bog‘lagach Telegramga to‘g‘ridan-to‘g‘ri o‘tish/OTP ishlaydi; passkey uchun mos HTTPS origin kerak. Native Androidda Telegram kirishi, web panelida esa passkey yuz/barmoq/PIN tasdig‘i bor.

Android budilnikda uyda bor xavfsiz buyumlarni tanlang: tasodifiy buyumni kamera bilan rasmga olish va mahalliy model tekshiruvi qo‘shildi. Joylashuv o‘quvchi o‘zi boshlaganda, ota-ona roziligi va ko‘rinadigan Stop bildirishnomasi bilan vaqtincha yuboriladi.

Groq real tutor va manbali kitob darsi sinovidan o‘tdi va asosiy provayder sifatida tanlandi. Hugging Face uchun kredit kerak (402), DeepSeek berilgan kalitni rad etdi (401). Maxfiy kalit va parollar arxiv/APKda yo‘q; yangi xavfsiz qiymatlarni serverda kiriting. Bu arxivni yuklab olishning o‘zi bot/backendni internetda doimiy ishga tushirmaydi.
