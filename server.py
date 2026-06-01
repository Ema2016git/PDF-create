# -*- coding: utf-8 -*-
import http.server
import json
import os
import uuid
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

PORT = 8000
PENDIENTES = {}  # token -> (filename, content_bytes, content_type)

CAMPOS = [
    ('lenguajes', 'Lenguajes'),
    ('saberes',   'Saberes y Pensamiento Cientifico'),
    ('etica',     'Etica, Naturaleza y Sociedades'),
    ('humano',    'De lo Humano y lo Comunitario'),
]
COLORES = {
    'lenguajes': '#6366f1',
    'saberes':   '#ec4899',
    'etica':     '#f59e0b',
    'humano':    '#10b981',
}

def esc(text):
    if not text:
        return ''
    return (text.replace('&','&amp;')
                .replace('<','&lt;')
                .replace('>','&gt;')
                .replace('\n','<br>'))

def generar_pdf(alumnos):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    CAMPO_COLORS_RL = {
        'lenguajes': colors.HexColor('#6366f1'),
        'saberes':   colors.HexColor('#ec4899'),
        'etica':     colors.HexColor('#f59e0b'),
        'humano':    colors.HexColor('#10b981'),
    }

    styles = getSampleStyleSheet()
    st_titulo = ParagraphStyle('titulo', parent=styles['Normal'],
                               fontSize=18, fontName='Helvetica-Bold',
                               alignment=TA_CENTER, spaceAfter=4)
    st_sub    = ParagraphStyle('sub', parent=styles['Normal'],
                               fontSize=11, fontName='Helvetica-Oblique',
                               textColor=colors.HexColor('#718096'),
                               alignment=TA_CENTER, spaceAfter=18)
    st_alumno = ParagraphStyle('alumno', parent=styles['Normal'],
                               fontSize=14, fontName='Helvetica-Bold',
                               textColor=colors.HexColor('#4f46e5'),
                               spaceBefore=14, spaceAfter=4)
    st_curp   = ParagraphStyle('curp', parent=styles['Normal'],
                               fontSize=11, spaceAfter=10)
    st_campo  = ParagraphStyle('campo', parent=styles['Normal'],
                               fontSize=12, fontName='Helvetica-Bold',
                               spaceBefore=10, spaceAfter=4)
    st_cell   = ParagraphStyle('cell', parent=styles['Normal'], fontSize=10)

    story = []
    story.append(Paragraph('EVALUACION DE CAMPOS FORMATIVOS', st_titulo))
    story.append(Paragraph('Preescolar - Registro de evaluaciones y observaciones', st_sub))

    for i, alumno in enumerate(alumnos):
        if i > 0:
            story.append(Spacer(1, 10))
            story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#e2e8f0')))
            story.append(Spacer(1, 10))

        nombre = alumno.get('nombre', '')
        curp   = alumno.get('curp', '') or '(No proporcionada)'
        story.append(Paragraph('Alumno: ' + nombre, st_alumno))
        story.append(Paragraph('<b>CURP:</b> ' + curp, st_curp))

        campos = alumno.get('campos', {})
        for key, nombre_campo in CAMPOS:
            campo = campos.get(key, {})
            ev    = campo.get('evaluacion', '') or '(Sin evaluacion)'
            obs   = campo.get('observaciones', '') or '(Sin observaciones)'
            col   = CAMPO_COLORS_RL.get(key, colors.HexColor('#4f46e5'))

            story.append(Paragraph(nombre_campo, ParagraphStyle(
                'cf_' + key, parent=st_campo, textColor=col)))

            data = [
                [Paragraph('<b>Evaluacion</b>', st_cell),
                 Paragraph(ev, st_cell)],
                [Paragraph('<b>Observaciones y Sugerencias</b>', st_cell),
                 Paragraph(obs, st_cell)],
            ]
            t = Table(data, colWidths=[5*cm, None])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f7fafc')),
                ('BOX',        (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
                ('INNERGRID',  (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
                ('VALIGN',     (0,0), (-1,-1), 'TOP'),
                ('TOPPADDING', (0,0), (-1,-1), 6),
                ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                ('LEFTPADDING',   (0,0), (-1,-1), 8),
                ('RIGHTPADDING',  (0,0), (-1,-1), 8),
            ]))
            story.append(t)
            story.append(Spacer(1, 4))

    doc.build(story)
    buf.seek(0)
    return buf.read()

def generar_doc(alumnos):
    p = []
    p.append("<html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>")
    p.append("<head><meta charset='utf-8'><style>")
    p.append("@page{margin:2cm}body{font-family:Calibri,Arial,sans-serif;color:#2d3748;line-height:1.6}")
    p.append(".titulo{text-align:center;font-size:18pt;font-weight:bold;margin-bottom:4pt}")
    p.append(".sub{text-align:center;font-size:11pt;color:#718096;font-style:italic;margin-bottom:20pt}")
    p.append(".alumno{font-size:14pt;font-weight:bold;color:#4f46e5;margin-top:18pt;margin-bottom:6pt;border-bottom:2px solid #4f46e5;padding-bottom:4pt}")
    p.append(".curp{font-size:11pt;margin-bottom:12pt}")
    p.append(".campo{font-size:12pt;font-weight:bold;margin-top:12pt;margin-bottom:4pt;padding:5pt 10pt}")
    p.append("table{width:100%;border-collapse:collapse;margin-bottom:10pt}")
    p.append("td{padding:6pt 10pt;vertical-align:top;font-size:11pt;border:1px solid #e2e8f0}")
    p.append("td.l{width:180pt;font-weight:bold;color:#4a5568;background:#f7fafc}")
    p.append("hr{border:none;border-top:2px solid #e2e8f0;margin:20pt 0}")
    p.append("</style></head><body>")
    p.append("<p class='titulo'>EVALUACION DE CAMPOS FORMATIVOS</p>")
    p.append("<p class='sub'>Preescolar - Registro de evaluaciones y observaciones</p>")
    for i, alumno in enumerate(alumnos):
        if i > 0:
            p.append("<hr>")
        p.append("<p class='alumno'>Alumno: " + esc(alumno.get('nombre','')) + "</p>")
        p.append("<p class='curp'><b>CURP:</b> " + (esc(alumno.get('curp','')) or '(No proporcionada)') + "</p>")
        campos = alumno.get('campos', {})
        for key, nombre_campo in CAMPOS:
            campo = campos.get(key, {})
            col = COLORES.get(key, '#4f46e5')
            p.append("<p class='campo' style='border-left:4pt solid " + col + ";background:" + col + "18'>" + nombre_campo + "</p>")
            p.append("<table>")
            p.append("<tr><td class='l'>Evaluacion</td><td>" + (esc(campo.get('evaluacion','')) or '(Sin evaluacion)') + "</td></tr>")
            p.append("<tr><td class='l'>Observaciones y Sugerencias</td><td>" + (esc(campo.get('observaciones','')) or '(Sin observaciones)') + "</td></tr>")
            p.append("</table>")
    p.append("</body></html>")
    return '\n'.join(p)


class Handler(http.server.BaseHTTPRequestHandler):

    def send_json(self, data):
        body = json.dumps(data).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(self.path)

        if parsed.path in ('/', '/index.html'):
            filepath = os.path.join(os.path.dirname(__file__), 'index.html')
            with open(filepath, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        elif parsed.path == '/download':
            params = parse_qs(parsed.query)
            token  = params.get('token', [''])[0]
            modo   = params.get('modo', ['word'])[0]
            if token in PENDIENTES:
                filename, content_bytes, ctype = PENDIENTES.pop(token)
                self.send_response(200)
                self.send_header('Content-Type', ctype)
                self.send_header('Content-Disposition', 'attachment; filename="' + filename + '"')
                self.send_header('Content-Length', str(len(content_bytes)))
                self.end_headers()
                self.wfile.write(content_bytes)
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/save':
            length = int(self.headers.get('Content-Length', 0))
            body   = self.rfile.read(length)
            data   = json.loads(body.decode('utf-8'))

            alumnos  = data.get('alumnos', [])
            filename = data.get('filename', 'Evaluacion.doc')

            pdf_bytes = generar_pdf(alumnos)
            filename  = filename.replace('.doc', '.pdf')
            token = str(uuid.uuid4())
            PENDIENTES[token] = (filename, pdf_bytes, 'application/pdf')

            self.send_json({'token': token})
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print("Servidor en http://localhost:" + str(PORT))
    with http.server.HTTPServer(("", PORT), Handler) as httpd:
        httpd.serve_forever()
