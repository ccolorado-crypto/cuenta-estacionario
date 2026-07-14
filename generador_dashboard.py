import pandas as pd
import plotly.express as px
from datetime import date, datetime
import sys

def generar_dashboard():
    print("Leyendo el archivo data.ods...")
    
    try:
        df = pd.read_excel('data/data.ods', engine='odf')
    except Exception as e:
        print(f"Error crítico al leer el archivo: {e}")
        sys.exit(1)

    # MAPEO EXACTO DE COLUMNAS SEGÚN TU ESTRUCTURA
    # A=0, B=1, C=2, D=3, F=5, R=17
    col_dealer = df.columns[1]      # Columna B: Dealer
    col_cliente = df.columns[2]     # Columna C: Cliente
    col_generador = df.columns[3]   # Columna D: Nombre del generador
    col_tecnologia = df.columns[5]  # Columna F: Tecnología
    col_fecha = df.columns[17]      # Columna R: Fecha de conexión

    # Extraer el nombre del Dealer (tomamos el primer valor válido que no esté vacío)
    nombre_dealer = df[col_dealer].dropna().iloc[0] if not df[col_dealer].dropna().empty else "Dealer Principal"

    # Convertir fecha
    df[col_fecha] = pd.to_datetime(df[col_fecha], errors='coerce').dt.date
    fecha_hoy = date.today()

    # LÓGICA DE CONECTIVIDAD Y DÍAS DESCONECTADO
    def clasificar_estado(fecha):
        if pd.isna(fecha): return 'Fuera de cobertura'
        if fecha >= fecha_hoy: return 'Operando'
        return 'Fuera de cobertura'
        
    def clasificar_tiempo_fuera(fecha):
        if pd.isna(fecha): return 'Sin registro previo'
        diferencia = (fecha_hoy - fecha).days
        if diferencia <= 0: return 'Conectado'
        if diferencia <= 3: return '1 a 3 días'
        if diferencia <= 7: return '4 a 7 días'
        return 'Más de 7 días'

    df['Estado_Conectividad'] = df[col_fecha].apply(clasificar_estado)
    df['Tiempo_Desconectado'] = df[col_fecha].apply(clasificar_tiempo_fuera)

    # CÁLCULO DE KPIs
    total_equipos = len(df)
    equipos_operando = len(df[df['Estado_Conectividad'] == 'Operando'])
    equipos_fuera = total_equipos - equipos_operando
    porcentaje_operando = round((equipos_operando / total_equipos) * 100, 1) if total_equipos > 0 else 0
    # Obtenemos la hora actual de Colombia (UTC-5) para que sea precisa
    fecha_actualizacion = datetime.now().strftime("%d/%m/%Y a las %H:%M")

    # ---------------- GRÁFICOS ----------------

    # GRÁFICO 1: Estado General (Dona)
    conteo_estado = df['Estado_Conectividad'].value_counts().reset_index()
    conteo_estado.columns = ['Estado', 'Cantidad']
    fig1 = px.pie(conteo_estado, values='Cantidad', names='Estado', 
                  title='Estado General de la Flota',
                  color='Estado', 
                  color_discrete_map={'Operando':'#28a745', 'Fuera de cobertura':'#dc3545'},
                  hole=0.4)

    # GRÁFICO 2: Conectividad por Tecnología (Barras)
    conteo_tech = df.groupby([col_tecnologia, 'Estado_Conectividad']).size().reset_index(name='Cantidad')
    fig2 = px.bar(conteo_tech, x=col_tecnologia, y='Cantidad', color='Estado_Conectividad',
                  title='Conectividad por Tecnología',
                  barmode='group',
                  color_discrete_map={'Operando':'#28a745', 'Fuera de cobertura':'#dc3545'},
                  labels={col_tecnologia: 'Tecnología', 'Cantidad': 'Equipos'})

    # GRÁFICO 3: Impacto por Cliente (Barras Apiladas) - NUEVO
    conteo_cliente = df.groupby([col_cliente, 'Estado_Conectividad']).size().reset_index(name='Cantidad')
    fig3 = px.bar(conteo_cliente, x=col_cliente, y='Cantidad', color='Estado_Conectividad',
                  title='Estado de Equipos por Cliente',
                  barmode='stack', # Apilado para ver el volumen total por cliente
                  color_discrete_map={'Operando':'#28a745', 'Fuera de cobertura':'#dc3545'},
                  labels={col_cliente: 'Cliente', 'Cantidad': 'Equipos'})
    # Girar un poco los nombres de los clientes para que se lean mejor
    fig3.update_layout(xaxis_tickangle=-45)

    # GRÁFICO 4: Gravedad de Desconexión
    df_fuera = df[df['Estado_Conectividad'] == 'Fuera de cobertura']
    conteo_tiempo = df_fuera['Tiempo_Desconectado'].value_counts().reset_index()
    conteo_tiempo.columns = ['Tiempo', 'Cantidad']
    fig4 = px.bar(conteo_tiempo, x='Tiempo', y='Cantidad',
                  title='Gravedad de Desconexión (Tiempo Offline)',
                  color='Tiempo',
                  color_discrete_sequence=px.colors.sequential.OrRd)

    # TABLA DE EQUIPOS CRÍTICOS (Ahora incluye Generador y Cliente)
    # Filtramos las columnas útiles y ordenamos por los más antiguos
    df_criticos = df_fuera.sort_values(by=col_fecha, na_position='first').head(20)
    tabla_criticos = df_criticos[[col_generador, col_cliente, col_tecnologia, col_fecha, 'Tiempo_Desconectado']].to_html(
        classes='data-table', index=False, na_rep='Sin registro'
    )

    # CONVERTIR GRÁFICOS A HTML
    html_fig1 = fig1.to_html(full_html=False, include_plotlyjs='cdn')
    html_fig2 = fig2.to_html(full_html=False, include_plotlyjs=False)
    html_fig3 = fig3.to_html(full_html=False, include_plotlyjs=False)
    html_fig4 = fig4.to_html(full_html=False, include_plotlyjs=False)

    # ---------------- PLANTILLA HTML ----------------
    dashboard_html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Dashboard {nombre_dealer}</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; padding: 20px; }}
            h1 {{ text-align: center; color: #2c3e50; margin-bottom: 5px; }}
            .subtitle {{ text-align: center; color: #7f8c8d; margin-bottom: 30px; font-size: 14px; }}
            
            /* KPIs */
            .kpi-container {{ display: flex; justify-content: space-between; gap: 20px; max-width: 1200px; margin: 0 auto 30px auto; }}
            .kpi-card {{ background: white; border-radius: 12px; padding: 20px; flex: 1; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
            .kpi-card h3 {{ margin: 0; color: #7f8c8d; font-size: 16px; font-weight: normal; }}
            .kpi-card .value {{ font-size: 32px; font-weight: bold; color: #2c3e50; margin-top: 10px; }}
            .kpi-card .value.green {{ color: #28a745; }}
            .kpi-card .value.red {{ color: #dc3545; }}
            
            /* Gráficos */
            .dashboard-container {{ max-width: 1200px; margin: 0 auto; display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
            .chart-card {{ background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); padding: 20px; }}
            .full-width {{ grid-column: 1 / -1; }}
            
            /* Tabla */
            .table-container {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); max-width: 1200px; margin: 20px auto; overflow-x: auto; }}
            .table-container h2 {{ color: #2c3e50; margin-top: 0; }}
            .data-table {{ width: 100%; border-collapse: collapse; text-align: left; }}
            .data-table th, .data-table td {{ padding: 12px 15px; border-bottom: 1px solid #e0e0e0; }}
            .data-table th {{ background-color: #f8f9fa; color: #2c3e50; font-weight: bold; }}
            .data-table tr:hover {{ background-color: #f1f4f6; }}
            
            @media (max-width: 768px) {{
                .dashboard-container {{ grid-template-columns: 1fr; }}
                .kpi-container {{ flex-direction: column; }}
            }}
        </style>
    </head>
    <body>
        <h1>📊 Conectividad - {nombre_dealer}</h1>
        <div class="subtitle">Última actualización automática: {fecha_actualizacion}</div>
        
        <div class="kpi-container">
            <div class="kpi-card">
                <h3>Total de Generadores</h3>
                <div class="value">{total_equipos}</div>
            </div>
            <div class="kpi-card">
                <h3>En línea (Operando)</h3>
                <div class="value green">{porcentaje_operando}%</div>
            </div>
            <div class="kpi-card">
                <h3>Equipos Offline</h3>
                <div class="value red">{equipos_fuera}</div>
            </div>
        </div>

        <div class="dashboard-container">
            <div class="chart-card">
                {html_fig1}
            </div>
            <div class="chart-card">
                {html_fig2}
            </div>
            <div class="chart-card full-width">
                {html_fig3}
            </div>
            <div class="chart-card full-width">
                {html_fig4}
            </div>
        </div>

        <div class="table-container">
            <h2>⚠️ Atención Requerida: Top 20 Generadores Desconectados</h2>
            <p style="color: #7f8c8d; font-size: 14px;">Muestra los equipos que llevan más tiempo sin reportar conexión hacia la plataforma.</p>
            {tabla_criticos}
        </div>
    </body>
    </html>
    """

    with open('dashboard_conectividad.html', 'w', encoding='utf-8') as f:
        f.write(dashboard_html)
    print("Dashboard profesional generado exitosamente.")

if __name__ == "__main__":
    generar_dashboard()
