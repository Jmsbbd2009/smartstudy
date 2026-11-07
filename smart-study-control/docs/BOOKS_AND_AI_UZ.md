# PDF kitob → vizual dars → tushunish testi

## “Yoz yomg‘iri” uchun tayyor test — 1–5-sahifalar

Kitob panelida o‘qituvchi yoki super admin PDFni yuklagach, sahifa oralig‘ini **1 dan 5 gacha** qo‘ying. **1–5-sahifalar uchun tayyor test** tugmasi manbaga bog‘langan dars qoralamasini ochadi: 10 ta aralashtiriladigan test savoli, to‘g‘ri javoblar izohi, tushuncha kartalari va ballga kirmaydigan “matndan dalil top” savoli. Qoralamani saqlang, sahifa iqtiboslari va javob kalitini tekshiring, so‘ng o‘qish topshirig‘iga biriktiring. Noto‘g‘ri javob mukofotni avtomatik bermaydi; vakolatli kattalar tekshiruvni tanlashi mumkin.

O‘quvchi testni boshlashdan oldin dars oralig‘idagi har bir sahifani **Sahifani belgilash** tugmasi bilan qayd etadi. Bu o‘quvchining o‘z hisoboti, sahifani to‘liq o‘qiganini isbotlamaydi. Test savollari faqat belgilangan 1–5-sahifalarga tayanadi, savol va javob variantlari har urinishda aralashtiriladi, natijada qaysi sahifa javob bilan tekshirilgani ko‘rsatiladi. Server iqtiboslar yuklangan PDFning aynan shu sahifalarida borligini tekshiradi. PDFning boshqa nashri yoki noto‘g‘ri OCR matni bo‘lsa, server darsni rad etadi; iqtibosni asliga qarab tuzating. Ushbu test butun asarni o‘qiganlikni tasdiqlamaydi.

Qo‘shimcha o‘rganish g‘oyalari: voqealar tartibini tiklash, qahramon qarorini matndan dalil bilan izohlash, noto‘g‘ri javobdan so‘ng sahifaga qaytib qisqa tushuntirish olish, keyingi testda qiynalgan sahifaga mos savollarni ko‘paytirish. Bular o‘quvchiga yordam beradi; qiyinchilikni jazo yoki zarur aloqa vaqtini cheklash uchun ishlatmaslik kerak.

v0.2.0 uchun amaliy qo‘llanma. Bu oqim haqiqiy fayl, baza va mukofot ledgeri bilan ishlaydi. AI provayderi ulanmagan bo‘lsa dars yaratish tugmasi aniq xato ko‘rsatadi; o‘qituvchi yoki ota-ona darsni qo‘lda ham tuzishi mumkin.

## Panelda ishlatish

1. Ota-ona yoki o‘qituvchi sifatida kiring → **Kitoblar va AI test**.
2. PDFni yuklang: 10 MiB, 300 sahifagacha, shifrlanmagan. Sahifa matni serverda ajratiladi. Asl PDF faqat yuklagan egasiga yuklab olish uchun beriladi; o‘quvchi faqat biriktirilgan sahifa matnini ko‘radi.
3. 1–5 sahifalik bo‘lim tanlang → **AI dars va test yaratish**. Provayder, model va moderatsiya serverda sozlangan bo‘lishi kerak. Har bir tushuncha/savol kitobdagi sahifa va aniq iqtibosga bog‘lanadi. Mos kelmagan iqtibos serverda rad qilinadi.
4. Natija: SVG tushunchalar xaritasi, ochiladigan kartochkalar, manba iqtiboslari va test qoralamasi. Tahrirlash ishlaydi. AI javobining iqtibosi mavjudligi uning mazmunan to‘g‘riligini kafolatlamaydi.
5. Katta kishi barcha javob kalitlari va manbani tekshiradi, tasdiq belgisini qo‘yadi va darsni e’lon qiladi. Tasdiqlanmagan dars o‘quvchiga test sifatida berilmaydi. Tahrir versiyani oshiradi va qayta tasdiqlash talab etadi.
6. Sahifalarni farzandga/sinf o‘quvchisiga biriktiring. O‘qituvchi faqat o‘z sinfidagi o‘quvchini tanlaydi va ekran vaqti mukofotini o‘zi belgilay olmaydi.
7. O‘quvchi panel yoki Androiddagi **Kitoblar va AI test** orqali o‘qiydi va test yechadi. Savol va variantlar serverda aralashtiriladi; javob kaliti test tugashidan oldin berilmaydi. Har urinish 30 daqiqa. Natija, tushuntirish va manba sahifasi ko‘rsatiladi.
8. Ota-ona **O‘qish topshiriqlari**dagi farzand kartasini ochib natija tarixini ko‘radi. **Kitoblar kutubxonasi** kartasi esa kitobni tahrirlash uchun ochadi.

## O‘qilganini qanday o‘lchaydi

Ikki alohida ko‘rsatkich bor: o‘quvchi o‘zi belgilagan sahifalar va to‘g‘ri test javoblari bilan tekshirilgan sahifalar. Sahifani ochish yoki uzoq turish o‘qiganlik isboti emas va mukofot bermaydi. To‘g‘ri javoblar tanlangan savollar bo‘yicha tushunish dalili; butun kitobni o‘qib chiqqanini isbotlamaydi. Kameradan yashirin kuzatuv yo‘q.

## Mukofot va avtomatika

Ota-ona **AI boshqaruv**da farzand uchun avtopilotni yoqadi, kunlik o‘qish mukofoti limitini belgilaydi. O‘qish topshirig‘ida ham avtomatik mukofot yoqilgan bo‘lishi kerak. Bo‘limga 0–30 daqiqa, testdan o‘tish chegarasi 50–100% (standart 80%) API orqali sozlanadi. Kunlik limit 0–120 daqiqa; standart 60. Ledger kun chegarasi UTC; keyinchalik oilaning vaqt zonasini sozlash qo‘shilishi kerak.

Tasdiqlangan testdan o‘tilganda server bitta tranzaksiyada kredit beradi. Har bir **o‘quvchi + dars** uchun faqat bir marta: takroriy finish, qayta yechish yoki shu darsni yana biriktirish qo‘shimcha daqiqa bermaydi. Avtomatika o‘chiq bo‘lsa ota-ona natijani qo‘lda tasdiqlaydi; kunlik limit bunda ham saqlanadi. O‘qituvchi biriktirgan topshiriq uchun ota-ona mukofotni API `reward-policy` orqali belgilashi mumkin; paneldagi shu alohida sozlash hali qo‘shilmagan.

Kredit berilishi ilovani darhol ochmaydi. Mavjud mukofot sahifasida o‘quvchi vaqtni band qiladi; qoida, uyqu va qurilma imkoniyati yana tekshiriladi. Favqulodda aloqa mukofotga bog‘liq emas.

## AI avtopiloti nimalar qiladi

Ota-onaning aniq ruxsati bilan bugungi akademik topshiriqlar bo‘yicha qisqa mashq rejasini yaratadi va o‘quvchiga yuboradi. Kuniga 0–3 vazifa, standart 2; har birida 0 mukofot. Bir kunlik muvaffaqiyatli reja qayta yuborilmaydi. Xato bo‘lsa kuniga ko‘pi bilan 3 AI urinishi. Kun Asia/Tashkent bo‘yicha aniqlanadi. Compose `autopilot` workeri har 300 soniyada ruxsat berilgan bolalarni tekshiradi; mahalliy ishga tushirish: `python -m app.workers.autopilot --once` yoki doimiy rejim uchun flagsiz.

AI ixtiyoriy kod/komanda bajarmaydi, o‘ziga rol bermaydi, qurilmaga administrator huquqini yoqmaydi, ilova cheklovlarini o‘zgartirmaydi va o‘zi mukofot yaratmaydi. Darsni avtomatik nashr qilish, subyektiv ishni yakuniy baholash va qurilmani cheksiz boshqarish yoqilmagan. Bu chegaralar backend ruxsatlari bilan tekshiriladi.

## Skanerlangan PDF va OCR

Linux serverda Poppler (`pdftoppm`) va Tesseract kerak. Dockerfile ularni o‘rnatadi. `.env`: `OCR_ENABLED=true`, `OCR_LANG=eng`. O‘zbek/rus matni uchun mos Tesseract til paketlarini o‘rnating va `uzb+rus+eng` kabi mavjud tillarni tanlang; hozirgi image faqat ingliz paketini o‘rnatadi. Har so‘rov 1–3 sahifa. OCR xato qilishi mumkin, natija `OCR_UNVERIFIED`; javob kaliti baribir katta kishi tomonidan tekshiriladi. Nashr qilingan dars manbasini OCR orqali o‘zgartirish taqiqlangan.

PDF protsessi 768 MiB virtual xotira, 18 CPU soniya va devor soati bo‘yicha timeout bilan alohida ishga tushadi. Muhitdan AI kalitlari berilmaydi. Bu to‘liq xavfsizlik sandboxi emas: ommaviy production uchun alohida izolyatsiyalangan worker, antivirus/quarantine va yangilanadigan parser/OS paketlari kerak.

## Android va o‘chirish himoyasi

Androidda biriktirilgan matn/kartochkalarni ochish, sahifa belgilash, test va natijalar mavjud. Oldin ochilgan o‘qish ma’lumotlari foydalanuvchi bo‘yicha Roomda saqlanadi; offline ko‘rish mumkin. Testni boshlash/yakunlash, progress yuborish va daqiqa berish hozir internet talab qiladi. PDF yuklash va dars muallifligi native Androidda hali yo‘q; React manba kodi saqlangan, ammo website sifatida deploy qilinmaydi. Room 1→2 migratsiyasi oldingi navbat va vazifalarni saqlaydi; migratsiya instrument testi yozilgan va kompilyatsiya qilingan, qurilmada bajarilmagan.

Ilovani tizim darajasida o‘chirishdan himoyalash faqat vakolatli **Device Owner** rejimida. Oddiy APK bunday huquqqa ega emas. Qurilma ekranida va ota-ona panelida haqiqiy `isUninstallBlocked` o‘qilishi asosidagi holat ko‘rsatiladi; server bu qurilmaning o‘z hisoboti ekanini saqlaydi. Bu hardware attestatsiyasi yoki factory-resetdan himoya emas. Sozlash/tiklash: `DEVICE_OWNER_SETUP.md`.

## Bu versiyada tekshirilgan

Haqiqiy PDF matn ajratish va raster sahifada haqiqiy Tesseract OCR, manbasiz iqtibosni rad etish, maxfiy javob kalitlari, ikki parallel finish, qayta biriktirish, bekor qilingan oila/sinf ruxsatlari, eskirgan dars/test, limit va AI yo‘qligi holatlari avtomatlashtirilgan. Admin/student/teacher interfeysi haqiqiy HTTP orqali vaqtinchalik backend bilan sinaldi. Brauzerning o‘zi bu muhitda ishga tusha olmadi; jsdom testi ekran maketi va brauzer API mosligini to‘liq tekshirmaydi. Qurilma va jonli AI integratsiyasi hali alohida sinov talab qiladi.
