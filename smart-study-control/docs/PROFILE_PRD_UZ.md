# Smart Study Control: profil va yangi mobil interfeys

2026-11-09. Ushbu aniqlashtirish avvalgi arxitektura va maxfiylik talablarini saqlaydi.

## Dizayn va navigatsiya

Telefon uchun besh asosiy yo‘nalish: Asosiy, Kitoblar, Fokus, AI ustoz, Profil. Ota-ona va xodimlarda vakolatga mos menyu. Yorug‘ fonda olovrang brend aksenti, o‘qilishi oson to‘q matn, yashil muvaffaqiyat kartalari. Kamida 48dp bosish maydoni. Kontent kichik ekranda aylantiriladi. Profil ichidagi har bir yo‘nalish mustaqil marshrut, ortga qaytish va xato/bo‘sh/yuklanish holatiga ega.

Profilning besh sahifasi: Mavzu va status, Mutolaa tarixi, Test natijalari va bonuslar, Qurilma va seanslar, Oila va qurilma himoyasi. Mavzu tanlovi DataStore’da foydalanuvchi identifikatori bilan ajratib saqlanadi; ism yonidagi belgi profil va bosh sarlavhada ishlaydi. Sakkiz mavzu va sakkiz emoji mavjud. Apple emoji fayllari tarqatilmaydi: Android tizim emoji shriftidan foydalaniladi. Shu sababli aynan iPhone ko‘rinishi va’da qilinmaydi.

## Ruxsatlarni to‘g‘ri tushuntirish

“Hammasini bir bosishda yoqish” o‘rniga bosqichma-bosqich ruxsat yordamchisi kerak. Android runtime, maxsus ruxsat va manifest huquqlarini turlicha boshqaradi. Har bir holat tizimdan qayta o‘qiladi; oddiy tugma bosilishi “Faol” deb hisoblanmaydi. Joylashuv o‘qish uchun shart emas, alohida rozilik bilan yoqiladi. Maxsus imkoniyatlar xizmati, overlay yoki root orqali Device Owner vakolatini taqlid qilish yo‘q.

Rasmiy enrollment qilingan Device Owner qurilmada ruxsat etilgan paketlarni to‘xtatish va o‘chirishni bloklash mumkin. Oddiy o‘rnatilgan APK o‘zini o‘chirishni to‘xtata olmaydi. PIN ilovaning o‘zidagi ota-ona amallarini qayta tasdiqlashi mumkin; u Android tizim huquqi hisoblanmaydi. Ota-ona tasdig‘i serverda bog‘lanish va vakolat orqali tekshiriladi, urinishlar cheklanadi. PIN ekranini haqiqiy server tekshiruvisiz ishlaydigan deb ko‘rsatish mumkin emas.

Manbalar: https://developer.android.com/guide/topics/permissions/overview va https://developer.android.com/reference/android/app/admin/DevicePolicyManager . Package suspension API 24+, uninstall blocking API 21+; qurilma/profil egasi yoki tegishli delegatsiya zarur. Loyiha minSdk 26.

## O‘qish va test

Kitobning aniq sahifa oralig‘i, nashri va manba matni savollarga bog‘lanadi. O‘quvchi belgilagan sahifa o‘qiganlikning isboti hisoblanmaydi; u self-reported progress. Natijalar alohida qayd qilinadi. AI savol loyihasi kattalar tasdig‘idan so‘ng baholash uchun ishlatiladi. Test faol bo‘lganda AI tutor endpointi 409 qaytaradi; native reader matn va tushuntirishlarni yashiradi. Boshqa qurilmadagi shu hisobga ham server cheklovi amal qiladi. Tashqi xizmatlardan foydalanishni mutlaq to‘sish va’da qilinmaydi.

4 savol uchun 80% chegarasi 4/4 javobni talab qiladi (3/4=75%). Aynan 80% natijani olish uchun 5 savol va 4 ta to‘g‘ri javob variantini tavsiya qilamiz. Savollar soni va bonus ota-ona/maktab siyosatida sozlanadi. Bonus faqat server ledgerida bir marta yoziladi.

## Seanslar

Refresh token oilasi alohida kirish seansi. Access token sid claim orqali shu oilaga bog‘lanadi. Seans uzilganda access va refresh so‘rovlari rad etiladi; boshqa hisob seansiga kirish 404. Joriy seansni tasodifan uzish o‘rniga alohida chiqish amali qo‘llanadi. Eski sid yo‘q access tokenlar 15 daqiqagacha yashashi mumkin; yangi kirish/refresh sid beradi. IP va joylashuv taxmin qilinmaydi yoki avtomatik oshkor qilinmaydi. Joriy qurilma modeli Android’dan olinadi, masofadagi noma’lum model soxtalashtirilmaydi.

## Budilnik, fokus, chat

Budilnikdagi matematika yoki surat mashqi ixtiyoriy; foydalanuvchi doim signalni to‘xtata oladi. Exact alarm ruxsati rad etilsa, kafolatning pasayishi ko‘rsatiladi. Fokus vaqtni monotonic soat bilan hisoblaydi. Barcha bildirishnomalarni o‘chirish faqat DND uchun alohida berilgan tizim ruxsati bilan mumkin, hozir bunday umumiy va’da berilmaydi.

Bolalar chati kelgusida sinf/ota-ona tasdig‘i bilan yopiq doirada, bloklash, shikoyat, fayl tekshirish, saqlash muddati va moderatsiya bilan qo‘shiladi. Hozirgi “AI ustoz” yo‘nalishi mavjud tutor xizmatini ochadi; soxta sinfdoshlar yoki xabarlar ko‘rsatilmaydi.

## 0.5.0 bajarilgan doira va ochiq ishlar

Bajarilgan: yangi light theme, bottom navigation, kompakt real-data dashboard, besh profil yo‘nalishi, lokal mavzu/status, serverdagi mutolaa va test tarixi, seanslarni uzish API’si, test vaqtida server AI blokirovkasi. Yangi DB jadvali talab qilinmaydi; seanslar mavjud refresh_tokens jadvalidan olinadi.

Ochiq ishlar: xodimlar mobil PDF mualliflik oqimi, native PDFning grafik sahifa renderer’i, tanlangan matn uchun kontekstual AI, ijtimoiy chat/media, serverda umumiy profil/stiker sinxronlashuvi, yutuqlar konstruktor va ledger integratsiyasi, PIN/OTP qayta tasdiqlash oqimi, haftalik profil grafigi, lokalizatsiyaning yangi matnlari, planshetning ikki ustunli maxsus joylashuvi, real qurilma accessibility va Device Owner sinovlari. AI/Telegram ishlashi serverdagi haqiqiy provider sozlamalariga bog‘liq. Ushbu ro‘yxat tugallanmaguncha “barcha funksiyalar tayyor” deb e’lon qilinmaydi.
