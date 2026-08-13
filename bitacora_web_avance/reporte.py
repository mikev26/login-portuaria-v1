from datetime import date
import io
import pandas as pd
from flask import Flask, render_template, request, send_file
pyodbc = __import__('pyodbc')

app = Flask(__name__)

def conectar_db():
    conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=192.168.3.17;'
        'DATABASE=dim_sis_puerto_v1;'
        'UID=UserGSoep;'
        'PWD=GSoep*2026*'
    )
    return conn

def fecha_valida(valor, predeterminada):
    try:
        date.fromisoformat(valor)
        return valor
    except (TypeError, ValueError):
        return predeterminada

def obtener_registros_filtrados(form_data):
    # Optimizado: por defecto arranca en el año actual para mayor velocidad
    f_desde = fecha_valida(form_data.get('f_desde'), '2026-01-01')
    f_hasta = fecha_valida(form_data.get('f_hasta'), '2026-12-31')
    en_puerto_filtro = True if form_data.get('en_puerto_filtro') == 'on' else False
    
    chk_buque = True if form_data.get('chk_buque') == 'on' else False
    sel_buque = form_data.get('sel_buque', '')
    chk_tiponave = True if form_data.get('chk_tiponave') == 'on' else False
    sel_tiponave = form_data.get('sel_tiponave', '')
    chk_armador = True if form_data.get('chk_armador') == 'on' else False
    sel_armador = form_data.get('sel_armador', '')
    chk_procedencia = True if form_data.get('chk_procedencia') == 'on' else False
    sel_procedencia = form_data.get('sel_procedencia', '')
    chk_destino = True if form_data.get('chk_destino') == 'on' else False
    sel_destino = form_data.get('sel_destino', '')
    chk_estado = True if form_data.get('chk_estado') == 'on' else False
    sel_estado = form_data.get('sel_estado', '')

    registros = []
    try:
        with conectar_db() as conn:
            cursor = conn.cursor()
            cursor.execute('EXEC SPJ_ReporteRegistroBuques ?, ?', f_desde, f_hasta)
            columns = [column[0] for column in cursor.description]
            raw_rows = cursor.fetchall()
            registros = [dict(zip(columns, row)) for row in raw_rows]
            
            for r in registros:
                if 'fecha_arrivo' in r:
                    r['fecha_arribo'] = r['fecha_arrivo']
                elif 'f_arribo' in r:
                    r['fecha_arribo'] = r['f_arribo']
                if 'fecha_zarpe' in r:
                    r['fecha_zarpe'] = r['fecha_zarpe']
                elif 'f_zarpe' in r:
                    r['fecha_zarpe'] = r['f_zarpe']
    except Exception:
        pass

    if en_puerto_filtro:
        registros = [
            r for r in registros 
            if not r.get('fecha_zarpe') or str(r.get('fecha_zarpe')).strip() in ['', 'None', 'NULL', 'NoneType']
        ]

    if chk_buque and sel_buque:
        registros = [r for r in registros if str(r.get('buque')) == sel_buque]
    if chk_tiponave and sel_tiponave:
        registros = [r for r in registros if str(r.get('tipo_de_trafico')) == sel_tiponave]
    if chk_armador and sel_armador:
        registros = [r for r in registros if str(r.get('armador')) == sel_armador]
    if chk_procedencia and sel_procedencia:
        registros = [r for r in registros if str(r.get('procedencia')) == sel_procedencia]
    if chk_destino and sel_destino:
        registros = [r for r in registros if str(r.get('destino')) == sel_destino]
    if chk_estado and sel_estado:
        registros = [r for r in registros if str(r.get('estado')) == sel_estado]

    return registros

@app.route('/', methods=['GET', 'POST'])
def index():
    registros = []
    fechas_aplicadas = False
    # Optimizado: por defecto arranca en el año actual
    f_desde = fecha_valida(request.form.get('f_desde'), '2026-01-01')
    f_hasta = fecha_valida(request.form.get('f_hasta'), '2026-12-31')
    en_puerto_filtro = True if request.form.get('en_puerto_filtro') == 'on' else False
    
    chk_buque = True if request.form.get('chk_buque') == 'on' else False
    sel_buque = request.form.get('sel_buque', '')
    chk_tiponave = True if request.form.get('chk_tiponave') == 'on' else False
    sel_tiponave = request.form.get('sel_tiponave', '')
    chk_armador = True if request.form.get('chk_armador') == 'on' else False
    sel_armador = request.form.get('sel_armador', '')
    chk_procedencia = True if request.form.get('chk_procedencia') == 'on' else False
    sel_procedencia = request.form.get('sel_procedencia', '')
    chk_destino = True if request.form.get('chk_destino') == 'on' else False
    sel_destino = request.form.get('sel_destino', '')
    chk_estado = True if request.form.get('chk_estado') == 'on' else False
    sel_estado = request.form.get('sel_estado', '')

    mensaje_error = None
    buques, tipos_nave, armadores, procedencias, destinos, estados, banderas, scregistros = [], [], [], [], [], [], [], []

    if request.method == 'POST':
        fechas_aplicadas = True
        registros = obtener_registros_filtrados(request.form)
        if not registros:
            mensaje_error = 'No se pudo cargar el reporte o no hay registros.'
        else:
            buques = sorted(list(set(str(r.get('buque')) for r in registros if r.get('buque'))))
            tipos_nave = sorted(list(set(str(r.get('tipo_de_trafico')) for r in registros if r.get('tipo_de_trafico'))))
            armadores = sorted(list(set(str(r.get('armador')) for r in registros if r.get('armador'))))
            procedencias = sorted(list(set(str(r.get('procedencia')) for r in registros if r.get('procedencia'))))
            destinos = sorted(list(set(str(r.get('destino')) for r in registros if r.get('destino'))))
            estados = sorted(list(set(str(r.get('estado')) for r in registros if r.get('estado'))))
            banderas = sorted(list(set(str(r.get('bandera')) for r in registros if r.get('bandera'))))
            scregistros = sorted(list(set(str(r.get('scregistro')) for r in registros if r.get('scregistro'))))

    return render_template('index.html', 
                           f_desde=f_desde, f_hasta=f_hasta,
                           fechas_aplicadas=fechas_aplicadas,
                           en_puerto_filtro=en_puerto_filtro,
                           chk_buque=chk_buque, sel_buque=sel_buque,
                           chk_tiponave=chk_tiponave, sel_tiponave=sel_tiponave,
                           chk_armador=chk_armador, sel_armador=sel_armador,
                           chk_procedencia=chk_procedencia, sel_procedencia=sel_procedencia,
                           chk_destino=chk_destino, sel_destino=sel_destino,
                           chk_estado=chk_estado, sel_estado=sel_estado,
                           buques=buques, tipos_nave=tipos_nave, armadores=armadores,
                           procedencias=procedencias, destinos=destinos, estados=estados,
                           banderas=banderas, scregistros=scregistros,
                           registros=registros,
                           mensaje_error=mensaje_error)

@app.route('/exportar', methods=['POST'])
def exportar():
    registros = obtener_registros_filtrados(request.form)
    df = pd.DataFrame(registros)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='ReporteBuques')
        
        # Auto-ajustar ancho de columnas para evitar los '########' en fechas/textos
        worksheet = writer.sheets['ReporteBuques']
        for col in worksheet.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = col[0].column_letter
            worksheet.column_dimensions[col_letter].width = max(max_len + 3, 12)
            
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='volcado_registros_buques.xlsx'
    )

if __name__ == '__main__':
    app.run(debug=True)