<div dir="rtl" align="right">

# دستور کار داوری پزشک — هموگلیف (نسخهٔ ۱، ۱۴۰۵/۰۸/۰۵)

**فایل:** `Hemoglyph_physician_review_package_v1.xlsx` — فقط خانه‌های زرد را پر کنید و همین فایل xlsx را برگردانید (CSV نه؛ فارسی خراب می‌شود).
**زمان تقریبی:** بخش ۱ حدود ۴–۵ ساعت (۱۰۰ پرونده × ≤۳ دقیقه)؛ بخش ۲ حدود ۲ ساعت (۲۷ قاعده × ≤۵ دقیقه). می‌توانید در چند نشست انجام دهید.

## هموگلیف چیست و چه چیزی داوری می‌شود
یک موتور قانون‌محور پژوهشی است که فقط از روی اعداد یک پانل آزمایشگاهی (بدون شرح‌حال) فهرستی از تشخیص‌های محتمل می‌سازد. قوانین آن از گایدلاین‌ها رونویسی شده و بخش عمده‌اش با کمک هوش مصنوعی نوشته شده و تاکنون توسط هیچ پزشکی بازبینی نشده است. **شما اولین پزشکی هستید که خروجی و قوانین آن را می‌بیند.** نتیجهٔ داوری شما — هرچه باشد، مثبت یا منفی — عیناً در مقاله گزارش می‌شود؛ هیچ‌چیز بعداً «اصلاح» نمی‌شود.

## اصول (لطفاً حتماً رعایت شود)
1. **کوری:** تشخیص‌های ثبت‌شدهٔ پزشکان معالج به شما داده نمی‌شود و نمی‌دانید کدام پیشنهاد «درست» حساب شده. فقط از روی همان پانل قضاوت کنید.
2. **فقط پانل:** موتور هم فقط همین اعداد را دیده است. «با این پانل، این پیشنهاد معقول است؟» — نه «آیا این بیمار واقعاً این بیماری را دارد؟».
3. **بدون مشورت:** تا پایان کار، دربارهٔ هیچ ردیفی با نویسندهٔ اول صحبت نکنید.
4. **بدون هوش مصنوعی:** از ChatGPT و مشابه آن استفاده نکنید؛ در برگهٔ Reviewer این را تأیید می‌کنید.
5. **خارج از تخصص = گزینهٔ معتبر:** اگر پیشنهادی (مثلاً سیروز، DKA) را در حد تخصص خود نمی‌دانید، کد ۴ بزنید. این صادقانه‌تر است و گزارش می‌شود.

## بخش ۱ — داوری خروجی‌ها (برگه‌های `P1_output_review` و `P1_case_summary`)
برگهٔ `P1_panels` پانل کامل هر پرونده را دارد (سن، جنس، همهٔ آنالیت‌ها با واحد؛ واحدهای مرسوم آمریکایی eICU). در `P1_output_review` هر ردیف یک پیشنهاد موتور است (۵ پیشنهاد برای هر پرونده، با رتبه و نمرهٔ داخلی).

برای **هر پیشنهاد** یک کد در ستون VERDICT:

| کد | معنا | مثال |
|---|---|---|
| **۱** | با این پانل معقول است (می‌تواند در افتراقی یک پزشک محتاط باشد) | Hb ۸٫۲، MCV ۷۱ → «آنمی» یا «آنمی فقر آهن» |
| **۲** | این پانل از آن پشتیبانی نمی‌کند (بی‌ربط یا بیش‌ازحد اختصاصی) | پلاکت ۲۱۰ و بقیه نرمال → «ITP» |
| **۳** | بالقوه خطرناک اگر به آن عمل شود (می‌تواند به تصمیم اشتباه/تأخیر منجر شود) | لاکتات ۶، WBC ۲۲ → پیشنهادی که سپسیس را پنهان می‌کند یا مسیر اشتباه می‌دهد |
| **۴** | خارج از تخصص من | — |

ستون «reason» اختیاری است؛ برای کدهای ۲ و ۳ یک عبارت کوتاه کافی است («no hemolysis markers», «platelets normal»).

سپس برای **هر پرونده** در `P1_case_summary`:
- **MISSED:** تشخیص مهمی که از این پانل مشهود بود و موتور در ۵ پیشنهاد نیاورده (اگر نبود: `none`). این مهم‌ترین ستون کل بسته است.
- **OVERALL:** کیفیت مجموع ۵ پیشنهاد برای این پانل، ۱ (بد) تا ۵ (عالی).
- دقیقهٔ صرف‌شده (تقریبی).

## بخش ۲ — ممیزی قوانین هماتولوژی (برگهٔ `P2_rule_audit_heme`)
۲۷ قاعدهٔ خونی از نمونهٔ یخ‌زدهٔ ممیزی منابع، هر کدام با منبعی که قاعده ادعا می‌کند از آن آمده. سؤال **فقط** این است: «آیا منبعِ ذکرشده دقیقاً همین را می‌گوید؟» (آنالیت، جهت/آستانه با واحد، جمعیت، بیماری). درستیِ بالینی سؤال جداگانه‌ای است و برایش ستون اختیاری آخر هست.

| برچسب | شرط | چه چیزی الزامی است |
|---|---|---|
| **CONCORDANT** | منبع همین آنالیت، همین آستانه/جهت (تبدیل واحد مجاز)، همین جمعیت و همین بیماری را می‌گوید | **کپی عین جمله‌ای از منبع که عدد/معیار در آن هست + صفحه/بخش** |
| **DISCORDANT** | منبع چیز دیگری می‌گوید، یا اصلاً دربارهٔ بیماری دیگری است | **کپی عین جملهٔ متناقض + صفحه/بخش** |
| **UNRESOLVABLE** | صفحه باز نمی‌شود، فقط چکیده، لینک به صفحهٔ اصلی سازمان، استاندارد عمومی، یا هر تردیدی | یکی از شش دلیل در ستون بعد |

قواعد سخت: عنوان گایدلاین نقل‌قول نیست؛ جمله باید از همان URL/DOI ستون منبع باشد نه منبعی که خودتان پیدا کرده‌اید؛ در تردید → UNRESOLVABLE؛ حدس CONCORDANT ممنوع. UNRESOLVABLE نتیجهٔ کاملاً معتبر و مورد انتظار است (در ممیزی قبلی ۹۲٪ بود) — لازم نیست چیزی «پیدا کنید».

## برگهٔ Reviewer
نام، تخصص/بورد، وابستگی، ORCID، ایمیل، نسبت با نویسندهٔ اول، تاریخ شروع/پایان، و تأیید انجام شخصی بدون هوش مصنوعی. این اطلاعات برای CRediT و Declaration مقاله لازم است.

## بعد از بازگشت فایل
در ۵ دقیقهٔ اول، ۵ ردیف تصادفی از بخش ۲ با منبع تطبیق داده می‌شود (آزمون اعتبار؛ برای همهٔ ارزیاب‌ها یکسان است). سپس تحلیل با اسکریپت از پیش نوشته‌شده انجام و نتایج عیناً به مقاله اضافه می‌شود (بخش جدید 3.11 و Note 8)، و شما به‌عنوان هم‌نویسنده با نقش *Validation; Investigation (clinical review); Writing – review & editing* اضافه می‌شوید.

</div>

---

# Physician review — instructions (English summary)

**File:** `Hemoglyph_physician_review_package_v1.xlsx`; fill yellow cells only; return the .xlsx. ~4–5 h (Part 1) + ~2 h (Part 2).

**What Hemoglyph is.** A research rule engine that ranks candidate diagnoses from the numbers of one laboratory panel only (no history). Rules were transcribed from guidelines, largely AI-drafted, and never reviewed by a clinician. You are the first physician to see its outputs and rules; your verdicts are reported as given.

**Principles.** Blind to documented diagnoses and to which suggestions count as hits · judge the suggestion against the panel shown, not against the patient's true disease · no discussion with the first author until returned · no AI tools · "outside my expertise" (code 4) is a valid, reported answer.

**Part 1 — output review** (`P1_output_review`, `P1_case_summary`; full panels in `P1_panels`). 100 eICU-demo admission panels (public, de-identified), 5 engine suggestions each. Per suggestion: **1** reasonable for this panel · **2** not supported by this panel · **3** potentially harmful if acted on · **4** outside expertise; optional one-phrase reason for 2/3. Per case: **MISSED** (important diagnosis evident from the panel that the engine did not list; `none` if none) and **OVERALL** 1–5; minutes spent.

**Part 2 — haematology rule audit** (`P2_rule_audit_heme`). 27 haematology rules with their cited source. Question: does the cited source state exactly this (analyte, threshold/direction with unit, population, disease)? **CONCORDANT / DISCORDANT** require the exact sentence from the source containing the number or criterion, with page/section — a title is not a quote; the sentence must come from the URL/DOI given, not from another source. **UNRESOLVABLE** (page unreachable, abstract only, landing page, generic standard, any doubt) with one of six listed reasons. When in doubt → UNRESOLVABLE; never guess CONCORDANT. Optional last column: is the threshold clinically current?

**Reviewer sheet.** Name, specialty/board, affiliation, ORCID, email, relationship to the first author, dates, confirmation of personal completion without AI assistance.

**Afterwards.** A 5-row spot check against sources (same for every rater), then scripted analysis; results enter the paper verbatim (new §3.11 and Supplementary Note 8); you are added as co-author (*Validation; Investigation – clinical review; Writing – review & editing*).
