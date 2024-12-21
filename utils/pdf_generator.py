from fastapi import requests
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime


class InformeInventarioPDF:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.elementos = []
        # Estilo personalizado para títulos de sección
        self.styles.add(ParagraphStyle(
            name='SeccionTitulo',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=30
        ))
        # Estilo para subtítulos
        self.styles.add(ParagraphStyle(
            name='Subtitulo',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=20
        ))

    def _truncar_texto(self, texto, max_length=40):
        """Trunca el texto si excede la longitud máxima"""
        if len(texto) > max_length:
            return texto[:max_length-3] + '...'
        return texto

    def generar_informe(self, resumen_data, compras_data, bajas_data, operativo_data):
        """Genera el informe completo en PDF"""
        # Crear el documento
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )

        # Portada
        self._agregar_portada()
        
        # Resumen Ejecutivo
        self._agregar_resumen_ejecutivo(resumen_data)
        
        # Análisis Histórico
        self._agregar_analisis_historico(resumen_data)
        self.elementos.append(PageBreak())
        
        # Análisis de Compras
        self._agregar_analisis_compras(compras_data)
        self.elementos.append(PageBreak())
        
        # Análisis de Bajas
        self._agregar_analisis_bajas(bajas_data)
        self.elementos.append(PageBreak())
        
        # Aspectos Operativos
        self._agregar_aspectos_operativos(operativo_data)

        # Generar PDF
        # Agregar pie de página y encabezado
        doc.build(
            self.elementos,
            onFirstPage=self._crear_pie_pagina,    # Para la primera página
            onLaterPages=self._crear_pie_pagina    # Para las demás páginas
        )
        buffer.seek(0)
        return buffer

    def _agregar_portada(self):
        """Agrega la portada del informe"""
        titulo = Paragraph(
            "INFORME SITUACIONAL DE APERTURA\nPROCESO DE INVENTARIO 2024",
            self.styles['Title']
        )
        subtitulo = Paragraph(
            f"Análisis de la Situación Inicial basado en Datos Históricos 2022-2023\n [incluye Bajas y Compras 2024]\n<br/><br/>Fecha: {datetime.now().strftime('%d/%m/%Y')}",
            self.styles['Heading2']
        )
        self.elementos.extend([
            Spacer(1, 2*inch),
            titulo,
            Spacer(1, inch),
            subtitulo,
            PageBreak()
        ])

    def _agregar_resumen_ejecutivo(self, resumen_data):
        """Agrega la sección de resumen ejecutivo"""
        self.elementos.extend([
            Paragraph("Resumen Ejecutivo", self.styles['SeccionTitulo']),
            Paragraph(
                """El presente informe analiza el estado y evolución del inventario institucional, 
                abarcando el período 2022-2024. Se destacan hallazgos significativos en la gestión 
                de bienes patrimoniales, incluyendo adquisiciones, bajas y estado general de los activos.""",
                self.styles['Normal']
            ),
            Spacer(1, 0.5*inch)
        ])
        
        # Tabla de resumen
        datos = [
            ['Métrica', 'Valor'],
            ['Total Bienes 2022', str(resumen_data['total_comparison']['data'][0])],
            ['Total Bienes 2023', str(resumen_data['total_comparison']['data'][1])],
            ['Bienes en Buen Estado', '67%'],
            ['Bienes que Requieren Atención', '33%']
        ]
        
        tabla = Table(datos, colWidths=[250, 200])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        self.elementos.extend([
            tabla,
            Spacer(1, 0.5*inch)
        ])

    def _agregar_analisis_historico(self, resumen_data):
        """Agrega la sección de análisis histórico"""
        self.elementos.extend([
            Paragraph("1. Análisis Histórico 2022-2023", self.styles['SeccionTitulo']),
            Paragraph(
                """Se observa la evolución del inventario entre los años 2022 y 2023, 
                identificando patrones y áreas que requieren atención.""",
                self.styles['Normal']
            ),
            Spacer(1, 0.5*inch)
        ])
        
        # ... Aquí agregaríamos los gráficos y tablas del análisis histórico

    def _agregar_analisis_compras(self, compras_data):
        """Agrega la sección de análisis de compras"""
        self.elementos.extend([
            Paragraph("2. Análisis de Compras 2024", self.styles['SeccionTitulo']),
            Paragraph(
                f"""Durante el año 2024 se realizaron adquisiciones por un total de 
                S/. {compras_data['total_valor']:,.2f}, correspondientes a {compras_data['total_compras']} bienes.""",
                self.styles['Normal']
            ),
            Spacer(1, 0.5*inch)
        ])
        
        # Datos de resumen
        datos_resumen = [
            ['Métrica', 'Valor'],
            ['Total Bienes Adquiridos', f"{compras_data['total_compras']}"],
            ['Inversión Total', f"S/. {compras_data['total_valor']:,.2f}"],
            ['Bienes en Desuso', f"{compras_data['desuso']['sin_uso_depreciables'] + compras_data['desuso']['sin_uso_no_depreciables']}"],
            ['% Bienes en Desuso (Cantidad)', "49%"],
            ['% Bienes en Desuso (Valor S/.)', "77%"]
        ]

        tabla_resumen = Table(datos_resumen, colWidths=[250, 200])
        tabla_resumen.setStyle(self._get_tabla_style())
        
        self.elementos.extend([
            Paragraph("2.1 Resumen de Adquisiciones", self.styles['Subtitulo']),
            tabla_resumen,
            Spacer(1, 0.3*inch)
        ])

    def _agregar_analisis_bajas(self, bajas_data):
        """Agrega la sección de análisis de bajas"""
        # ... Implementación del análisis de bajas

    def _agregar_aspectos_operativos(self, operativo_data):
        """Agrega la sección de aspectos operativos"""
        # ... Implementación de aspectos operativos


    def _agregar_analisis_historico(self, resumen_data):
        """Agrega la sección de análisis histórico"""
        self.elementos.extend([
            Paragraph("1. Análisis Histórico 2022-2023", self.styles['SeccionTitulo']),
            Paragraph(
                """Se analizó la evolución del inventario institucional entre los años 2022 y 2023, 
                identificando las siguientes tendencias y hallazgos significativos:""",
                self.styles['Normal']
            ),
            Spacer(1, 0.2*inch)
        ])

        # Tabla de comparación anual
        datos_comparacion = [
            ['Año', 'Total Bienes', 'Variación'],
            ['2022', f"{resumen_data['total_comparison']['data'][0]:,}", "-"],
            ['2023', f"{resumen_data['total_comparison']['data'][1]:,}", 
            f"{((resumen_data['total_comparison']['data'][1] - resumen_data['total_comparison']['data'][0]) / resumen_data['total_comparison']['data'][0] * 100):.1f}%"]
        ]

        tabla = Table(datos_comparacion, colWidths=[150, 150, 150])
        tabla.setStyle(self._get_tabla_style())
        self.elementos.extend([
            Paragraph("1.1 Evolución Cuantitativa", self.styles['Subtitulo']),
            tabla,
            Spacer(1, 0.3*inch)
        ])

        # Estado de bienes
        self.elementos.extend([
            Paragraph("1.2 Estado de los Bienes", self.styles['Subtitulo']),
            Paragraph(
                """La siguiente tabla muestra la distribución de bienes según su estado, 
                identificando áreas que requieren atención inmediata:""",
                self.styles['Normal']
            ),
            Spacer(1, 0.2*inch)
        ])

        datos_estado = [
            ['Estado', 'Cantidad', 'Porcentaje'],
            ['Bueno (B)', f"{resumen_data['estado_2023']['data'][0]:,}", 
            f"{(resumen_data['estado_2023']['data'][0]/sum(resumen_data['estado_2023']['data'])*100):.1f}%"],
            ['Regular (R)', f"{resumen_data['estado_2023']['data'][1]:,}", 
            f"{(resumen_data['estado_2023']['data'][1]/sum(resumen_data['estado_2023']['data'])*100):.1f}%"],
            ['Malo (M)', f"{resumen_data['estado_2023']['data'][2]:,}", 
            f"{(resumen_data['estado_2023']['data'][2]/sum(resumen_data['estado_2023']['data'])*100):.1f}%"]
        ]

        tabla_estado = Table(datos_estado, colWidths=[150, 150, 150])
        tabla_estado.setStyle(self._get_tabla_style())
        self.elementos.extend([
            tabla_estado,
            Spacer(1, 0.3*inch)
        ])

    def _get_tabla_style(self):
        """Retorna un estilo común para las tablas"""
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])



    #******************  métodos para análisis de compras y bajas *************************
    def _agregar_analisis_compras(self, compras_data):
        """Agrega la sección de análisis de compras"""
        self.elementos.extend([
            Paragraph("2. Análisis de Compras 2024", self.styles['SeccionTitulo']),
            Paragraph(
                f"""Durante el año 2024 se realizaron adquisiciones significativas, 
                con una inversión total de S/. {compras_data['total_valor']:,.2f} 
                distribuida en {compras_data['total_compras']} bienes. 
                Se identificaron los siguientes aspectos relevantes:""",
                self.styles['Normal']
            ),
            Spacer(1, 0.3*inch)
        ])

        # Resumen de compras
        datos_resumen = [
            ['Métrica', 'Valor'],
            ['Total Bienes Adquiridos', f"{compras_data['total_compras']}"],
            ['Inversión Total', f"S/. {compras_data['total_valor']:,.2f}"],
            ['Bienes en Desuso', f"{compras_data['desuso']['sin_uso_depreciables'] + compras_data['desuso']['sin_uso_no_depreciables']}"],
            ['% Valor en Desuso', "77%"]  # Este valor podría calcularse dinámicamente
        ]

        tabla_resumen = Table(datos_resumen, colWidths=[200, 250])
        tabla_resumen.setStyle(self._get_tabla_style())
        
        self.elementos.extend([
            Paragraph("2.1 Resumen de Adquisiciones", self.styles['Subtitulo']),
            tabla_resumen,
            Spacer(1, 0.3*inch)
        ])

        # Análisis de bienes en desuso
        self.elementos.extend([
            Paragraph("2.2 Análisis de Bienes en Desuso", self.styles['Subtitulo']),
            Paragraph(
                """Se ha identificado una cantidad significativa de bienes adquiridos 
                que actualmente se encuentran sin uso asignado:""",
                self.styles['Normal']
            ),
            Spacer(1, 0.2*inch)
        ])

        total_valor = compras_data['total_valor']
        datos_desuso = [
            ['Categoría', 'Cant.', 'Valor (S/.)', '% Cant.', '% Valor'],
            *[
                [self._truncar_texto(item['categoria']), 
                str(item['cantidad']),
                f"{item['valor']:,.2f}",
                f"{item['porcentaje']:.1f}%",
                f"{(item['valor']/total_valor*100):.1f}%"]
                for item in compras_data['detalles_desuso']
            ]
        ]

        tabla_desuso = Table(datos_desuso, colWidths=[200, 40, 75, 55, 55])
        tabla_desuso.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),      # Primera columna a la izquierda
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),   # Resto de columnas centradas
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),       # Tamaño fuente encabezado
            ('FONTSIZE', (0, 1), (-1, -1), 8),       # Tamaño fuente reducido para datos
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('WORDWRAP', (0, 0), (0, -1), True)      # Permite wrap de texto
        ]))
        self.elementos.extend([
            tabla_desuso,
            Spacer(1, 0.3*inch),
            Paragraph(
                """Observación: El alto porcentaje de bienes en desuso representa 
                un riesgo significativo para la eficiencia en el uso de recursos.""",
                self.styles['Italic']
            )
        ])

    def _agregar_analisis_bajas(self, bajas_data):
        """Agrega la sección de análisis de bajas"""
        self.elementos.extend([
            Paragraph("3. Análisis de Bajas 2024", self.styles['SeccionTitulo']),
            Paragraph(
                """Durante el año 2024 se procesaron bajas de bienes patrimoniales, 
                siguiendo los lineamientos establecidos en las Directivas 004-2021-EF/54.01 
                y 006-2021-EF/54.01. Los principales hallazgos son:""",
                self.styles['Normal']
            ),
            Spacer(1, 0.3*inch)
        ])
        
        # Distribución por procedencia
        datos_procedencia = [
            ['Procedencia', 'Cantidad', '% del Total'],
            ['Compras', '737', '75.9%'],
            ['Transferencias', '136', '14.0%'],
            ['Donaciones', '36', '3.7%'],
            ['Saneamiento', '35', '3.6%'],
            ['Reposición', '26', '2.7%'],
            ['Fabricación', '1', '0.1%']
        ]

        tabla_procedencia = Table(datos_procedencia, colWidths=[150, 100, 100])
        tabla_procedencia.setStyle(self._get_tabla_style())
        
        self.elementos.extend([
            Paragraph("3.1 Procedencia de Bienes Dados de Baja", self.styles['Subtitulo']),
            tabla_procedencia,
            Spacer(1, 0.3*inch)
        ])

        self.elementos.extend([
            Spacer(1, 0.2*inch),
            Paragraph(
                """Observación: Es necesario evaluar y monitorear los motivos de 
                procedencia 'Saneamiento' y 'Reposición', para prevenir su escalamiento 
                y asegurar que estas categorías no se conviertan en una práctica frecuente.""",
                self.styles['Italic']
            ),
            Spacer(1, 0.3*inch)
        ])

        # Casos especiales
        self.elementos.extend([
            Paragraph("3.2 Casos que Requieren Atención Especial", self.styles['Subtitulo']),
            Paragraph(
                """Se identificaron los siguientes casos que requieren una revisión 
                detallada de los criterios de baja:""",
                self.styles['Normal']
            ),
            Spacer(1, 0.2*inch)
        ])

        datos_especiales = [
            ['Tipo de Bien', 'Estado', 'Cantidad', 'Observaciones'],
            ['Laptops', 'Bueno', '5', 'Revisar criterios de baja'],
            ['Cámara de Video', 'Bueno', '1', 'Verificar motivo de baja'],
            ['Vehículos', 'Regular', '3', '2 autos y 1 camioneta']
        ]

        tabla_especiales = Table(datos_especiales, colWidths=[150, 100, 100, 150])
        tabla_especiales.setStyle(self._get_tabla_style())
        self.elementos.extend([
            tabla_especiales,
            Spacer(1, 0.3*inch)
        ])

        self.elementos.extend([
            Paragraph(
                """IMPORTANTE: De acuerdo a la normativa vigente, existe un plazo máximo 
                de cinco (5) meses para la disposición final de los bienes dados de baja. 
                Al no contar con las fechas específicas de declaración de baja para cada 
                bien, no es posible determinar el cumplimiento de estos plazos. Se 
                recomienda implementar un sistema de seguimiento para asegurar el 
                cumplimiento de estos plazos normativos.""",
                self.styles['Italic']
            )
        ])


    #**********************     método para aspectos operativos y las funciones auxiliares *******************
    def _agregar_aspectos_operativos(self, operativo_data):
        """Agrega la sección de aspectos operativos"""
        self.elementos.extend([
            Paragraph("4. Aspectos Operativos y Financieros", self.styles['SeccionTitulo']),
            Paragraph(
                """Este capítulo analiza los aspectos críticos de la gestión operativa 
                del inventario, enfocándose en mantenimiento, aseguramiento y recomendaciones 
                para optimizar la gestión.""",
                self.styles['Normal']
            ),
            Spacer(1, 0.3*inch)
        ])

        # 4.1 Estado de Bienes Críticos
        self.elementos.extend([
            Paragraph("4.1 Estado de Bienes Críticos", self.styles['Subtitulo']),
            Paragraph(
                """La siguiente tabla muestra el estado actual de los bienes considerados 
                críticos por su función o valor:""",
                self.styles['Normal']
            ),
            Spacer(1, 0.2*inch)
        ])

        datos_criticos = [
            ['Tipo de Bien', 'Buen Estado', 'Regular', 'Malo', 'Total'],
            ['Extintores', '167', '124', '4', '295'],
            ['Equipos Multifuncionales', '115', '131', '25', '271'],
            ['Aires Acondicionados', '55', '69', '8', '132'],
            ['Teléfonos Celulares', '844', '13', '5', '862']
        ]

        #tabla_criticos = Table(datos_criticos, colWidths=[150, 90, 90, 90, 90])
        tabla_criticos = Table(datos_criticos, colWidths=[120, 70, 70, 70, 70])
        tabla_criticos.setStyle(self._get_tabla_style())
        self.elementos.extend([
            tabla_criticos,
            Spacer(1, 0.3*inch)
        ])

        # 4.2 Análisis de Riesgos
        self.elementos.extend([
            Paragraph("4.2 Análisis de Riesgos", self.styles['Subtitulo']),
            Paragraph(
                """Se han identificado los siguientes riesgos que requieren atención inmediata:""",
                self.styles['Normal']
            ),
            Spacer(1, 0.2*inch)
        ])

        # Lista de riesgos identificados
        riesgos = [
            "Equipos Multifuncionales: 48% en estado Regular, con riesgo de deterioro acelerado.",
            "Teléfonos Celulares: 98% en buen estado, pero con riesgo de obsolescencia masiva.",
            "Aires Acondicionados: 52% en estado Regular, requieren mantenimiento preventivo urgente.",
            "Extintores: 42% requieren evaluación especializada y certificación."
        ]

        for riesgo in riesgos:
            self.elementos.extend([
                Paragraph(f"• {riesgo}", self.styles['Normal']),
                Spacer(1, 0.1*inch)
            ])

        # 4.3 Recomendaciones
        self.elementos.extend([
            Spacer(1, 0.2*inch),
            Paragraph("4.3 Recomendaciones", self.styles['Subtitulo']),
            Paragraph(
                """Basado en el análisis realizado, se proponen las siguientes recomendaciones:""",
                self.styles['Normal']
            ),
            Spacer(1, 0.2*inch)
        ])

        # Tabla de recomendaciones y presupuesto estimado
        datos_recomendaciones = [
            ['Área', 'Recomendación', 'Presupuesto Estimado'],
            ['Mantenimiento', 'Implementar programa preventivo', 'S/. 120,000.00'],
            ['Renovación', 'Plan escalonado de equipos', 'S/. 250,000.00'],
            ['Capacitación', 'Programa de uso adecuado', 'S/. 30,000.00'],
            ['Auditorías', 'Evaluaciones trimestrales', 'S/. 40,000.00']
        ]

        #tabla_recomendaciones = Table(datos_recomendaciones, colWidths=[100, 250, 150])
        tabla_recomendaciones = Table(datos_recomendaciones, colWidths=[80, 200, 120])
        tabla_recomendaciones.setStyle(self._get_tabla_style())
        self.elementos.extend([
            tabla_recomendaciones,
            Spacer(1, 0.3*inch)
        ])

        # Conclusión
        self.elementos.extend([
            Paragraph("4.4 Conclusión", self.styles['Subtitulo']),
            Paragraph(
                """La implementación de estas recomendaciones requiere una inversión 
                total estimada de S/. 440,000.00, que representa aproximadamente el 2.9% 
                del valor total de las adquisiciones realizadas en 2024. Esta inversión 
                se justifica considerando el valor de los activos a proteger y el costo 
                potencial de su deterioro o pérdida.""",
                self.styles['Normal']
            )
        ])

        self.elementos.extend([
            #tabla_recomendaciones,
            Spacer(1, 0.2*inch),
            Paragraph(
                """Nota: Los montos y cálculos presentados son referenciales y pretenden 
                servir como guía inicial para la toma de decisiones. Se recomienda su 
                actualización y ajuste de acuerdo a la Política Institucional vigente 
                y las prioridades establecidas por las autoridades competentes.""",
                self.styles['Italic']
            )
        ])

    def _agregar_numero_pagina(self, canvas, doc):
        """Agrega números de página al documento"""
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        page_number_text = f"Página {doc.page}"
        canvas.drawRightString(
            doc.pagesize[0] - 72,
            72,
            page_number_text
        )
        canvas.restoreState()

    def _crear_pie_pagina(self, canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        autor = 'Generado por: [DataExtractor]'
        #autor = '<link href="mailto:duilio@dataextractor.cloud">Generado por: {usuario}</link>'
        # Fecha a la izquierda
        canvas.drawString(72, 72, f"Fecha: {fecha}")
        # Autor al centro
        canvas.drawCentredString(doc.pagesize[0]/2, 72, autor)
        # Número de página a la derecha
        canvas.drawRightString(doc.pagesize[0]-72, 72, f"Página {doc.page}")
        canvas.restoreState()

        #usuario = request.state.user.codigo  # Obtener usuario actual
        #autor = f"Generado por: {usuario}"

