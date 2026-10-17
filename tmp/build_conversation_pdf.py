from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import (
    Image, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer,
    Table, TableStyle, HRFlowable, KeepTogether,
)

SKILL_DIR = Path(r'C:\Users\besat\.gapcode\plugins\cache\gapgpt\pdf\26.722.10000\skills\pdf')
sys.path.insert(0, str(SKILL_DIR / 'scripts'))
from fa_pdf import register_persian_fonts, rtl_line, rtl_paragraph, jalali_today_str

ROOT = Path(r'D:\ai-amirali')
OUT = ROOT / 'گفتگوی_پروژه_CrackLens.pdf'
ATTACHMENT = Path(r'C:\Users\besat\.gapcode\attachments\0d27aaba-1937-45da-8e3c-9153b9362b33\pasted-text.txt')
BEAM_IMAGE = ROOT / 'artifacts' / 'beam_test.png'
FONT_DIR = SKILL_DIR / 'assets' / 'fonts'
register_persian_fonts(fonts_dir=FONT_DIR)

TEAL = colors.HexColor('#0D6E70')
DARK = colors.HexColor('#182326')
MUTED = colors.HexColor('#637176')
PAPER = colors.HexColor('#F4F1E8')
PALE_TEAL = colors.HexColor('#EAF3F2')
PALE_BLUE = colors.HexColor('#EFF3F5')
RULE = colors.HexColor('#D8DEE4')

page_w, page_h = A4
left = right = 20 * mm
top = 24 * mm
bottom = 19 * mm

doc = SimpleDocTemplate(
    str(OUT), pagesize=A4, rightMargin=right, leftMargin=left,
    topMargin=top, bottomMargin=bottom,
    title='گفتگوی پروژه CrackLens', author='OpenAI Codex',
    subject='رونوشت گفتگو، شرح پروژه و نتایج اجرای CrackLens',
)
styles = {
    'cover': ParagraphStyle('fa_cover', fontName='Vazirmatn-Bold', fontSize=24, leading=39, alignment=TA_RIGHT, textColor=DARK, spaceAfter=8),
    'subtitle': ParagraphStyle('fa_subtitle', fontName='Vazirmatn', fontSize=13, leading=24, alignment=TA_RIGHT, textColor=TEAL, spaceAfter=8),
    'h1': ParagraphStyle('fa_h1', fontName='Vazirmatn-Bold', fontSize=16, leading=29, alignment=TA_RIGHT, textColor=TEAL, spaceBefore=8, spaceAfter=5),
    'h2': ParagraphStyle('fa_h2', fontName='Vazirmatn-Bold', fontSize=12, leading=22, alignment=TA_RIGHT, textColor=DARK, spaceBefore=5, spaceAfter=3),
    'body': ParagraphStyle('fa_body', fontName='Vazirmatn', fontSize=10.1, leading=19.2, alignment=TA_RIGHT, textColor=DARK, spaceAfter=4),
    'small': ParagraphStyle('fa_small', fontName='Vazirmatn', fontSize=8.5, leading=16, alignment=TA_RIGHT, textColor=MUTED),
    'label': ParagraphStyle('fa_label', fontName='Vazirmatn-Bold', fontSize=9.6, leading=18, alignment=TA_RIGHT, textColor=TEAL),
    'latin': ParagraphStyle('latin', fontName='Helvetica', fontSize=9.4, leading=13.8, alignment=TA_LEFT, textColor=DARK, spaceAfter=4),
    'latin_small': ParagraphStyle('latin_small', fontName='Helvetica', fontSize=8, leading=11, alignment=TA_LEFT, textColor=MUTED),
    'latin_h2': ParagraphStyle('latin_h2', fontName='Helvetica-Bold', fontSize=12, leading=16, alignment=TA_LEFT, textColor=TEAL, spaceBefore=5, spaceAfter=3),
    'code': ParagraphStyle('code', fontName='Courier', fontSize=8, leading=11, alignment=TA_LEFT, textColor=DARK, backColor=PALE_BLUE, borderColor=RULE, borderWidth=0.4, borderPadding=6, leftIndent=3, rightIndent=3, spaceBefore=3, spaceAfter=6),
}
story = []


def fa(text: str, style='body'):
    story.append(rtl_paragraph(text, styles[style], doc.width))


def en(text: str, style='latin'):
    story.append(Paragraph(escape(text), styles[style]))


def heading(text: str):
    story.append(rtl_paragraph(text, styles['h1'], doc.width))


def subheading(text: str):
    story.append(rtl_paragraph(text, styles['h2'], doc.width))


def code(text: str):
    story.append(Preformatted(text, styles['code'], maxLineLength=100))


def chat(role: str, parts: list[tuple[str, str]]):
    rows = [[rtl_paragraph(role, styles['label'], doc.width - 16 * mm)]]
    for kind, value in parts:
        if kind == 'code':
            rows.append([Preformatted(value, styles['code'], maxLineLength=100)])
        else:
            rows.append([rtl_paragraph(value, styles['body'], doc.width - 16 * mm)])
    table = Table(rows, colWidths=[doc.width], hAlign='LEFT')
    shade = PALE_BLUE if role.startswith('درخواست') else PALE_TEAL
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), shade),
        ('NOSPLIT', (0, 0), (-1, 1)),
        ('BOX', (0, 0), (-1, -1), 0.6, RULE),
        ('LINEBELOW', (0, 0), (-1, 0), 0.6, colors.HexColor('#B9D4D1')),
        ('LEFTPADDING', (0, 0), (-1, -1), 8 * mm),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8 * mm),
        ('TOPPADDING', (0, 0), (-1, -1), 3 * mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3 * mm),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(table)
    story.append(Spacer(1, 4 * mm))


def page_chrome(canvas, _doc):
    canvas.saveState()
    canvas.setFillColor(TEAL)
    canvas.rect(0, page_h - 7 * mm, page_w, 7 * mm, fill=1, stroke=0)
    canvas.setFont('Vazirmatn', 8)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(page_w - right, page_h - 15 * mm, rtl_line('گفتگوی پروژهٔ CrackLens'))
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(left, 14 * mm, page_w - right, 14 * mm)
    canvas.setFont('Vazirmatn', 8)
    canvas.drawRightString(page_w - right, 9 * mm, rtl_line('صفحه ' + str(canvas.getPageNumber())))
    canvas.drawString(left, 9 * mm, 'CrackLens | Conversation Record')
    canvas.restoreState()


# Cover
story.append(Spacer(1, 18 * mm))
story.append(rtl_paragraph('گفتگو و گزارش اجرای پروژه', styles['cover'], doc.width))
story.append(rtl_paragraph('CrackLens — سامانهٔ بازرسی تصویری ترک تیرهای بتن‌آرمه', styles['subtitle'], doc.width))
story.append(HRFlowable(width='100%', thickness=1.4, color=TEAL, spaceBefore=2 * mm, spaceAfter=5 * mm))
fa('این سند، شرح اولیهٔ پروژه، روند انجام کار، وضعیت فنی خروجی و پرسش‌وپاسخ‌های کاربر دربارهٔ استفاده، نتیجهٔ Verdict، اشتراک‌گذاری برنامه و تصویر تست را برای ارائه و اشتراک در یک فایل گردآوری می‌کند.')
fa('تاریخ تهیه: ' + jalali_today_str(), 'small')
story.append(Spacer(1, 4 * mm))
if BEAM_IMAGE.exists():
    img = Image(str(BEAM_IMAGE))
    max_w = doc.width
    max_h = 105 * mm
    factor = min(max_w / img.imageWidth, max_h / img.imageHeight)
    img.drawWidth = img.imageWidth * factor
    img.drawHeight = img.imageHeight * factor
    img.hAlign = 'CENTER'
    story.append(img)
    story.append(rtl_paragraph('تصویر نمونهٔ تیر ترک‌خوردهٔ تولیدشده برای آزمون نمایشی برنامه؛ تصویر فاقد مقیاس کالیبره است.', styles['small'], doc.width))
story.append(Spacer(1, 3 * mm))
meta_rows = [
    [Paragraph(escape('Project'), styles['latin_small']), rtl_paragraph('CrackLens', styles['body'], doc.width / 2)],
    [Paragraph(escape('Contents'), styles['latin_small']), rtl_paragraph('شرح پروژه، اجرا، نتایج و گفتگوهای اصلی', styles['body'], doc.width / 2)],
]
meta = Table(meta_rows, colWidths=[doc.width * 0.28, doc.width * 0.72])
meta.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, -1), PAPER), ('BOX', (0, 0), (-1, -1), 0.5, RULE),
    ('INNERGRID', (0, 0), (-1, -1), 0.3, RULE), ('LEFTPADDING', (0, 0), (-1, -1), 7),
    ('RIGHTPADDING', (0, 0), (-1, -1), 7), ('TOPPADDING', (0, 0), (-1, -1), 5),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 2), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
story.append(meta)
story.append(PageBreak())

# Project and execution summary
heading('۱. موضوع پروژه و درخواست اولیه')
fa('در فایل پیوست‌شده، ساخت خودکار پروژهٔ CrackLens از صفر تا تحویل درخواست شده بود: سامانه‌ای برای قطعه‌بندی ترک در تصویر تیر بتن‌آرمه، اندازه‌گیری طول و عرض با مقیاس مرجع، دسته‌بندی تقریبی ترک خمشی و برشی از روی زاویه، مقایسهٔ عرض با حدود سرویس‌پذیری ACI 224R و مبحث ۹ مقررات ملی ساختمان، ارائهٔ رابط Gradio و گزارش بازتولیدپذیر.')
fa('در پیوست پایانی، متن فایل اولیهٔ پروژه آمده است. در ادامه، نتیجهٔ اجرای واقعی در محیط موجود و حدود آن ثبت شده تا تفاوت میان اجزای پیاده‌شده و مواردی که به‌علت محدودیت محیط کامل نشدند روشن باشد.')

heading('۲. وضعیت اجرای پروژه')
fa('ساختار پروژه و اجزای اصلی پیاده‌سازی شدند: آماده‌سازی داده، مدل پایهٔ آستانه‌ای، محاسبهٔ هندسهٔ ترک، دسته‌بندی جهت، غربالگری کد، رابط Gradio، فرمان‌های خط فرمان، تست‌ها و نوت‌بوک گزارش.')
summary = json.loads((ROOT / 'models' / 'metrics.json').read_text(encoding='utf-8'))
model = summary.get('model', {})
metadata_path = ROOT / 'data' / 'processed' / 'metadata.json'
metadata = json.loads(metadata_path.read_text(encoding='utf-8')) if metadata_path.exists() else {}
fa(f"داده: {metadata.get('count', 24)} تصویر مصنوعیِ جفت‌شده با ماسک تولید شد. دانلود دو منبع عمومی به‌علت محدودیت دسترسی شبکه در محیط اجرا ناموفق بود؛ در نتیجه، نتیجه‌های زیر مربوط به آزمون نرم‌افزار روی دادهٔ مصنوعی هستند، نه ارزیابی تعمیم به عکس‌های واقعی.")
fa(f"مدل اجراشده: مدل پایهٔ کلاسیک با آستانهٔ روشنایی {model.get('threshold', 'نامشخص')}؛ آموزش YOLO انجام نشد. در این مدل، mAP واقعی تعریف نشده و به‌درستی به‌صورت unavailable ثبت شده است.")
metrics_rows = [
    ['Split', 'Images', 'IoU', 'F1'],
]
for split in ('train', 'val', 'test'):
    item = summary.get(split, {})
    metrics_rows.append([split, str(item.get('images', '—')), f"{item.get('iou', 0):.4f}", f"{item.get('f1', 0):.4f}"])
metrics_table = Table(metrics_rows, colWidths=[doc.width * .25, doc.width * .2, doc.width * .25, doc.width * .3], repeatRows=1)
metrics_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), TEAL), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'), ('FONTSIZE', (0, 0), (-1, -1), 9),
    ('GRID', (0, 0), (-1, -1), .4, RULE), ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, PAPER]),
    ('ALIGN', (1, 0), (-1, -1), 'CENTER'), ('TOPPADDING', (0, 0), (-1, -1), 6), ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
]))
story.append(metrics_table)
story.append(Spacer(1, 4 * mm))
fa('اعتبارسنجی: کامپایل پایتون انجام شد و ۷ تست واحد با unittest موفق بودند. نوت‌بوک گزارش اجرا شد. رابط Gradio در همین محیط اجرا نشد، چون بستهٔ Gradio نصب نبود و نصب آنلاین آن به‌علت محدودیت شبکه ممکن نشد؛ کد رابط در پروژه موجود است.')
fa('محدودیت اندازه‌گیری: اگر مرجع پیکسلی وارد نشود، فرض پیش‌فرض ۱۰۰ میلی‌متر در عرض تصویر به‌کار می‌رود. برای عکس واقعی باید مقیاس با خط‌کش یا نشانگر کالیبره شود. مقدار پیش‌فرض مبحث ۹ برابر ۰٫۳۰ میلی‌متر یک مقدار قابل‌تنظیم پروژه‌ای است و باید با نسخه و ضوابط موردنظر تطبیق داده شود. نوار CAUTION نیز قرارداد هشدار برنامه است، نه الزام مستقل کد.')
fa('فایل‌های اصلی پروژه: README.md، ASSUMPTIONS.md، models/cracklens_classical.json، models/metrics.json و پوشه‌های src، tests و notebooks.')

heading('۳. روند انجام کار')
for item in [
    'پیوست کاربر به‌عنوان مشخصات کامل پروژهٔ CrackLens خوانده شد و اجرای انتهابه‌انتها در محدودهٔ امکان محیط آغاز شد.',
    'مخزن در آغاز خالی بود. به‌علت مسدودبودن دسترسی اینترنت، پروژه به مسیر آفلاین مجهز شد و دادهٔ مصنوعیِ قابل‌بازتولید به‌عنوان fallback ثبت شد.',
    'ماژول‌های قطعه‌بندی پایه، طول و عرض، زاویه و دسته‌بندی، verdict، رابط کاربری، خط فرمان، تست‌ها و گزارش ساخته شدند.',
    'دادهٔ نمونه ساخته و مدل آستانه‌ای آموزش داده شد؛ چهار تصویر آزمون تحلیل شدند و تصویرهای overlay و گزارش JSON تولید شدند.',
    'در یک دور اصلاح، ورودی دادهٔ جفت‌شده از ساختارهای محلی رایج اضافه شد و mAP برای مدل آستانه‌ای به‌جای عدد ساختگی، unavailable ثبت شد.',
    'در پایان، هفت تست موفق شدند و نوت‌بوک گزارش اجرا شد. نصب Gradio و pytest در محیط محدود باقی ماند.'
]:
    fa('• ' + item)

heading('۴. گفتگوی کاربر و پاسخ‌ها')
chat('درخواست کاربر', [('text', 'به‌عنوان کاربر چطور می‌توانم از برنامه استفاده کنم و خروجی بگیرم؟')])
chat('پاسخ دستیار', [
    ('text', 'برای استفاده در PowerShell، ترمینال را در پوشهٔ پروژه D:\\ai-amirali باز کنید. اگر وابستگی‌ها نصب نیستند، یک‌بار محیط مجازی را بسازید و بسته‌ها را نصب کنید:'),
    ('code', 'python -m venv .venv\n.\\.venv\\Scripts\\Activate.ps1\npython -m pip install -r requirements.txt'),
    ('text', 'سپس رابط برنامه را اجرا کنید:'),
    ('code', '$env:PYTHONPATH = "src"\npython -m cracklens demo'),
    ('text', 'در صفحه‌ای که برنامه باز می‌کند، تصویر تیر را بارگذاری کنید، طول مرجع معلوم را برحسب میلی‌متر و پیکسل وارد کنید، کد و شرایط محیطی را انتخاب کنید و Analyze cracks را بزنید. جدول شامل نوع، زاویه، طول، بیشینه و میانگین عرض و verdict است.'),
    ('text', 'برای ذخیرهٔ JSON و تصویر overlay از فرمان analyze استفاده کنید. اگر مرجع معلوم ندارید، مقدار پیش‌فرض کالیبره نیست و اندازه‌ها را واقعی تلقی نکنید.')
])

chat('درخواست کاربر', [('text', 'ستون verdict نشان‌دهندهٔ چه نتیجه‌ای را برای من مشخص می‌کند؟')])
chat('پاسخ دستیار', [('text', 'ستون Verdict نتیجهٔ غربالگری عرض ترک را نسبت به حدی که در برنامه انتخاب کرده‌اید نشان می‌دهد: PASS یعنی عرض تا ۸۰٪ حد انتخاب‌شده است؛ CAUTION یعنی عرض بین ۸۰٪ حد و خود حد است؛ FAIL یعنی عرض از حد انتخاب‌شده بیشتر است. برای حد ۰٫۳۰ میلی‌متر، تا ۰٫۲۴ PASS، از ۰٫۲۴ تا ۰٫۳۰ CAUTION و بالاتر از ۰٫۳۰ FAIL می‌شود. مرز ۸۰٪ قرارداد داخلی برنامه است و این برچسب‌ها تأیید ایمنی سازه نیستند؛ دقتشان به کالیبراسیون مقیاس تصویر وابسته است.')])

chat('درخواست کاربر', [('text', 'در یک پاراگراف به زبان ساده کارکرد برنامه را برای من شرح بده.')])
chat('پاسخ دستیار', [('text', 'برنامه تصویر تیر بتنی را بررسی می‌کند، ترک‌های قابل‌مشاهده را روی تصویر مشخص می‌کند و برای هر ترک طول، عرض و زاویه‌اش را تخمین می‌زند؛ سپس بر اساس زاویه، ترک را خمشی یا برشی دسته‌بندی می‌کند و عرضش را با حد انتخاب‌شده مقایسه می‌کند تا نتیجه‌ای مثل PASS، CAUTION یا FAIL نشان دهد. برای اینکه اندازه‌ها به میلی‌متر نزدیک باشند، باید مقیاس تصویر را با یک خط‌کش یا مرجع معلوم تنظیم کنید.')])

chat('درخواست کاربر', [('text', 'برای اینکه بتوانم برنامهٔ قابل‌اجرا را برای یک نفر بفرستم، چه فایل‌هایی را نیاز است برای وی بفرستم و آن شخص چه کارهایی را باید انجام دهد؟')])
chat('پاسخ دستیار', [
    ('text', 'پروژه فعلاً فایل اجرایی مستقل EXE نیست؛ ساده‌ترین راه فرستادن ZIP از پوشهٔ پروژه است. برای اجرای برنامه لازم است پوشهٔ src، مدل models/cracklens_classical.json، فایل‌های requirements.txt و README.md و نیز pyproject.toml، configs و ASSUMPTIONS.md داخل ZIP باشند. داده‌های آموزشی، نوت‌بوک‌ها و تست‌ها برای اجرای فقط رابط ضروری نیستند؛ metrics.json و یک تصویر نمونه اختیاری‌اند.'),
    ('text', 'گیرنده باید Python نسخهٔ ۳٫۱۰ یا بالاتر نصب کند، ZIP را باز کند، در PowerShell وارد پوشهٔ پروژه شود و این فرمان‌ها را اجرا کند:'),
    ('code', 'python -m venv .venv\n.\\.venv\\Scripts\\Activate.ps1\npython -m pip install -r requirements.txt\n$env:PYTHONPATH = "src"\npython -m cracklens demo'),
    ('text', 'بعد از بارگذاری تصویر و تنظیم کالیبراسیون، برنامه را اجرا می‌کند. برای ذخیرهٔ خروجی JSON و PNG، فرمان python -m cracklens analyze را با مسیر تصویر و پارامترهای مرجع اجرا می‌کند. نصب وابستگی‌ها معمولاً اینترنت می‌خواهد. مدل فعلی با دادهٔ مصنوعی آموزش دیده و برای تست اجراست، نه تصمیم مهندسی دربارهٔ تصاویر واقعی.')
])

chat('درخواست کاربر', [('text', 'یک نمونه تصویر تیر برای تست برنامه به من بده.')])
chat('پاسخ دستیار', [('text', 'تصویر نمونهٔ تیر ترک‌خورده ساخته و در پیام گفتگو ارائه شد. نسخهٔ محلی آن نیز در پوشهٔ artifacts با نام beam_test.png قرار گرفت تا داخل برنامه بارگذاری شود. تصویر خط‌کش کالیبراسیون ندارد؛ برای تست ظاهر خروجی مناسب است، اما اندازه‌های عرض ترک را واقعی تلقی نکنید.')])
heading('۵. نتیجهٔ تحلیل نمونه و شیوهٔ خروجی‌گرفتن')
fa('برای خروجی فایل، فرمان زیر یک فایل JSON و یک تصویر overlay با همان نام در پوشهٔ artifacts می‌سازد. مقادیر مرجع را با اندازهٔ واقعی نشانگر داخل عکس جایگزین کنید:')
code('python -m cracklens analyze `\n  --image "C:\\path\\beam.jpg" `\n  --output "artifacts\\beam01.json" `\n  --reference-mm 50 `\n  --reference-pixels 120 `\n  --code ACI224R `\n  --exposure humidity')
fa('فایل JSON شامل خلاصه و ردیف‌های ترک است؛ تصویر PNG، ماسک‌های شناسایی‌شده را روی تصویر ورودی نشان می‌دهد. رابط Gradio فعلی نتایج را روی صفحه نمایش می‌دهد و برای ذخیرهٔ جداگانه، از دستور خط فرمان بالا استفاده می‌شود.')

story.append(PageBreak())
heading('۶. نکات و منابع ثبت‌شده در گفتگو')
fa('حدود ACI در کد به‌عنوان راهنمای غربالگری و قابل‌تنظیم معرفی شده‌اند؛ برای کاربرد مهندسی باید نسخهٔ آیین‌نامه و شرایط محیطی پروژه بررسی شود. حد مبحث ۹ در پیاده‌سازی، مقدار پیش‌فرض قابل‌تنظیم است و ادعای حد جهانی یا قطعی ندارد.')
en('ACI reference mentioned in the prior response: https://www.concrete.org/portals/0/files/pdf/webinars/ws_S18_Tyler.pdf', 'latin_small')
en('DeepCrack dataset terms mentioned in the prior response: https://github.com/yhlleo/DeepCrack/blob/master/README.md?plain=1', 'latin_small')

# Full source attachment appendix
story.append(Paragraph('Appendix — Original project brief', styles['latin_h2']))
fa('این پیوست، متن استخراج‌شده از فایل اولیهٔ کاربر است. شکست خطوط ناشی از صفحه‌آرایی فایل مبدأ برای خوانایی دوباره‌چینی شده است.', 'small')
raw = ATTACHMENT.read_text(encoding='utf-8-sig').replace('\uffff', 'to')
source_lines = raw.splitlines()
clean_lines = []
for raw_line in source_lines:
    line = raw_line.strip()
    if not line:
        clean_lines.append('')
        continue
    if line.startswith('Master Codex Prompt: Zero-to-Hundred Automated Build of the RC Crack Inspection Project'):
        continue
    if line in {'1', '2', '3'}:
        continue
    clean_lines.append(line)
# Join only wrapped source lines and preserve blank-line paragraph boundaries.
paragraphs = []
buffer = []
for line in clean_lines:
    if not line:
        if buffer:
            paragraphs.append(' '.join(buffer))
            buffer = []
    else:
        buffer.append(line)
if buffer:
    paragraphs.append(' '.join(buffer))
joined = '\n'.join(paragraphs)
for old, new in {
    'Quan tification': 'Quantification', 'com pare': 'compare', 'com pliance': 'compliance',
    'andwarns': 'and warns', 'thatasking': 'that asking', 'preamblescancause': 'preambles can cause',
    'agentto': 'agent to', 'for bids': 'forbids', 'Tooldiscipline': 'Tool discipline',
    'keep builds/type-checks passing': 'keep builds/type-checks passing', 'zero-to hundred': 'zero-to-hundred',
}.items():
    joined = joined.replace(old, new)
appendix_blocks = joined.split('\n')
for block in appendix_blocks:
    block = block.strip()
    if not block:
        continue
    if re.match(r'^\d+\s+(Purpose and Target Project|Prompt Engineering Principles Applied|The Master Prompt|How to Run and Customize)', block):
        story.append(Paragraph(escape(block), styles['latin_h2']))
    elif block in {'Contents', '1 Purpose and Target Project', '2 Prompt Engineering Principles Applied', '3 The Master Prompt(Copy-Paste into Codex)', '4 How to Run and Customize'}:
        story.append(Paragraph(escape(block), styles['latin_h2']))
    else:
        story.append(Paragraph(escape(block), styles['latin']))


def on_page(canvas, _doc):
    page_chrome(canvas, _doc)

OUT.parent.mkdir(parents=True, exist_ok=True)
doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print(json.dumps({'pdf': str(OUT), 'bytes': OUT.stat().st_size, 'jalali_date': jalali_today_str(), 'attachment_characters': len(raw), 'pages': 'render to inspect'}, ensure_ascii=True))
