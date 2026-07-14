import pandas as pd
import plotly.express as px
from datetime import date

def generar_dashboard():
    print("Leyendo el archivo data.ods...")
    
    # 1. Cargar los datos
    # Usamos engine='odf' para poder leer formatos de LibreOffice/OpenOffice
    try:
      df = pd.read_excel('data/data.ods', engine='odf')
  except Exception as e:
        import sys
        print(f"Error crítico al leer el archivo: {e}")
        sys.exit(1) # Esto le dice a GitHub Actions que aborte el proceso

    # Mapeo de columnas basándonos en tu descripción (A=0, B=1... F=5, R=17)
    # Tomamos los nombres de las columnas en esos índices
    col_tecnologia = df.columns[5]  # Columna F
    col_fecha = df.columns[17]      # Columna R

    print(f"Columna de Tecnología detectada: {col_tecnologia}")
    print(f"Columna de Fecha detectada: {col_fecha}")

    # Convertir la columna R a formato de fecha puro
    df[col_fecha] = pd.to_datetime(df[col_fecha], errors='coerce').dt.date

    # 2. Lógica de conectividad (Regla de la columna R)
    fecha_hoy = date.today()

    def clasificar_estado(fecha):
        # Si la celda está vacía o es una fecha anterior a hoy
        if pd.isna(fecha):
            return 'Fuera de cobertura'
        elif fecha >= fecha_hoy:
            return 'Operando'
        else:
            return 'Fuera de cobertura'

    # Aplicamos la regla para crear una nueva columna de estado
    df['Estado_Conectividad'] = df[col_fecha].apply(clasificar_estado)

    # 3. Gráfico 1: Máquinas comunicando vs Fuera de cobertura
    print("Generando gráfico de estado general...")
    conteo_estado = df['Estado_Conectividad'].value_counts().reset_index()
    conteo_estado.columns = ['Estado', 'Cantidad']
    
    fig1 = px.pie(conteo_estado, values='Cantidad', names='Estado', 
                  title='Estado General de Conectividad de los Equipos',
                  color='Estado', 
                  color_discrete_map={'Operando':'#28a745', 'Fuera de cobertura':'#dc3545'},
                  hole=0.4) # Estilo de dona para que se vea más moderno

    # 4. Gráfico 2: Conectividad por Tecnología (Regla de la columna F)
    print("Generando gráfico por tecnología...")
    # Agrupamos por tecnología (Col F) y el nuevo estado
    conteo_tech = df.groupby([col_tecnologia, 'Estado_Conectividad']).size().reset_index(name='Cantidad')
    
    fig2 = px.bar(conteo_tech, x=col_tecnologia, y='Cantidad', color='Estado_Conectividad',
                  title='Estado de Conectividad por Tecnología',
                  barmode='group', # Barras agrupadas lado a lado
                  color_discrete_map={'Operando':'#28a745', 'Fuera de cobertura':'#dc3545'},
                  labels={col_tecnologia: 'Tecnología', 'Cantidad': 'Número de Equipos'})

    # 5. Exportar a Dashboard HTML
    print("Ensamblando el dashboard HTML...")
    # Convertimos los gráficos de Plotly a fragmentos HTML interactivos
    html_fig1 = fig1.to_html(full_html=False, include_plotlyjs='cdn')
    html_fig2 = fig2.to_html(full_html=False, include_plotlyjs=False) # Ya se incluyó el script arriba

    # Plantilla web responsiva
    dashboard_html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Dashboard de Conectividad - Dealer</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; padding: 20px; }}
            h1 {{ text-align: center; color: #2c3e50; margin-bottom: 30px; }}
            .dashboard-container {{ max-width: 1200px; margin: 0 auto; display: flex; flex-direction: column; gap: 30px; }}
            .chart-card {{ background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); padding: 20px; transition: transform 0.2s; }}
            .chart-card:hover {{ transform: translateY(-2px); box-shadow: 0 6px 15px rgba(0,0,0,0.1); }}
        </style>
    </head>
    <body>
        <h1>📊 Dashboard de Conectividad de Equipos</h1>
        
        <div class="dashboard-container">
            <div class="chart-card">
                {html_fig1}
            </div>
            
            <div class="chart-card">
                {html_fig2}
            </div>
        </div>
    </body>
    </html>
    """

    # Escribir el archivo final
    with open('dashboard_conectividad.html', 'w', encoding='utf-8') as f:
        f.write(dashboard_html)

    print("¡Listo! Se ha creado el archivo 'dashboard_conectividad.html'. Puedes abrirlo con cualquier navegador web.")

if __name__ == "__main__":
    generar_dashboard()
