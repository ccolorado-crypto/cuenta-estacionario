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

    # MAPEO EXACTO DE COLUMNAS (A=0, B=1, C=2, D=3, F=5, R=17)
    col_dealer = df.columns[1]      # Columna B: Dealer
    col_cliente = df.columns[2]     # Columna C: Cliente
    col_generador = df.columns[3]   # Columna D: Nombre del generador
    col_tecnologia = df.columns[5]  # Columna F: Tecnología
    col_fecha = df.columns[17]      # Columna R: Fecha de conexión

    # Extraer el nombre del Dealer
    nombre_dealer = str(df[col_dealer].dropna().iloc[0]) if not df[col_dealer].dropna().empty else "Dealer Principal"

    # Preparar registros para JSON
    df[col_fecha] = pd.to_datetime(df[col_fecha], errors='coerce').dt.date
    fecha_hoy = date.today()
    
    records = []
    for idx, row in df.iterrows():
        # Limpieza de datos básicos
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

    # Convertir a formato JSON seguro para inyectar en JS
    data_json = json.dumps(records, ensure_ascii=False)
    
    # Hora de actualización ajustada a Colombia (UTC-5)
    colombia_time = datetime.utcnow() - timedelta(hours=5)
    fecha_actualizacion = colombia_time.strftime("%d/%m/%Y a las %H:%M (Hora Col)")

    # ---------------- PLANTILLA HTML MULTI-INTERACTIVA ----------------
    dashboard_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Centro de Control - {nombre_dealer}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
</head>
<body class="bg-gray-100 text-gray-800 font-sans min-h-screen pb-12">

    <header class="bg-slate-800 text-white shadow-md py-6 px-8 mb-6">
        <div class="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
            <div>
                <h1 class="text-2xl md:text-3xl font-bold tracking-tight">📊 Centro de Control - {nombre_dealer}</h1>
                <p class="text-xs md:text-sm text-gray-400 mt-1">Actualizado automáticamente el: {fecha_actualizacion}</p>
            </div>
            <div class="flex items-center gap-2 bg-slate-700 p-2 rounded-lg">
                <label for="client_select" class="text-sm font-semibold text-gray-300">Cliente:</label>
                <select id="client_select" class="bg-slate-800 text-white rounded border border-slate-600 px-3 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500" onchange="filterByClient(this.value)">
                    <option value="TODOS">-- TODOS LOS CLIENTES --</option>
                </select>
            </div>
        </div>
    </header>

    <div class="max-w-7xl mx-auto px-4 md:px-8">

        <div class="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-r-lg mb-6 shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
                <p class="text-sm text-blue-800 font-medium">💡 ¡Dashboard 100% Interactivo!</p>
                <p class="text-xs text-blue-600 mt-0.5">Haz clic en las secciones o barras de cualquier gráfico para filtrar el resto del panel y la tabla de equipos.</p>
            </div>
            <div id="active_filters" class="flex flex-wrap gap-2 items-center">
                </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-8">
            <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200 text-center">
                <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-wider">Total Generadores</h3>
                <p id="kpi_total" class="text-4xl font-extrabold text-slate-800 mt-2">0</p>
            </div>
            <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200 text-center">
                <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-wider">En línea (Operando)</h3>
                <p id="kpi_online" class="text-4xl font-extrabold text-green-600 mt-2">0%</p>
            </div>
            <div class="bg-white p-6 rounded-xl shadow-sm border border-gray-200 text-center">
                <h3 class="text-sm font-semibold text-gray-500 uppercase tracking-wider">Fuera de Cobertura</h3>
                <p id="kpi_offline" class="text-4xl font-extrabold text-red-600 mt-2">0</p>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
                <div id="chart_dona" class="w-full"></div>
            </div>
            <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
                <div id="chart_tech" class="w-full"></div>
            </div>
            <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
                <div id="chart_gravity" class="w-full"></div>
            </div>
            <div class="bg-white p-4 rounded-xl shadow-sm border border-gray-200">
                <div id="chart_top_clients" class="w-full"></div>
            </div>
        </div>

        <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div class="p-6 border-b border-gray-200 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h2 class="text-lg font-bold text-slate-800">📋 Listado de Equipos bajo Filtro Activo</h2>
                    <p class="text-xs text-gray-500 mt-0.5">Mostrando los registros que coinciden con los criterios de selección actuales.</p>
                </div>
                <div class="w-full sm:w-auto">
                    <input type="text" id="table_search" placeholder="Buscar por generador..." oninput="onSearchTable(this.value)" class="w-full bg-gray-50 border border-gray-300 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>
            </div>
            
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="bg-gray-50 text-slate-700 text-xs font-bold uppercase tracking-wider border-b border-gray-200">
                            <th class="px-6 py-4">Generador</th>
                            <th class="px-6 py-4">Cliente</th>
                            <th class="px-6 py-4">Tecnología</th>
                            <th class="px-6 py-4 text-center">Estado</th>
                            <th class="px-6 py-4">Última Conexión</th>
                            <th class="px-6 py-4">Detalle Cobertura</th>
                        </tr>
                    </thead>
                    <tbody id="table_body" class="divide-y divide-gray-100 text-sm">
                        </tbody>
                </table>
            </div>
            <div id="no_data_message" class="hidden p-8 text-center text-gray-500 font-medium">
                No se encontraron equipos bajo los criterios seleccionados.
            </div>
        </div>
    </div>

    <script>
        // Los datos JSON de Python inyectados
        const rawData = {data_json};

        // Estado inicial de filtros
        let currentFilters = {{
            cliente: 'TODOS',
            estado: null,
            tecnologia: null,
            gravedad: null
        }};

        let searchTerm = '';

        // Inicializar Dashboard
        window.addEventListener('DOMContentLoaded', () => {{
            populateClientDropdown();
            updateDashboard();
        }});

        // Llenar el Dropdown de Clientes dinámicamente
        function populateClientDropdown() {{
            const select = document.getElementById('client_select');
            const uniqueClients = [...new Set(rawData.map(d => d.cliente))].sort();
            uniqueClients.forEach(client => {{
                const opt = document.createElement('option');
                opt.value = client;
                opt.textContent = client;
                select.appendChild(opt);
            }});
        }}

        // Cambiar filtro por dropdown de cliente
        function filterByClient(clientValue) {{
            currentFilters.cliente = clientValue;
            updateDashboard();
        }}

        // Limpiar un filtro individual
        function clearFilter(filterKey) {{
            if (filterKey === 'cliente') {{
                currentFilters.cliente = 'TODOS';
                document.getElementById('client_select').value = 'TODOS';
            }} else {{
                currentFilters[filterKey] = null;
            }}
            updateDashboard();
        }}

        // Limpiar todos los filtros activos
        function clearAllFilters() {{
            currentFilters.cliente = 'TODOS';
            currentFilters.estado = null;
            currentFilters.tecnologia = null;
            currentFilters.gravedad = null;
            document.getElementById('client_select').value = 'TODOS';
            updateDashboard();
        }}

        // Buscar en la tabla en tiempo real
        function onSearchTable(val) {{
            searchTerm = val.toLowerCase().trim();
            renderTableOnly();
        }}

        // Función Principal de Actualización del Dashboard
        function updateDashboard() {{
            // 1. Filtrar los datos maestros
            const filteredData = rawData.filter(d => {{
                const matchCliente = (currentFilters.cliente === 'TODOS' || d.cliente === currentFilters.cliente);
                const matchEstado = (!currentFilters.estado || d.estado === currentFilters.estado);
                const matchTech = (!currentFilters.tecnologia || d.tecnologia === currentFilters.tecnologia);
                const matchGrav = (!currentFilters.gravedad || d.gravedad === currentFilters.gravedad);
                return matchCliente && matchEstado && matchTech && matchGrav;
            }});

            // 2. Actualizar KPIs
            const total = filteredData.length;
            const online = filteredData.filter(d => d.estado === 'Operando').length;
            const offline = total - online;
            const percentage = total > 0 ? Math.round((online / total) * 100) : 0;

            document.getElementById('kpi_total').textContent = total;
            document.getElementById('kpi_online').textContent = percentage + '%';
            document.getElementById('kpi_offline').textContent = offline;

            // 3. Renderizar Filtros Activos (Tags)
            renderActiveFilterTags();

            // 4. Renderizar Gráficas
            renderDonaChart(filteredData);
            renderTechChart(filteredData);
            renderGravityChart(filteredData);
            renderTopClientsChart(filteredData);

            // 5. Renderizar Tabla
            renderTableOnly(filteredData);
        }}

        // Renderizar tags de filtros aplicados
        function renderActiveFilterTags() {{
            const container = document.getElementById('active_filters');
            container.innerHTML = '';

            let hasFilters = false;

            if (currentFilters.cliente !== 'TODOS') {{
                createTag(container, `Cliente: ${{currentFilters.cliente}}`, 'cliente');
                hasFilters = true;
            }}
            if (currentFilters.estado) {{
                createTag(container, `Estado: ${{currentFilters.estado}}`, 'estado');
                hasFilters = true;
            }}
            if (currentFilters.tecnologia) {{
                createTag(container, `Tecnología: ${{currentFilters.tecnologia}}`, 'tecnologia');
                hasFilters = true;
            }}
            if (currentFilters.gravedad) {{
                createTag(container, `Gravedad: ${{currentFilters.gravedad}}`, 'gravedad');
                hasFilters = true;
            }}

            if (hasFilters) {{
                const clearBtn = document.createElement('button');
                clearBtn.className = "bg-red-100 hover:bg-red-200 text-red-700 text-xs font-bold px-3 py-1 rounded-lg transition";
                clearBtn.textContent = "Limpiar Filtros ❌";
                clearBtn.onclick = clearAllFilters;
                container.appendChild(clearBtn);
            }} else {{
                container.innerHTML = '<span class="text-xs text-blue-500 italic">Ningún gráfico seleccionado. Panel completo.</span>';
            }}
        }}

        function createTag(parent, text, filterKey) {{
            const tag = document.createElement('span');
            tag.className = "bg-blue-100 text-blue-800 text-xs font-semibold px-2.5 py-1 rounded flex items-center gap-1.5 border border-blue-200";
            tag.innerHTML = `${{text}} <button class="text-blue-500 hover:text-blue-900 font-bold" onclick="clearFilter('${{filterKey}}')">×</button>`;
            parent.appendChild(tag);
        }}

        // --- RENDERIZADO DE GRÁFICOS INTERACTIVOS ---

        // 1. Gráfico de Dona: Conectividad General
        function renderDonaChart(data) {{
            const operando = data.filter(d => d.estado === 'Operando').length;
            const offline = data.filter(d => d.estado === 'Fuera de cobertura').length;

            const plotData = [{{
                values: [operando, offline],
                labels: ['Operando', 'Fuera de cobertura'],
                type: 'pie',
                hole: 0.4,
                marker: {{ colors: ['#10B981', '#EF4444'] }},
                textinfo: 'value+percent'
            }}];

            const layout = {{
                title: {{ text: '<b>Estado General de la Flota</b>', font: {{ size: 15 }} }},
                margin: {{ t: 40, b: 20, l: 20, r: 20 }},
                height: 280,
                showlegend: true,
                legend: {{ orientation: 'h', y: -0.1 }}
            }};

            Plotly.react('chart_dona', plotData, layout, {{ responsive: true, displayModeBar: false }});

            // Acción al hacer click
            document.getElementById('chart_dona').on('plotly_click', function(clickData) {{
                const label = clickData.points[0].label;
                currentFilters.estado = (currentFilters.estado === label) ? null : label;
                updateDashboard();
            }});
        }}

        // 2. Gráfico de Barras: Tecnología
        function renderTechChart(data) {{
            const techMap = {{}};
            data.forEach(d => {{
                if (!techMap[d.tecnologia]) techMap[d.tecnologia] = {{ operando: 0, offline: 0 }};
                if (d.estado === 'Operando') techMap[d.tecnologia].operando++;
                else techMap[d.tecnologia].offline++;
            }});

            const xKeys = Object.keys(techMap).sort();
            const yOperando = xKeys.map(k => techMap[k].operando);
            const yOffline = xKeys.map(k => techMap[k].offline);

            const trace1 = {{
                x: xKeys,
                y: yOperando,
                name: 'Operando',
                type: 'bar',
                marker: {{ color: '#10B981' }}
            }};

            const trace2 = {{
                x: xKeys,
                y: yOffline,
                name: 'Fuera cobertura',
                type: 'bar',
                marker: {{ color: '#EF4444' }}
            }};

            const layout = {{
                title: {{ text: '<b>Conectividad por Tecnología</b>', font: {{ size: 15 }} }},
                barmode: 'group',
                margin: {{ t: 40, b: 40, l: 40, r: 20 }},
                height: 280,
                legend: {{ orientation: 'h', y: -0.25 }}
            }};

            Plotly.react('chart_tech', [trace1, trace2], layout, {{ responsive: true, displayModeBar: false }});

            document.getElementById('chart_tech').on('plotly_click', function(clickData) {{
                const tech = clickData.points[0].x;
                currentFilters.tecnologia = (currentFilters.tecnologia === tech) ? null : tech;
                updateDashboard();
            }});
        }}

        // 3. Gráfico de Barras: Gravedad de Desconexión
        function renderGravityChart(data) {{
            const gravData = data.filter(d => d.estado === 'Fuera de cobertura');
            const counts = {{
                "1 a 3 días": 0,
                "4 a 7 días": 0,
                "Más de 7 días": 0,
                "Sin registro previo": 0
            }};

            gravData.forEach(d => {{
                if (counts[d.gravedad] !== undefined) counts[d.gravedad]++;
            }});

            const xKeys = Object.keys(counts);
            const yValues = xKeys.map(k => counts[k]);

            const plotData = [{{
                x: xKeys,
                y: yValues,
                type: 'bar',
                marker: {{ color: ['#FDBA74', '#F97316', '#C2410C', '#9CA3AF'] }}
            }}];

            const layout = {{
                title: {{ text: '<b>Gravedad de la Desconexión (Offline)</b>', font: {{ size: 15 }} }},
                margin: {{ t: 40, b: 40, l: 40, r: 20 }},
                height: 280
            }};

            Plotly.react('chart_gravity', plotData, layout, {{ responsive: true, displayModeBar: false }});

            document.getElementById('chart_gravity').on('plotly_click', function(clickData) {{
                const grav = clickData.points[0].x;
                currentFilters.gravedad = (currentFilters.gravedad === grav) ? null : grav;
                updateDashboard();
            }});
        }}

        // 4. Gráfico: Top 10 Clientes Críticos (Reemplazo del gráfico complejo anterior)
        function renderTopClientsChart(data) {{
            const offlineData = data.filter(d => d.estado === 'Fuera de cobertura');
            const clientCounts = {{}};
            offlineData.forEach(d => {{
                clientCounts[d.cliente] = (clientCounts[d.cliente] || 0) + 1;
            }});

            // Ordenar clientes descendente y tomar top 10
            const sortedClients = Object.entries(clientCounts)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 10)
                .reverse(); // Reverso para que la barra más larga quede arriba en vertical/horizontal

            const yClients = sortedClients.map(item => item[0]);
            const xCounts = sortedClients.map(item => item[1]);

            const plotData = [{{
                y: yClients,
                x: xCounts,
                type: 'bar',
                orientation: 'h',
                marker: {{ color: '#EF4444' }}
            }}];

            const layout = {{
                title: {{ text: '<b>Top 10 Clientes con más Equipos Offline</b>', font: {{ size: 15 }} }},
                margin: {{ t: 40, b: 40, l: 150, r: 20 }},
                height: 280,
                xaxis: {{ dtick: 1 }}
            }};

            Plotly.react('chart_top_clients', plotData, layout, {{ responsive: true, displayModeBar: false }});

            document.getElementById('chart_top_clients').on('plotly_click', function(clickData) {{
                const clientName = clickData.points[0].y;
                currentFilters.cliente = (currentFilters.cliente === clientName) ? 'TODOS' : clientName;
                document.getElementById('client_select').value = currentFilters.cliente;
                updateDashboard();
            }});
        }}

        // --- RENDERIZADO DE TABLA ---
        function renderTableOnly(dataToRender) {{
            // Si no se pasa data, filtramos con el estado actual
            const data = dataToRender || rawData.filter(d => {{
                const matchCliente = (currentFilters.cliente === 'TODOS' || d.cliente === currentFilters.cliente);
                const matchEstado = (!currentFilters.estado || d.estado === currentFilters.estado);
                const matchTech = (!currentFilters.tecnologia || d.tecnologia === currentFilters.tecnologia);
                const matchGrav = (!currentFilters.gravedad || d.gravedad === currentFilters.gravedad);
                return matchCliente && matchEstado && matchTech && matchGrav;
            }});

            const tbody = document.getElementById('table_body');
            const msg = document.getElementById('no_data_message');
            tbody.innerHTML = '';

            // Filtrar localmente con el término de búsqueda
            const finalData = data.filter(d => d.generador.toLowerCase().includes(searchTerm));

            if (finalData.length === 0) {{
                msg.classList.remove('hidden');
                return;
            }} else {{
                msg.classList.add('hidden');
            }}

            finalData.forEach(row => {{
                const tr = document.createElement('tr');
                tr.className = "hover:bg-slate-50 transition";

                // Badge de Estado
                const statusBadge = row.estado === 'Operando' 
                    ? '<span class="bg-green-100 text-green-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-green-200">Operando</span>'
                    : '<span class="bg-red-100 text-red-800 text-xs font-semibold px-2.5 py-0.5 rounded-full border border-red-200">Offline</span>';

                // Badge de gravedad
                let gravBadge = '';
                if (row.estado === 'Operando') {{
                    gravBadge = '<span class="text-green-600 font-medium">Estable</span>';
                }} else {{
                    const colors = {{
                        "1 a 3 días": "text-amber-600 bg-amber-50 px-2 py-0.5 rounded font-medium",
                        "4 a 7 días": "text-orange-600 bg-orange-50 px-2 py-0.5 rounded font-medium",
                        "Más de 7 días": "text-red-700 bg-red-50 px-2 py-0.5 rounded font-bold",
                        "Sin registro previo": "text-gray-500 bg-gray-50 px-2 py-0.5 rounded"
                    }};
                    gravBadge = `<span class="${{colors[row.gravedad] || 'text-gray-500'}}">${{row.gravedad}}</span>`;
                }}

                tr.innerHTML = `
                    <td class="px-6 py-4 font-bold text-slate-800">${{row.generador}}</td>
                    <td class="px-6 py-4 text-slate-600 font-medium">${{row.cliente}}</td>
                    <td class="px-6 py-4 text-gray-500">${{row.tecnologia}}</td>
                    <td class="px-6 py-4 text-center">${{statusBadge}}</td>
                    <td class="px-6 py-4 text-gray-500">${{row.fecha}}</td>
                    <td class="px-6 py-4 text-xs">${{gravBadge}}</td>
                `;
                tbody.appendChild(tr);
            }});
        }}
    </script>
</body>
</html>"""

    # Inyectar el JSON y guardar el archivo final
    html_final = dashboard_html.replace('{data_json}', data_json)
    
    with open('dashboard_conectividad.html', 'w', encoding='utf-8') as f:
        f.write(html_final)
        
    print("¡Proceso completado! Nuevo Dashboard Interactivo generado.")

if __name__ == "__main__":
    generar_dashboard()
