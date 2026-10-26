# -*- coding: utf-8 -*-
"""رندر نسخهٔ فارسی مقالهٔ ۱ (v5.3): Markdown راست‌به‌چپ + DOCX با قلم وزیرمتن.

    python3 docs/paper1/v53/extract_numbers.py && python3 docs/paper1/v53/render_fa.py
خروجی: docs/paper1/Paper1_Hemoglyph_FA.md و .docx
جدول‌ها از همان توابع نسخهٔ انگلیسی تولید می‌شوند (اعداد و اصطلاحات فنی لاتین می‌مانند) و تنها عنوان آن‌ها فارسی است.
"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import tables_en as T
import text_fa as F
from md_to_docx import md_to_docx

CAPS = {
    "Table 1": "**جدول ۱ | منابع داده، استانداردهای مرجع و نقش هر مجموعه.** همهٔ داده‌ها عمومی و هویت‌زدوده‌اند؛ موتور پیش از انجماد v1 هیچ‌یک از مجموعه‌های برون‌نمونه را ندیده بود مگر آنچه زیر ستون *Role* آمده است.",
    "Table 2": "**جدول ۲ | دموی eICU-CRD: فراخوانی تشخیص‌های فهرست‌شدهٔ پزشکان بر حسب بازوی ورودی، موتور v5.3 (رجیستری 13.3.0).** فراخوانی روی تشخیص‌هایی محاسبه شده که آنالیت کلیدی‌شان اندازه‌گیری شده است؛ ستون آخر همان بازو را زیر رجیستری 13.1.0 (انجماد v5.2) برای مقایسهٔ پیش‌ثبت‌شدهٔ H2 نشان می‌دهد.",
    "Table 3": "**جدول ۳ | دموی eICU-CRD: تفکیک و فراخوانی گروهیِ موتور آموزش‌ندیده در برابر آستانهٔ خام آنالیت کلیدی (B1) و مدل گرادیان‌بوستینگ آموزش‌دیده روی همان ورودی‌ها (B2، برون‌تایی پنج‌لایه).** گروه‌های با ≥ ۹ بستری فهرست‌شده؛ ستون LLM از زیرمجموعهٔ کور ۴۰۰ بستری (جدول ۵) و تنها برای جهت‌گیری است.",
    "Table 4": "**جدول ۴ | عملکرد برون‌نمونه در NHANES، آزمایشگاه ارجاعی تیروئید Garvan، کوهورت HCV آلمان و کوهورت ILPD هند.** موتور v5.3، رجیستری 13.3.0؛ همهٔ اجراهای برون‌نمونه تکمیل شده‌اند.",
    "Table 5": "**جدول ۵ | مقایسهٔ کور با یک LLM پیشروی صفر-شات با ورودی یکسان.** بستری‌های eICU-CRD با یک نگاشت برچسب ثابت و پیش‌ثبت‌شده نمره گرفتند؛ LLM (هویت کور، بخش روش‌ها) دقیقاً همان آنالیت‌ها، واحدها، سن و جنس را دریافت و فهرستی رتبه‌بندی‌شده با ≤ ۱۰ تشخیص بازگرداند. B8 (۲۴۰ بستری) پس از انجماد v5.1 کشیده و هرگز بازبینی نشد. آزمون دقیق مک‌نمار روی برچسب‌های ناهم‌خوان.",
}

def fa_caption(md):
    for k, cap in CAPS.items():
        md = re.sub(r"^\*\*" + k + r" \|[^\n]*", cap, md, count=1, flags=re.M)
    return md

main_tables = "\n\n".join(fa_caption(f()) for f in T.ALL_MAIN)

doc = f"""# {F.TITLE}

{F.AUTHORS}

## چکیده
{F.ABSTRACT}

{F.INTRO}

{F.METHODS}

{F.results()}

{F.DISCUSSION}

{F.BACK}

## جدول‌ها

{main_tables}

## اطلاعات تکمیلی
جدول‌ها و فایل‌های تکمیلی (S1–S10 و S12، SAP با اصلاحیه‌های ۱–۱۳ (اصلاحیهٔ ۱۳ = بازتحلیل پس‌تجربی Sepsis-2019)، بیانیهٔ افشا و محدودیت‌ها، چک‌لیست TRIPOD+AI، یادداشت تکمیلی S11 (پروتکل ارزیابی کاربرد بالینی: مطالعهٔ چندخوانندهٔ متقاطع و اجرای آینده‌نگر خاموش)، دادهٔ تکمیلی ۱ (فهرست منابع دانش با وضعیت تأیید هر منبع)، طرح‌وارهٔ ورودی) در نسخهٔ انگلیسی `Paper1_Supplement_EN.docx` آمده‌اند و عیناً برای هر دو نسخه معتبرند.
"""

out_md = os.path.join(HERE, "..", "Paper1_Hemoglyph_FA.md")
open(out_md, "w", encoding="utf-8").write('<div dir="rtl" align="right">\n\n' + doc + "\n</div>\n")
figdir = os.path.join(HERE, "..", "figures")
FIGS = {"1": "fig1_architecture.png", "2": "fig2_auroc_forest.png", "3": "fig3_eicu_baselines.png", "4": "fig4_calibration_dca.png",
        "5": "fig5_llm_comparison.png", "6": "fig6_audit_nexttest.png"}
# شکل‌ها در نسخهٔ فارسی هم با شمارهٔ فارسی در عنوان می‌آیند؛ نگاشت ارقام فارسی به کلید
FIGS.update({"۱": FIGS["1"], "۲": FIGS["2"], "۳": FIGS["3"], "۴": FIGS["4"], "۵": FIGS["5"], "۶": FIGS["6"]})
md_to_docx(doc, os.path.join(HERE, "..", "Paper1_Hemoglyph_FA.docx"), figdir=figdir, fig_map=FIGS, rtl=True, font="Vazirmatn", double_space=False, line_numbers=False)
print("wrote", os.path.abspath(out_md), "and .docx; words ≈", len(re.findall(r"\w+", doc)))
