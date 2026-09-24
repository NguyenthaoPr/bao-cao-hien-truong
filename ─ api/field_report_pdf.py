from io import BytesIO
import os, re, time, html
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


PRIMARY=colors.HexColor('#0B4F6C'); ACCENT=colors.HexColor('#1B7A8C'); TEXT=colors.HexColor('#20303B'); MUTED=colors.HexColor('#5A6B75'); LIGHT=colors.HexColor('#EAF2F5')
ORG='CHI NHÁNH THỦY LỢI VU GIA - THU BỒN'; APP='THỦY LỢI AI'

def fonts():
    reg='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'; bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    if os.path.exists(reg):
        pdfmetrics.registerFont(TTFont('TLUnicode',reg)); pdfmetrics.registerFont(TTFont('TLUnicode-Bold',bold if os.path.exists(bold) else reg)); return 'TLUnicode','TLUnicode-Bold'
    return 'Helvetica','Helvetica-Bold'

def esc(s): return html.escape(str(s or ''))

def footer(canvas, doc, title, fr, fb, when):
    canvas.saveState(); w,h=A4
    canvas.setFillColor(PRIMARY); canvas.rect(0,h-24*mm,w,24*mm,stroke=0,fill=1)
    canvas.setFillColor(colors.white); canvas.setFont(fb,11.5); canvas.drawString(20*mm,h-10*mm,ORG)
    canvas.setFont(fr,9); canvas.drawString(20*mm,h-16*mm,f'BÁO CÁO NHANH HIỆN TRƯỜNG • {title}')
    canvas.setFont(fb,10); canvas.drawRightString(w-20*mm,h-13*mm,APP)
    canvas.setStrokeColor(colors.HexColor('#C9D8DE')); canvas.line(20*mm,16*mm,w-20*mm,16*mm)
    canvas.setFillColor(MUTED); canvas.setFont(fr,8); canvas.drawCentredString(w/2,11*mm,f'{APP} • Trang {doc.page}')
    canvas.restoreState()

def build_pdf(title, answer, image_bytes, reviewer, capture_time, lat, lng, sources):
    buf=BytesIO(); fr,fb=fonts()
    doc=SimpleDocTemplate(buf,pagesize=A4,leftMargin=20*mm,rightMargin=20*mm,topMargin=32*mm,bottomMargin=22*mm,title=title,author=ORG)
    styles=getSampleStyleSheet()
    title_s=ParagraphStyle('t',parent=styles['Title'],fontName=fb,fontSize=17,leading=22,alignment=TA_CENTER,textColor=PRIMARY,spaceAfter=6)
    head=ParagraphStyle('h',parent=styles['Heading2'],fontName=fb,fontSize=11.5,leading=15,textColor=ACCENT,spaceBefore=8,spaceAfter=4)
    body=ParagraphStyle('b',parent=styles['BodyText'],fontName=fr,fontSize=10.2,leading=15,textColor=TEXT,spaceAfter=4)
    note=ParagraphStyle('n',parent=body,fontSize=9.2,textColor=MUTED,backColor=LIGHT,borderPadding=7)
    story=[Paragraph('BÁO CÁO NHANH HIỆN TRƯỜNG',title_s),Paragraph(esc(title),ParagraphStyle('st',parent=body,fontName=fb,alignment=TA_CENTER,textColor=ACCENT)),Spacer(1,5)]
    info=[['Thời gian',capture_time or time.strftime('%H:%M %d/%m/%Y')],['Người kiểm tra',reviewer or 'Chưa cung cấp'],['Tọa độ GPS',f'{lat}, {lng}' if lat and lng else 'Chưa có']]
    tbl=Table([[Paragraph(f'<b>{esc(a)}</b>',body),Paragraph(esc(b),body)] for a,b in info],colWidths=[42*mm,118*mm])
    tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(0,-1),LIGHT),('BOX',(0,0),(-1,-1),0.5,colors.HexColor('#C9D8DE')),('INNERGRID',(0,0),(-1,-1),0.25,colors.HexColor('#C9D8DE')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7)]))
    story += [tbl,Spacer(1,8)]
    if image_bytes:
        try:
            img=RLImage(BytesIO(image_bytes)); maxw=160*mm; maxh=95*mm; scale=min(maxw/img.imageWidth,maxh/img.imageHeight,1); img.drawWidth=img.imageWidth*scale; img.drawHeight=img.imageHeight*scale; story += [Paragraph('Ảnh hiện trường',head),img,Spacer(1,7)]
        except Exception: pass
    story.append(Paragraph('Nội dung báo cáo',head))
    text=str(answer or '').replace('\r','')
    for raw in text.split('\n'):
        line=raw.strip()
        if not line: story.append(Spacer(1,3)); continue
        line=re.sub(r'^#{1,6}\s*','',line)
        if re.match(r'^\d+[.)]\s+',line): story.append(Paragraph(esc(line),head))
        elif re.match(r'^[-*•]\s+',line): story.append(Paragraph('• '+esc(re.sub(r'^[-*•]\s+','',line)),body))
        elif len(line)<70 and line.isupper(): story.append(Paragraph(esc(line),head))
        else: story.append(Paragraph(esc(line),body))
    if sources:
        story += [Paragraph('Nguồn hồ sơ File Search',head)]
        for s in sources:
            name=s.get('file_name') or 'Tài liệu THỦY LỢI AI'; page=s.get('page_number'); suffix=f' — trang {page}' if page else ''
            story.append(Paragraph('• '+esc(name+suffix),note))
    story += [Spacer(1,10),Paragraph('Lưu ý: Đây là dự thảo hỗ trợ nghiệp vụ; cán bộ có thẩm quyền cần kiểm tra, xác nhận trước khi sử dụng như báo cáo chính thức.',note)]
    doc.build(story,onFirstPage=lambda c,d:footer(c,d,title,fr,fb,capture_time),onLaterPages=lambda c,d:footer(c,d,title,fr,fb,capture_time))
    return buf.getvalue()

