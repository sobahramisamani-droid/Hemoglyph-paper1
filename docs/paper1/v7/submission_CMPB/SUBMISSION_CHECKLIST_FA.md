<div dir="rtl" align="right">

# چک‌لیست ارسال به CMPB — نسخهٔ R6 (۱۴۰۵/۰۸/۰۵ – 2026-10-27)

## الف) آنچه آماده است (کار من — تمام)

| # | مورد | فایل | وضعیت |
|---|---|---|---|
| 1 | مقاله (docx، دو خط فاصله، ≈۴٬۹۰۰ کلمهٔ متن اصلی، چکیدهٔ ساختاریافته ۳۴۵ کلمه، ۳۴ مرجع) | `docs/paper1/v7/ارسال پیپر ۱/Manuscript_Paper1_Hemoglyph_CMPB_R9.docx` | ✅ |
| 2 | هایلایت‌ها (۵ مورد، همه ≤ ۸۵ کاراکتر) | `submission_CMPB/highlights.txt` | ✅ |
| 3 | شکل‌های ۱ تا ۷ (فایل‌های جدا، ۳۰۰ dpi) | `submission_CMPB/Figure_1.png … Figure_7.png` | ✅ |
| 4 | مکمل واحد (Notes 1–12، Tables S1–S16، Figs S1–S7، TRIPOD+AI، Reproducibility map) | `submission_CMPB/ارسال پیپر ۱/Supplementary_Information.docx` | ✅ |
| 5 | Supplementary Data 1 (منابع رجیستری) | `docs/paper1/supplement/Supplementary_Data_1_sources_13.4.1.xlsx` | ✅ |
| 6 | کاور لتر | `docs/paper1/v7/COVER_LETTER_CMPB.md` | ✅ (بلوک نویسندهٔ مسئول خالی) |
| 7 | صفحهٔ عنوان | `submission_CMPB/TITLE_PAGE.md` | ⚠️ نیاز به تکمیل تو |
| 8 | README پژوهشی مخزن + مثال اجرایی | `README_PAPER.md`, `examples_quickstart.py` | ✅ (اجرا تست شد) |
| 9 | پاسخ‌های از پیش‌آمادهٔ داوری (داخلی) | `submission_CMPB/REVIEWER_RESPONSES_PREPARED.md` | ✅ |
| 10 | نمونه‌های سبک CMPB (داخلی) | `submission_CMPB/EXEMPLARS_CMPB.md` | ✅ |

## ب) آنچه فقط تو می‌توانی انجام دهی — قبل از ارسال

| # | کار | چرا مهم است | چطور |
|---|---|---|---|
| 1 | **تأیید کتبی دو هم‌نویسنده** (ایمیل کافی است): نویسندگی، سهم CRediT، متن دقیق وابستگی، ORCID | بدون آن ارسال اخلاقاً مجاز نیست؛ EM از هر نویسنده تأیید می‌گیرد | متن پیشنهادی ایمیل را می‌توانم بنویسم |
| 2 | **اطلاعات نویسندهٔ مسئول**: تلفن، نشانی پستی، ایمیل پایدار | الزام CMPB در صفحهٔ عنوان | در `TITLE_PAGE.md` و `COVER_LETTER_CMPB.md` جایگزین کن (یا به من بده) |
| 3 | **مخزن GitHub را عمومی کن** و `README_PAPER.md` را در بالای README اصلی لینک بده | داور کد را باز می‌کند؛ README فعلی تبلیغاتی است | پیشنهاد: README محصول را به `README_PRODUCT.md` تغییر نام بده و `README_PAPER.md` را `README.md` کن — فقط با تأیید تو این کار را می‌کنم |
| 4 | **DOI زنودو** برای اسنپ‌شات فریزشده | در مقاله نوشته‌ایم «قبل از انتشار»؛ بهتر است قبل از ارسال باشد | GitHub → Zenodo (رایگان، ۱۰ دقیقه)؛ DOI را به من بده تا در Data availability بگذارم |
| 5 | **ساخت حساب Editorial Manager** | `submit.elsevier.com/CMPB` | با همان ایمیل نویسندهٔ مسئول |
| 6 | **نتایج دکتر حفیظی** (اختیاری ولی مؤثرترین عامل) | +۱۰ تا ۱۵ واحد احتمال پذیرش | اگر تا ۲ هفته رسید، §3.8 اضافه می‌کنم؛ اگر نه، بدون آن ارسال کن |

## ج) هنگام ارسال در Editorial Manager (ترتیب فیلدها)

1. Article type: **Original Research Article**
2. Title / Abstract: کپی از docx (چکیدهٔ ساختاریافته با چهار سرفصل)
3. Keywords: Clinical decision support; Knowledge base; Software verification; Provenance; Laboratory medicine; Large language models
4. Authors: سه نفر، ترتیب مقاله؛ فقط یک نویسندهٔ مسئول
5. Funding: None
6. Declarations: Conflict of interest (مالکیت محصول تجاری توسط نویسندهٔ اول — **حتماً**)، Ethics (داده‌های عمومی بدون شناسه؛ بدون نیاز به تأیید کمیته؛ دلیل در مقاله)، GenAI declaration (متن موجود در Declarations مقاله)
7. Suggested reviewers: پنج نفر در کاور لتر (Wright, Sittig, Peleg, McCudden, Dhombres)
8. آپلود به ترتیب: Cover Letter → Title Page → Highlights → Manuscript → Figure 1–7 → Supplementary Material → Supplementary Data 1
9. PDF ساخته‌شدهٔ EM را **کامل** باز کن و تأیید کن (جدول‌ها و کاراکترهای ≥ ≤ κ سالم باشند)

## د) بعد از ارسال

- تصمیم اول ≈ ۳–۴ هفته. اگر desk-reject → JBI (R5 آماده؛ نیم روز هم‌ترازی با R6) → IJMI.
- در صورت revision: از `REVIEWER_RESPONSES_PREPARED.md` شروع کن؛ هر ایراد را بپذیر، عدد بده، پیشنهاد مشخص بده.
- موازی: پروتکل Paper 2 (مطالعهٔ خواننده با پزشکان) و تأیید اخلاق.

## ه) چیزهایی که نباید انجام شود

- دست زدن به موتور/رجیستری برای بالا بردن عدد روی eICU.
- افزودن نام مدل LLM از روی حدس.
- حذف جملهٔ تک‌ارزیاب بودن ممیزی (پروتکل عمومی ارزیاب دوم را ذکر کرده).
- ارسال هم‌زمان به دو مجله.

</div>
