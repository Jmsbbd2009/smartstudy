import type { Row } from "../../services/api";

/** Teacher-reviewed starter assessment grounded only in PDF pages 1–5. */
export const YOZ_YOMGIRI_PAGES_1_5: Row = {
  title: "Yoz yomg‘iri — 1–5-sahifalar",
  summary:
    "Kirish sahifalarida Muniraning tonggi voqeani ko‘rishi, Rahimning oilaviy hayot haqidagi qarashlari va uning Munisxon bilan ilk tanishuvi tasvirlanadi. Savollar faqat 1–5-sahifalardagi ma’lumotni tekshiradi.",
  concepts: [
    {
      id: "munosabatlar",
      title: "Oiladagi kelishmovchilik",
      explanation:
        "Rahim takrorlanadigan janjallar munosabatlarni ichidan asta yemirishi mumkin deb hisoblaydi. Bu uning oilaviy hayotga xavotir bilan qarashini ko‘rsatadi.",
      source_page: 2,
      source_quote: "ичидаги қурт",
    },
    {
      id: "matndan_dalil",
      title: "Matndan dalil top",
      explanation:
        "O‘zingdan so‘ra: Munira noma’lum hodisani qanday belgi orqali payqadi? Javobingni 1-sahifadagi tafsilot bilan asosla. Bu mashq ballga ta’sir qilmaydi.",
      source_page: 1,
      source_quote: "наъматак буталари",
    },
  ],
  connections: [],
  questions: [
    {
      prompt: "Qissa boshida voqea qaysi sana bilan boshlanadi?",
      options: [
        "197... yil 22-avgust",
        "197... yil 22-sentabr",
        "197... yil 1-iyun",
        "197... yil 5-iyul",
      ],
      correct_index: 0,
      explanation:
        "Birinchi sahifada sana 197... yil 22-avgust deb berilgan; yilning qolgan raqamlari matnda ochiqlanmagan.",
      source_page: 1,
      source_quote: "22 августи",
    },
    {
      prompt: "Munira qaysi transport vositasini boshqaradi?",
      options: ["Trolleybus", "Tramvay", "Poyezd", "Avtobus"],
      correct_index: 1,
      explanation:
        "Hikoya Munirani tramvay haydovchisi sifatida tanishtiradi.",
      source_page: 1,
      source_quote: "трамвай ҳайдовчи",
    },
    {
      prompt: "Bekat yonida Muniraning e’tiborini avval nima tortadi?",
      options: [
        "Butalar orasidan ko‘rinib turgan ayol tuflisi",
        "Yo‘l chetidagi singan chiroq",
        "Bekatda qolib ketgan chamadon",
        "Tashlab ketilgan velosiped",
      ],
      correct_index: 0,
      explanation:
        "Na’matak butalari orasidan ayolning oq, baland poshnali tuflisi ko‘rinib turgan edi.",
      source_page: 1,
      source_quote: "наъматак буталари",
    },
    {
      prompt: "Muniraning tramvayiga birinchi bekatda kim chiqadi?",
      options: [
        "Temiryo‘lchi, o‘rta yoshli erkak",
        "Institut direktori",
        "Munisxonning jiyani",
        "Yosh militsiya xodimi",
      ],
      correct_index: 0,
      explanation:
        "U temiryo‘lchilar kiyimidagi, Munira har smenada ko‘radigan yo‘lovchi edi.",
      source_page: 1,
      source_quote: "темирйўлчилар кийимидаги",
    },
    {
      prompt: "Rahim Saidov Munisxon bilan turmush qurganiga qancha bo‘lgan edi?",
      options: [
        "To‘rt yildan sal ko‘proq",
        "Bir yildan kam",
        "Yetti yil",
        "O‘n yildan ko‘p",
      ],
      correct_index: 0,
      explanation:
        "Ikkinchi sahifada ularning turmush qurganiga to‘rt yildan ozgina oshgani aytiladi.",
      source_page: 2,
      source_quote: "тўрт йилдан",
    },
    {
      prompt: "Rahim oiladagi janjallarni nimaga qiyoslaydi?",
      options: [
        "Daraxt ichidagi qurtga",
        "Qishda yog‘adigan qorga",
        "Uzilgan arqonga",
        "So‘nayotgan chiroqqa",
      ],
      correct_index: 0,
      explanation:
        "Rahim nazarida janjal daraxtni ichidan yemiradigan qurt kabi muhabbatga zarar yetkazadi.",
      source_page: 2,
      source_quote: "ичидаги қурт",
    },
    {
      prompt: "Matnga ko‘ra, Munisxon farzand masalasida qanday fikrda edi?",
      options: [
        "U ataylab farzand istamas edi",
        "U darhol farzand ko‘rishni rejalagan edi",
        "Bu haqda Rahim bilan kelishib olgan edi",
        "U farzand masalasini qo‘shnilarga topshirgan edi",
      ],
      correct_index: 0,
      explanation:
        "Ikkinchi sahifa uning ataylab farzand istamasligini bildiradi.",
      source_page: 2,
      source_quote: "бола истамаслигидан",
    },
    {
      prompt: "Rahim Munisxonni ilk bor qayerda ko‘rgan edi?",
      options: [
        "Qo‘qon–Ohangaron yo‘lidagi dovonda",
        "Chorsu bekatida",
        "Institut kutubxonasida",
        "Toshkentdagi restoranda",
      ],
      correct_index: 0,
      explanation:
        "Ular ilk bor Qo‘qon–Ohangaron yo‘lidagi dovonda, tajriba uchastkasidan qaytayotgan paytda uchrashadi.",
      source_page: 3,
      source_quote: "ганч шернинг",
    },
    {
      prompt: "Munisxon aslida qaysi yo‘nalishda o‘qishni orzu qilgan?",
      options: ["Tarix", "Kimyo", "Biokimyo", "Qishloq xo‘jaligi"],
      correct_index: 0,
      explanation:
        "Suhbatda Munisxon tarixni yaxshi ko‘rishini va tarixchi bo‘lishni istaganini aytadi.",
      source_page: 5,
      source_quote: "Тарихни жуда",
    },
    {
      prompt: "Munisxon Rahimning yelkasida uxlab qolganda, Rahim nima qiladi?",
      options: [
        "Uni uyg‘otmaslik uchun qimirlamay o‘tiradi",
        "Darhol mashinani to‘xtatishni so‘raydi",
        "Uni boshqa o‘rindiqqa o‘tkazadi",
        "Shofyorni chaqirib, uni uyg‘otadi",
      ],
      correct_index: 0,
      explanation:
        "Rahim qiz uyg‘onib ketmasligi uchun qimirlamaslikka qaror qiladi.",
      source_page: 5,
      source_quote: "қимир этмасликка қарор",
    },
  ],
};
