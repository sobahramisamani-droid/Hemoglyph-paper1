<div dir="rtl" align="right">

# راهنمای گام‌به‌گام ارسال مقالهٔ Hemoglyph به CMPB
*Computer Methods and Programs in Biomedicine — Elsevier — سامانهٔ Editorial Manager: `https://submit.elsevier.com/CMPB`*
*نسخهٔ ارسالی: R9 (فشرده) — به‌روزرسانی ۱۴۰۵/۰۸/۰۶ (2026-10-28)*

---

## مرحلهٔ ۰ — پیش از باز کردن سامانه (۳ تا ۱۰ روز)

| # | کار | وضعیت | مسئول |
|---|---|---|---|
| ۰٫۱ | ارسال دعوت‌نامه به دو متخصص برای ممیزی انسانی (`eval/audit/human_audit/rater_package/INVITATION_FA_EN.md` + فرم xlsx + دستورالعمل). **اگر ظرف ۲ هفته نتیجه بگیرید، قبل از ارسال، نتیجه را به یادداشت ۱۹ اضافه کنید؛ بزرگ‌ترین اهرم شانس.** اگر نه، ارسال کنید و در بازنگری اضافه می‌شود. | ☐ | شما |
| ۰٫۲ | تأیید نهایی دو همکار (خانم دکتر طهماسبی‌نژاد، دکتر بهرامی‌سامانی): خواندن نسخهٔ نهایی، تأیید سطرهای CRediT، ORCID، نگارش دقیق وابستگی سازمانی (به‌ویژه وابستگی دوم Z.T.). **بدون تأیید کتبی (ایمیل) ارسال نکنید.** | ☐ | شما + همکاران |
| ۰٫۳ | تکمیل `TITLE_PAGE.md`: تلفن، نشانی پستی کامل نویسندهٔ مسئول، ORCID همکاران. | ☐ | شما |
| ۰٫۴ | push کردن HEAD (`ae63215`) به GitHub عمومی؛ روی یک کلون تازه: `bash reproduce.sh quick` → باید PASS بدهد. | ☐ | شما |
| ۰٫۵ | ساخت رکورد Zenodo از همان کامیت (GitHub → Zenodo integration یا آپلود zip؛ مجوزها: کد AGPL-3.0، رجیستری CC BY-SA 4.0). DOI را در بخش *Data and code availability* مقاله جایگزین عبارت «will be archived» کنید؛ سپس `python3 build_docx.py` را دوباره اجرا کنید. | ☐ | شما |
| ۰٫۶ | یک‌بار خواندن کامل docx نهایی (نه md) — به‌ویژه بخش Declarations و اینکه هیچ «[to be supplied]» باقی نمانده باشد. | ☐ | شما |

> **قاعدهٔ طلایی:** هیچ عددی را تغییر ندهید. اگر چیزی در خواندن نهایی مشکوک بود، به جای تغییر عدد، جمله را حذف یا به مکمل منتقل کنید.

---

## مرحلهٔ ۱ — فایل‌هایی که آپلود می‌کنید

| نوع فایل در EM (Item type) | فایل | نکته |
|---|---|---|
| **Cover Letter** | متن `COVER_LETTER_CMPB.md` (بلوک نویسندهٔ مسئول پر شود) | در کادر متنی paste کنید یا به docx تبدیل کنید |
| **Title Page (with Author Details)** | `submission_CMPB/TITLE_PAGE.md` → تبدیل به docx | جدا از متن اصلی |
| **Manuscript** | `ارسال پیپر ۱/Manuscript_Paper1_Hemoglyph_CMPB_R9.docx` | تک‌ستون، دوخط‌فاصله، بخش‌های شماره‌دار، شکل‌ها در انتها برای داوری |
| **Highlights** | `submission_CMPB/highlights.txt` | ۵ مورد، هر یک ≤۸۵ نویسه (بررسی شد: ۷۹–۸۲) |
| **Graphical Abstract** | `fig/Graphical_abstract.png` | اختیاری |
| **Figure** ×۸ | `submission_CMPB/Figure_1.png … Figure_8.png` | هر شکل یک فایل، ۳۰۰ dpi، به ترتیب ارجاع |
| **Supplementary Material** | `submission_CMPB/ارسال پیپر ۱/Supplementary_Information.docx` | یک فایل؛ نام را هنگام آپلود `Supplementary_Information.docx` بگذارید |
| **Supplementary Data** | `docs/paper1/supplement/Supplementary_Data_1_sources_13.4.1.xlsx` | Supplementary Data 1 |
| **Declaration of Interest Statement** | فرم الزویر (در سامانه تولید می‌شود) | با متن Competing interest مقاله یکسان باشد |

**آپلود نکنید:** `*_R9_long.md`، `EXEMPLARS_CMPB.md`، `REVIEWER_RESPONSES_PREPARED.md`، چک‌لیست‌ها، بستهٔ ارزیاب.

---

## مرحلهٔ ۲ — پر کردن فرم‌های سامانه (ترتیب EM)

1. **Article Type:** *Original Research Article*.
2. **Section/Category:** روش‌ها و نرم‌افزار / Clinical decision support (هرکدام که نزدیک‌تر است).
3. **Title / Abstract / Keywords:** عیناً از docx کپی کنید (چکیدهٔ ساختاریافته، ۶ کلیدواژه).
4. **Authors:** سه نویسنده به ترتیب مقاله؛ ایمیل‌های سازمانی/واقعی؛ ORCID هر سه؛ فقط **یک** نویسندهٔ مسئول (شما). نقش‌های CRediT را در سامانه هم وارد کنید (همان متن مقاله).
5. **Funding:** «None».
6. **Classifications:** چند کلیدواژهٔ موضوعی انتخاب کنید (clinical decision support, knowledge-based systems, verification/validation, laboratory medicine).
7. **Suggested reviewers (معمولاً ۳ نفر):** پژوهشگرانی با کار منتشرشده در CDSS/verification/laboratory informatics که **هیچ ارتباطی** با شما ندارند و در کشور شما نیستند. پیشنهادهای معقول: نویسندگان مراجع [13–17]، [33]، [34] مقاله (Isabel/DXplain-vs-LLM، verification of guideline knowledge، Cabitza). **Opposed reviewers:** خالی بگذارید.
8. **Questionnaire / Declarations:** مطابق متن مقاله پاسخ دهید —
   - اخلاق: داده‌های عمومیِ بی‌نام؛ بدون شرکت‌کنندهٔ انسانی؛ بدون نیاز به تأیید کمیتهٔ اخلاق (دلیل ذکر شود).
   - **Generative AI declaration: «Yes»** — سه کاربرد اعلام‌شده (پیش‌نویس قواعد، ارزیاب تطابق، کمک نگارشی) همان‌طور که در مقاله هست. پنهان نکنید؛ این بخشی از موضوع مقاله است.
   - تعارض منافع: محصول تجاری دسکتاپ نویسندهٔ اول (همان متن مقاله).
   - دسترسی داده/کد: GitHub + DOI زنودو؛ انتخاب گزینهٔ «data available in public repository».
   - Preprint: اگر ندارید، «No».
9. **Comments to editor:** خالی یا یک جمله: «The LLM comparator cannot be named or re-run for contractual reasons; this is stated in the manuscript and supplement.» (فقط اگر در cover letter نیامده).
10. **Build PDF → View Submission:** فایل PDF ساخته‌شده را **کامل باز کنید**: ترتیب شکل‌ها، خوانایی جداول، نبودن کاراکترهای شکسته (فارسی نام شما در title page باید درست دیده شود؛ اگر نه، فقط لاتین بگذارید).
11. **Approve Submission.** شمارهٔ مقاله (CMPB-D-26-xxxxx) را در `CHECKLIST.md` یادداشت کنید.

---

## مرحلهٔ ۳ — پس از ارسال

| زمان تقریبی | اتفاق | کار شما |
|---|---|---|
| ۱–۷ روز | بررسی فنی دفتر (technical check) — ممکن است فایل‌ها را برگردانند (مثلاً فرم تعارض منافع، dpi شکل) | ظرف ۴۸ ساعت اصلاح و بازارسال |
| ≈۳–۴ هفته | تصمیم اول (desk reject یا ارسال به داوری) | هیچ؛ در این مدت ممیزی انسانی را جلو ببرید |
| ≈۲–۴ ماه | نظر داوران: محتمل‌ترین نتیجه **Major revision** | پاسخ نقطه‌به‌نقطه؛ پایهٔ آماده: `REVIEWER_RESPONSES_PREPARED.md`؛ هر انتقاد درست را بپذیرید؛ عدد منجمد را تغییر ندهید؛ تغییرات را در فایل track-changes نشان دهید |
| در صورت رد | گزینهٔ بعدی: **JBI** (ارسال همان بسته با تغییر قالب) سپس **IJMI** | نظرات داوران CMPB را پیش از ارسال مجدد اعمال کنید |

---

## چک‌لیست یک‌صفحه‌ای نهایی (لحظهٔ پیش از Approve)

- ☐ هیچ «[to be supplied]» یا «XXX» در هیچ فایلی نیست (`grep -rn "to be supplied" submission_CMPB docs/paper1/v7/*.md`)
- ☐ DOI زنودو در Data availability درج شده و resolve می‌شود
- ☐ GitHub عمومی است و `reproduce.sh quick` روی کلون تازه PASS داده
- ☐ ایمیل تأیید هر دو همکار در دست است
- ☐ چکیده ≤۳۵۰ کلمه؛ highlights ≤۸۵ نویسه؛ ۳۴ مرجع؛ ۸ شکل؛ ۷ جدول — همه با PDF ساخته‌شده مطابق است
- ☐ اعلامیهٔ GenAI، اخلاق، تعارض منافع، CRediT در سامانه با متن مقاله یکسان است
- ☐ نسخهٔ ارسالی (`R9.docx`) با tag گیت ثبت شده: `git tag paper1-R9-submitted && git push --tags`

</div>
