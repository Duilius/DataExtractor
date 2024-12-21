from fastapi.responses import HTMLResponse
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case, desc
from database import SessionLocal
from scripts.sql_alc.create_tables_BD_INVENTARIO import ProcesoInventario, Oficina, Empleado, Bien, Sede
import json

gerencial_router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@gerencial_router.get("/metricas-gerenciales", response_class=HTMLResponse)
async def get_metricas_gerenciales(db: Session = Depends(get_db)):
    try:
        total_bienes = db.query(func.sum(Sede.cantidad_bienes)).scalar() or 0
        bienes_registrados = db.query(func.count(Bien.id)).scalar() or 0
        avance_global = round((bienes_registrados / total_bienes * 100) if total_bienes else 0, 1)
        
        return f"""
        <div class="metric-card highlight">
            <div class="metric-value">{avance_global}%</div>
            <div class="metric-label">Avance Global</div>
            <div class="metric-trend">
                <span class="trend-up">↑</span>
                2.5% vs ayer
            </div>
        </div>
        """
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@gerencial_router.get("/chart-avance-sedes", response_class=HTMLResponse)
async def get_avance_sedes(db: Session = Depends(get_db)):
    try:
        resultados = db.query(
            Sede.nombre.label('sede'),
            Sede.cantidad_bienes.label('total'),
            func.count(Bien.id).label('registrados')
        ).outerjoin(
            Bien, Bien.sede_actual_id == Sede.id
        ).group_by(
            Sede.nombre, 
            Sede.cantidad_bienes
        ).all()
        
        data = [
            {
                "sede": row.sede,
                "avance": round((row.registrados / row.total * 100) if row.total else 0, 1)
            } 
            for row in resultados
        ]
        
        print("Datos:", data)  # Para debug
        
        chart_html = f"""
            <div class="chart-container">
                <h2>Avance por Sede</h2>
                <div class="chart-wrapper" style="height: 400px;">
                    <canvas id="avanceChart"></canvas>
                </div>
                <script>
                    window.addEventListener('DOMContentLoaded', function() {{
                        const ctx = document.getElementById('avanceChart').getContext('2d');
                        new Chart(ctx, {{
                            type: 'bar',
                            data: {{
                                labels: {json.dumps([d['sede'] for d in data])},
                                datasets: [{{
                                    label: 'Avance (%)',
                                    data: {json.dumps([d['avance'] for d in data])},
                                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                                    borderColor: 'rgb(54, 162, 235)',
                                    borderWidth: 1
                                }}]
                            }},
                            options: {{
                                responsive: true,
                                maintainAspectRatio: false
                            }}
                        }});
                    }});
                </script>
            </div>
            """
        return chart_html
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@gerencial_router.get("/chart-productividad", response_class=HTMLResponse)
async def get_productividad(db: Session = Depends(get_db)):
   try:
       query = db.query(
           Empleado.nombre.label('empleado'),
           func.count(Bien.id).label('bienes_registrados')
       ).join(
           Bien, 
           Bien.codigo_inventariador == Empleado.codigo
       ).filter(
           Empleado.es_inventariador == True
       ).group_by(
           Empleado.nombre
       ).order_by(
           desc('bienes_registrados')
       )
       
       resultados = query.all()
       max_registrados = max([r.bienes_registrados for r in resultados]) if resultados else 1
       
       data = [
           {
               "equipo": row.empleado,
               "productividad": round((row.bienes_registrados / max_registrados * 100), 1)
           } 
           for row in resultados
       ]
       
       chart_html = f"""
       <div class="card">
           <h2>Productividad por Equipo</h2>
           <div class="chart-wrapper">
               <canvas _="on load call renderChart(event.target, {json.dumps(data)}, 'Productividad')"></canvas>
           </div>
       </div>
       """
       return chart_html
   except Exception as e:
       raise HTTPException(status_code=500, detail=str(e))

def generate_chart_html(data, chart_type):
    return f"""
    <div class="chart-wrapper">
        <canvas _="on load call render{chart_type.capitalize()}(event.target)"></canvas>
    </div>
    <script type="text/hyperscript">
        def render{chart_type.capitalize()}(canvas)
            set data to {json.dumps(data)}
            call Chart.new(canvas, {{
                type: 'bar',
                data: {{
                    labels: data.map(d -> d.{'sede' if chart_type == 'sedes' else 'equipo'}),
                    datasets: [{{
                        label: '{"Avance" if chart_type == "sedes" else "Productividad"} (%)',
                        data: data.map(d -> d.{'avance' if chart_type == 'sedes' else 'productividad'}),
                        backgroundColor: 'rgba(54, 162, 235, 0.5)',
                        borderColor: 'rgb(54, 162, 235)',
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            max: 100
                        }}
                    }}
                }}
            }})
    </script>
    """