import pandas as pd
import json
from datetime import date, datetime, timedelta
import sys

def generar_dashboard():
    print("Iniciando procesamiento de datos...")
    
    try:
        df = pd.read_excel('data/data.ods', engine='odf')
    except Exception as e:
        print(f"Error crítico al leer el archivo: {e}")
        sys.exit(1)

    # MAPEO DE COLUMNAS
    col_dealer = df.columns[1]
    col_cliente = df.columns[2]
    col_generador = df.columns[3]
    col_tecnologia = df.columns[5]
    col_fecha = df.columns[17]

    nombre_dealer = str(df[col_dealer].dropna().iloc[0]) if not df[col_dealer].dropna().empty else "Dealer Principal"

    df[col_fecha] = pd.to_datetime(df[col_fecha], errors='coerce').dt.date
    fecha_hoy = date.today()
    
    records = []
    for idx, row in df.iterrows():
        cliente = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else "Sin Cliente"
        generador = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else "Sin Nombre"
        tech = str(row.iloc[5]).strip() if pd.notna(row.iloc[5]) else "Desconocida"
        
        raw_fecha = row.iloc[17]
        fecha_str = "Sin registro"
        status = "Fuera de cobertura"
        gravity = "Sin registro previo"
        dias_offline = -1
        
        if pd.notna(raw_fecha):
            fecha_str = raw_fecha.strftime("%d/%m/%Y")
            if raw_fecha >= fecha_hoy:
                status = "Operando"
                gravity = "Conectado"
                dias_offline = 0
            else:
                status = "Fuera de cobertura"
                dias_offline = (fecha_hoy - raw_fecha).days
                if dias_offline <= 3:
                    gravity = "1 a 3 días"
                elif dias_offline <= 7:
                    gravity = "4 a 7 días"
                else:
                    gravity = "Más de 7 días"
                    
        records.append({
            "generador": generador,
            "cliente": cliente,
            "tecnologia": tech,
            "fecha": fecha_str,
            "estado": status,
            "gravedad": gravity,
            "dias_offline": dias_offline
        })

    data_json = json.dumps(records, ensure_ascii=False)
    colombia_time = datetime.utcnow() - timedelta(hours=5)
    fecha_actualizacion = colombia_time.strftime("%d/%m/%Y a las %H:%M (Hora Col)")

    dashboard_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{nombre_dealer} — Dashboard ÁRTIMO</title>
    <link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@300;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
    <!-- Librería para exportar a PDF -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    <style>
        :root {{
            --artimo-rojo-oscuro:   #BC1818;
            --artimo-rojo-vivo:     #E10B17;
            --artimo-gris:          #5A5A59;
            --artimo-negro:         #1A1A1A;
            --artimo-blanco:        #FFFFFF;
            --artimo-gris-claro:    #F2F2F2;
        }}

        body {{ font-family: 'Open Sans', Arial, sans-serif; font-weight: 300; background: #F4F5F7; color: var(--artimo-negro); margin: 0; padding: 0; }}
        
        /* FIX: Topbar Responsiva y adaptada a nombres largos */
        .topbar {{ 
            background: var(--artimo-negro); color: var(--artimo-blanco); min-height: 56px; 
            display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; 
            padding: 10px 24px; position: sticky; top: 0; z-index: 100; box-shadow: 0 2px 8px rgba(0,0,0,0.3); gap: 15px;
        }}
        .topbar-brand {{ display: flex; align-items: center; gap: 15px; flex: 1; min-width: 300px; overflow: hidden; }}
        .topbar-brand img {{ height: 36px; object-fit: contain; }}
        .topbar-title-container {{ flex: 1; min-width: 0; }}
        .topbar-title {{ 
            font-size: 16px; font-weight: 600; margin: 0; line-height: 1.2; 
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis; /* Evita que rompa el diseño */
        }}
        .topbar-sub {{ font-size: 11px; color: #9CA3AF; font-weight: 300; margin: 0; margin-top: 2px; }}
        
        .topbar-right {{ display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }}
        .filter-select {{ background: #2a2a2a; color: white; border: 1px solid #4B5563; padding: 8px 12px; border-radius: 6px; font-size: 13px; font-family: 'Open Sans'; outline: none; cursor: pointer; max-width: 250px; text-overflow: ellipsis; }}
        
        /* Botones de Descarga */
        .btn-action {{ 
            padding: 8px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; font-family: 'Open Sans';
            cursor: pointer; border: none; transition: background 0.2s; display: flex; align-items: center; gap: 6px;
        }}
        .btn-pdf {{ background: var(--artimo-rojo-oscuro); color: white; }}
        .btn-pdf:hover {{ background: #9a1414; }}
        .btn-csv {{ background: #10B981; color: white; }}
        .btn-csv:hover {{ background: #059669; }}

        .main-content {{ max-width: 1400px; margin: 0 auto; padding: 24px; }}
        
        .alert-box {{ background: rgba(90,90,89,0.1); border-left: 4px solid var(--artimo-gris); padding: 12px 20px; border-radius: 8px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: center; }}
        .alert-box p {{ margin: 0; font-size: 13px; font-weight: 600; }}
        .active-tags {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }}
        .tag {{ background: var(--artimo-gris-claro); color: var(--artimo-negro); font-size: 11px; font-weight: 600; padding: 4px 10px; border-radius: 12px; border: 1px solid #E5E7EB; display: flex; align-items: center; gap: 6px; }}
        .tag button {{ background: none; border: none; color: var(--artimo-rojo-oscuro); font-weight: bold; cursor: pointer; }}
        .btn-clear {{ background: rgba(188,24,24,0.15); color: var(--artimo-rojo-oscuro); border: 1px solid rgba(188,24,24,0.3); font-size: 11px; font-weight: 600; padding: 4px 10px; border-radius: 12px; cursor: pointer; }}

        .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }}
        .kpi-card {{ background: var(--artimo-blanco); border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border: 1px solid #E5E7EB; display: flex; flex-direction: column; gap: 6px; }}
        .kpi-card.prio-1 {{ border-top: 3px solid var(--artimo-rojo-oscuro); }}
        .kpi-label {{ font-size: 11px; color: var(--artimo-gris); text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }}
        .kpi-value {{ font-size: 38px; font-weight: 700; line-height: 1; }}
        .kpi-sub {{ font-size: 11px; color: var(--artimo-gris); font-weight: 300; }}
        .kpi-p1 .kpi-value {{ color: var(--artimo-rojo-oscuro); }}
        .kpi-ok .kpi-value {{ color: #10B981; }}
        .kpi-dark .kpi-value {{ color: var(--artimo-negro); }}

        .card-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin-bottom: 24px; }}
        .card {{ background: var(--artimo-blanco); border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border: 1px solid #E5E7EB; transition: transform 0.15s, box-shadow 0.15s; }}

        .table-section {{ background: var(--artimo-blanco); border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border: 1px solid #E5E7EB; overflow: hidden; }}
        .table-header {{ padding: 20px; border-bottom: 1px solid #E5E7EB; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; }}
        .table-header h2 {{ margin: 0; font-size: 18px; font-weight: 700; }}
        .header-actions {{ display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }}
        .search-input {{ padding: 8px 12px; border: 1.5px solid #E5E7EB; border-radius: 8px; font-size: 13px; font-family: 'Open Sans'; outline: none; width: 200px; }}
        .search-input:focus {{ border-color: var(--artimo-rojo-oscuro); }}

        .fc-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        .fc-table th {{ background: #F9FAFB; padding: 12px 20px; font-size: 11px; text-transform: uppercase; letter-spacing: 0.4px; color: var(--artimo-gris); font-weight: 600; text-align: left; }}
        .fc-table td {{ padding: 12px 20px; border-bottom: 1px solid #F3F4F6; font-weight: 300; }}
        .fc-table tr:hover td {{ background: #FAFAFA; }}

        .badge-ok {{ background: rgba(16,185,129,0.2); color: #10B981; border: 1px solid rgba(16,185,129,0.3); padding: 2px 9px; border-radius: 12px; font-size: 11px; font-weight: 600; }}
        .badge-p1 {{ background: rgba(188,24,24,0.15); color: var(--artimo-rojo-oscuro); border: 1px solid rgba(188,24,24,0.3); padding: 2px 9px; border-radius: 12px; font-size: 11px; font-weight: 600; }}
        .badge-p2 {{ background: rgba(245,158,11,0.12); color: #F59E0B; border: 1px solid rgba(245,158,11,0.3); padding: 2px 9px; border-radius: 12px; font-size: 11px; font-weight: 600; }}
        .badge-mid {{ background: rgba(90,90,89,0.1); color: var(--artimo-gris); border: 1px solid rgba(90,90,89,0.2); padding: 2px 9px; border-radius: 12px; font-size: 11px; font-weight: 600; }}
        .font-bold {{ font-weight: 700; color: var(--artimo-negro); }}
        .text-sub {{ color: var(--artimo-gris); }}
    </style>
</head>
<body>

    <div class="topbar">
        <div class="topbar-brand">
            <!-- FIX: Controlamos el ancho de la imagen para que no explote si no carga -->
            <img src="artimo_logo.jpg" alt="Logo Ártimo" style="height:32px; min-width:80px;" onerror="this.onerror=null; this.src='https://via.placeholder.com/120x40/BC1818/FFFFFF?text=ARTIMO';"/>
            <div class="topbar-title-container">
                <p class="topbar-title" title="{nombre_dealer} Dashboard">{nombre_dealer} Dashboard</p>
                <p class="topbar-sub">Ártimo Telematics · Actualizado: {fecha_actualizacion}</p>
            </div>
        </div>
        <div class="topbar-right">
            <button onclick="exportToPDF()" class="btn-action btn-pdf">📄 PDF Dashboard</button>
            <select id="client_select" class="filter-select" onchange="filterByClient(this.value)">
                <option value="TODOS">-- TODOS LOS CLIENTES --</option>
            </select>
        </div>
    </div>

    <div class="main-content" id="report_area">
        <div class="alert-box" data-html2canvas-ignore="true"> <!-- Ignorar en PDF -->
            <div>
                <p>Filtros de Dashboard Interactivo</p>
                <div id="active_filters" class="active-tags">
                    <span class="text-sub" style="font-size:12px; font-weight:300;">Haz clic en las gráficas para filtrar la información.</span>
                </div>
            </div>
        </div>

        <div class="kpi-grid">
            <div class="kpi-card kpi-dark prio-4">
                <div class="kpi-label">Total Generadores</div>
                <div id="kpi_total" class="kpi-value">0</div>
                <div class="kpi-sub">Unidades registradas</div>
            </div>
            <div class="kpi-card kpi-ok">
                <div class="kpi-label">Conectividad Global</div>
                <div id="kpi_online" class="kpi-value">0%</div>
                <div class="kpi-sub">Operando correctamente</div>
            </div>
            <div class="kpi-card kpi-p1 prio-1">
                <div class="kpi-label">Equipos Offline</div>
                <div id="kpi_offline" class="kpi-value">0</div>
                <div class="kpi-sub">Unidades fuera de cobertura</div>
            </div>
        </div>

        <div class="card-grid">
            <div class="card"><div id="chart_dona" style="width:100%;"></div></div>
            <div class="card"><div id="chart_tech" style="width:100%;"></div></div>
            <div class="card"><div id="chart_gravity" style="width:100%;"></div></div>
            <div class="card"><div id="chart_top_clients" style="width:100%;"></div></div>
        </div>

        <div class="table-section">
            <div class="table-header">
                <div>
                    <h2 id="table_title">Detalle General de Equipos</h2>
                    <span class="text-sub" style="font-size: 12px;">Mostrando todos los equipos según los filtros seleccionados.</span>
                </div>
                <div class="header-actions" data-html2canvas-ignore="true">
                    <input type="text" id="table_search" class="search-input" placeholder="Buscar generador..." oninput="onSearchTable(this.value)">
                    <button onclick="exportToCSV()" class="btn-action btn-csv">📥 Exportar CSV</button>
                </div>
            </div>
            <div style="overflow-x: auto;">
                <table class="fc-table">
                    <thead>
                        <tr>
                            <th>Generador</th>
                            <th>Cliente</th>
                            <th>Tecnología</th>
                            <th>Estado</th>
                            <th>Última Conexión</th>
                            <th>Severidad</th>
                        </tr>
                    </thead>
                    <tbody id="table_body"></tbody>
                </table>
            </div>
            <div id="no_data_message" style="display:none; padding: 40px; text-align: center; color: var(--artimo-gris); font-size: 14px;">
                No se encontraron registros bajo los filtros actuales.
            </div>
        </div>
    </div>

    <script>
        const rawData = {data_json};
        let currentFilters = {{ cliente: 'TODOS', estado: null, tecnologia: null, gravedad: null }};
        let searchTerm = '';

        const plotlyLayoutBase = {{
            font: {{ family: 'Open Sans, Arial, sans-serif', color: '#1A1A1A' }},
            paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)',
            margin: {{ t: 40, b: 30, l: 40, r: 20 }}, height: 280
        }};

        window.addEventListener('DOMContentLoaded', () => {{
            populateClientDropdown();
            updateDashboard();
        }});

        function populateClientDropdown() {{
            const select = document.getElementById('client_select');
            const uniqueClients = [...new Set(rawData.map(d => d.cliente))].sort();
            uniqueClients.forEach(c => {{
                const opt = document.createElement('option');
                opt.value = opt.textContent = c;
                select.appendChild(opt);
            }});
        }}

        function filterByClient(val) {{ currentFilters.cliente = val; updateDashboard(); }}
        function clearFilter(key) {{
            if(key === 'cliente') document.getElementById('client_select').value = 'TODOS';
            currentFilters[key] = (key === 'cliente') ? 'TODOS' : null;
            updateDashboard();
        }}
        function clearAllFilters() {{
            currentFilters = {{ cliente: 'TODOS', estado: null, tecnologia: null, gravedad: null }};
            document.getElementById('client_select').value = 'TODOS';
            updateDashboard();
        }}
        function onSearchTable(val) {{ searchTerm = val.toLowerCase().trim(); renderTableOnly(); }}

        function getFilteredData() {{
            return rawData.filter(d => 
                (currentFilters.cliente === 'TODOS' || d.cliente === currentFilters.cliente) &&
                (!currentFilters.estado || d.estado === currentFilters.estado) &&
                (!currentFilters.tecnologia || d.tecnologia === currentFilters.tecnologia) &&
                (!currentFilters.gravedad || d.gravedad === currentFilters.gravedad)
            );
        }}

        function updateDashboard() {{
            const filteredData = getFilteredData();

            const total = filteredData.length;
            const online = filteredData.filter(d => d.estado === 'Operando').length;
            document.getElementById('kpi_total').textContent = total;
            document.getElementById('kpi_online').textContent = total > 0 ? Math.round((online/total)*100) + '%' : '0%';
            document.getElementById('kpi_offline').textContent = total - online;

            const tableTitle = document.getElementById('table_title');
            if(currentFilters.estado === 'Operando') tableTitle.textContent = "Equipos en Línea";
            else if (currentFilters.estado === 'Fuera de cobertura' || currentFilters.gravedad) tableTitle.textContent = "Equipos Críticos";
            else tableTitle.textContent = "Detalle General de Equipos";

            renderActiveFilterTags();
            renderDonaChart(filteredData);
            renderTechChart(filteredData);
            renderGravityChart(filteredData);
            renderTopClientsChart(filteredData);
            renderTableOnly(filteredData);
        }}

        function renderActiveFilterTags() {{
            const container = document.getElementById('active_filters');
            container.innerHTML = '';
            let has = false;
            Object.keys(currentFilters).forEach(key => {{
                if(currentFilters[key] && currentFilters[key] !== 'TODOS') {{
                    has = true;
                    container.innerHTML += `<div class="tag">${{key.toUpperCase()}}: ${{currentFilters[key]}} <button onclick="clearFilter('${{key}}')">×</button></div>`;
                }}
            }});
            if(has) container.innerHTML += `<button class="btn-clear" onclick="clearAllFilters()">Limpiar Filtros</button>`;
            else container.innerHTML = `<span class="text-sub" style="font-size:12px; font-weight:300;">Haz clic en las gráficas para filtrar.</span>`;
        }}

        function renderDonaChart(data) {{
            const op = data.filter(d => d.estado === 'Operando').length;
            const off = data.filter(d => d.estado === 'Fuera de cobertura').length;
            const layout = {{ ...plotlyLayoutBase, title: {{ text: '<b>Estado General</b>', font: {{size: 15}} }}, legend: {{ orientation: 'h', y: -0.1 }} }};
            Plotly.react('chart_dona', [{{ values: [op, off], labels: ['Operando', 'Fuera de cobertura'], type: 'pie', hole: 0.5, marker: {{ colors: ['#10B981', '#BC1818'] }}, textinfo: 'value+percent' }}], layout, {{ responsive: true, displayModeBar: false }});
            document.getElementById('chart_dona').on('plotly_click', d => {{ currentFilters.estado = (currentFilters.estado === d.points[0].label) ? null : d.points[0].label; updateDashboard(); }});
        }}

        function renderTechChart(data) {{
            const map = {{}};
            data.forEach(d => {{
                if(!map[d.tecnologia]) map[d.tecnologia] = {{ op: 0, off: 0 }};
                d.estado === 'Operando' ? map[d.tecnologia].op++ : map[d.tecnologia].off++;
            }});
            const x = Object.keys(map).sort();
            const layout = {{ ...plotlyLayoutBase, title: {{ text: '<b>Tecnología</b>', font: {{size: 15}} }}, barmode: 'group', legend: {{ orientation: 'h', y: -0.2 }} }};
            Plotly.react('chart_tech', [ {{ x: x, y: x.map(k=>map[k].op), name: 'Operando', type: 'bar', marker: {{ color: '#10B981' }} }}, {{ x: x, y: x.map(k=>map[k].off), name: 'Offline', type: 'bar', marker: {{ color: '#BC1818' }} }} ], layout, {{ responsive: true, displayModeBar: false }});
            document.getElementById('chart_tech').on('plotly_click', d => {{ currentFilters.tecnologia = (currentFilters.tecnologia === d.points[0].x) ? null : d.points[0].x; updateDashboard(); }});
        }}

        function renderGravityChart(data) {{
            const map = {{ "1 a 3 días": 0, "4 a 7 días": 0, "Más de 7 días": 0, "Sin registro previo": 0 }};
            data.filter(d => d.estado !== 'Operando').forEach(d => {{ if(map[d.gravedad] !== undefined) map[d.gravedad]++; }});
            const x = Object.keys(map);
            const layout = {{ ...plotlyLayoutBase, title: {{ text: '<b>Gravedad (Offline)</b>', font: {{size: 15}} }} }};
            Plotly.react('chart_gravity', [{{ x: x, y: x.map(k=>map[k]), type: 'bar', marker: {{ color: ['#E63B1E', '#E42520', '#BC1818', '#5A5A59'] }} }}], layout, {{ responsive: true, displayModeBar: false }});
            document.getElementById('chart_gravity').on('plotly_click', d => {{ currentFilters.gravedad = (currentFilters.gravedad === d.points[0].x) ? null : d.points[0].x; updateDashboard(); }});
        }}

        function renderTopClientsChart(data) {{
            const map = {{}};
            data.filter(d => d.estado !== 'Operando').forEach(d => map[d.cliente] = (map[d.cliente]||0) + 1);
            const sorted = Object.entries(map).sort((a,b)=>b[1]-a[1]).slice(0,10).reverse();
            
            // FIX: Automargin en el eje Y para que los nombres largos no se recorten
            const layout = {{ 
                ...plotlyLayoutBase, 
                title: {{ text: '<b>Top 10 Clientes Críticos</b>', font: {{size: 15}} }}, 
                margin: {{ t:40, b:30, l:20, r:20 }},
                yaxis: {{ automargin: true }} 
            }};
            
            Plotly.react('chart_top_clients', [{{ y: sorted.map(i=>i[0]), x: sorted.map(i=>i[1]), type: 'bar', orientation: 'h', marker: {{ color: '#BC1818' }} }}], layout, {{ responsive: true, displayModeBar: false }});
            document.getElementById('chart_top_clients').on('plotly_click', d => {{
                currentFilters.cliente = (currentFilters.cliente === d.points[0].y) ? 'TODOS' : d.points[0].y;
                document.getElementById('client_select').value = currentFilters.cliente; updateDashboard();
            }});
        }}

        function renderTableOnly(dataToRender) {{
            const data = dataToRender || getFilteredData();
            const tbody = document.getElementById('table_body');
            const msg = document.getElementById('no_data_message');
            
            let finalData = data.filter(d => d.generador.toLowerCase().includes(searchTerm));
            finalData.sort((a, b) => b.dias_offline - a.dias_offline);
            
            if(finalData.length === 0) {{ tbody.innerHTML = ''; msg.style.display = 'block'; return; }}
            msg.style.display = 'none';

            let tableHTML = '';
            finalData.forEach(r => {{
                const statusBadge = r.estado === 'Operando' ? '<span class="badge-ok">Operando</span>' : '<span class="badge-p1">Offline</span>';
                let gravBadge = '<span class="badge-ok">Estable</span>';
                if(r.estado !== 'Operando') {{
                    if(r.gravedad === '1 a 3 días') gravBadge = '<span class="badge-p2">1 a 3 días</span>';
                    else if(r.gravedad === 'Más de 7 días') gravBadge = '<span class="badge-p1">Más de 7 días</span>';
                    else gravBadge = `<span class="badge-mid">${{r.gravedad}}</span>`;
                }}
                
                tableHTML += `<tr><td class="font-bold">${{r.generador}}</td><td class="text-sub">${{r.cliente}}</td><td class="text-sub">${{r.tecnologia}}</td><td>${{statusBadge}}</td><td class="text-sub">${{r.fecha}}</td><td>${{gravBadge}}</td></tr>`;
            }});
            tbody.innerHTML = tableHTML;
        }}

        // --- FUNCIONES DE EXPORTACIÓN ---
        
        function exportToCSV() {{
            const dataToExport = getFilteredData().filter(d => d.generador.toLowerCase().includes(searchTerm));
            if (dataToExport.length === 0) return alert("No hay datos para exportar.");

            const headers = ["Generador", "Cliente", "Tecnologia", "Estado", "Ultima_Conexion", "Severidad", "Dias_Desconectado"];
            const csvRows = [headers.join(',')];

            dataToExport.forEach(r => {{
                // Protegemos strings con comas envolviéndolos en comillas dobles
                const values = [ `"${{r.generador}}"`, `"${{r.cliente}}"`, `"${{r.tecnologia}}"`, `"${{r.estado}}"`, `"${{r.fecha}}"`, `"${{r.gravedad}}"`, r.dias_offline ];
                csvRows.push(values.join(','));
            }});

            const blob = new Blob(["\\uFEFF" + csvRows.join('\\n')], {{ type: 'text/csv;charset=utf-8;' }}); // \\uFEFF for Excel UTF-8
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.setAttribute('href', url);
            a.setAttribute('download', `Artimo_Equipos_${{new Date().getTime()}}.csv`);
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        }}

        function exportToPDF() {{
            const element = document.getElementById('report_area');
            const opt = {{
                margin:       0.3,
                filename:     `Reporte_Artimo_${{new Date().getTime()}}.pdf`,
                image:        {{ type: 'jpeg', quality: 0.98 }},
                html2canvas:  {{ scale: 2, useCORS: true }},
                jsPDF:        {{ unit: 'in', format: 'a4', orientation: 'landscape' }}
            }};
            
            // html2pdf procesará el div 'report_area' (ignora los botones gracias a data-html2canvas-ignore)
            html2pdf().set(opt).from(element).save();
        }}
    </script>
</body>
</html>"""

    html_final = dashboard_html.replace('{data_json}', data_json)
    with open('dashboard_conectividad.html', 'w', encoding='utf-8') as f:
        f.write(html_final)
    print("Dashboard actualizado con exportación PDF/CSV y UX mejorada.")

if __name__ == "__main__":
    generar_dashboard()
