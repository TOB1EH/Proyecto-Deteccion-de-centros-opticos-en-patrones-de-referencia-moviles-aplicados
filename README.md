# Detección de Centros Ópticos en Patrones de Referencia Móviles Aplicados

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green.svg)](https://opencv.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Experimental-orange.svg)](README.md)

> **Sistema de detección y tracking de marcadores ópticos LED para aplicaciones de Helmet Mounted Display (HMD)**

Sistema **en desarrollo activo** para la detección automática de marcadores LED infrarojos y el cálculo preciso de sus centros ópticos, diseñado para sistemas de trackeo de cascos en tiempo real en aeronaves.

---

## ⚠️ ADVERTENCIA IMPORTANTE

**Este proyecto se encuentra en fase experimental y NO está listo para uso en producción.**

### Limitaciones Críticas Actuales:

- 🔴 **Alta tasa de falsos positivos** - El sistema confunde objetos brillantes con LEDs reales
- 🔴 **Error de precisión elevado** - Desviaciones de hasta 122 píxeles (inaceptable para trackeo de precisión)
- 🔴 **Sin validación ground-truth** - Los resultados reportados no han sido verificados contra posiciones reales conocidas
- 🔴 **Método de parpadeo NO implementado** - Técnica crítica para eliminar ruido IR pendiente
- 🔴 **Sin filtro predictivo (Kalman)** - Tracking temporal básico, vulnerable a oclusiones
- 🔴 **Sin corrección de distorsión** - No considera aberraciones de lente

**Los datos estadísticos presentados incluyen detecciones erróneas y NO deben considerarse confiables para evaluación cuantitativa.**

### Próximos Pasos Críticos:
1. Implementar método de detección por parpadeo sincronizado
2. Establecer ground-truth y validar resultados
3. Calibrar cámara y corregir distorsión
4. Implementar filtro de Kalman
5. Reducir error a σ < 5 px por LED

---

## 📋 Tabla de Contenidos

- [Descripción del Proyecto](#-descripción-del-proyecto)
- [Metodología](#-metodología)
- [Características Principales](#-características-principales)
- [Resultados Actuales](#-resultados-actuales)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Instalación y Uso](#-instalación-y-uso)
- [Documentación](#-documentación)
- [Estado del Proyecto](#-estado-del-proyecto)
- [Autor](#-autor)

---

## 🎯 Descripción del Proyecto

Este proyecto desarrolla un sistema de visión por computadora para la **detección robusta de marcadores LED infrarojos** y el **cálculo de sus centros ópticos con precisión subpíxel**, aplicado al trackeo de Helmet Mounted Displays (HMD) en entornos aeronáuticos.

### Contexto y Aplicación

Los sistemas HMD modernos requieren conocer con alta precisión la posición y orientación de la cabeza del piloto en tiempo real. Para lograrlo, se utilizan marcadores ópticos LED (infrarojos) montados en el casco o en la cabina, cuyas posiciones son detectadas por cámaras. La precisión en la determinación de los **centros ópticos** de estos marcadores es crítica para el correcto funcionamiento del sistema de realidad aumentada.

### Objetivos del Proyecto

1. **Desarrollar algoritmos robustos** para la detección de marcadores LED en condiciones variables de iluminación
2. **Calcular centros ópticos con precisión subpíxel** minimizando errores de estimación
3. **Operar en tiempo real** (compatible con video streaming a 24+ fps)
4. **Minimizar falsos positivos y negativos** mediante técnicas multi-método
5. **Cuantificar el error inherente** en la estimación de centros ópticos bajo diversas condiciones

---

## 🔬 Metodología

El proyecto se estructura en **tres etapas** según el plan metodológico establecido:

### **Etapa 1: Análisis y Desarrollo de Algoritmos** 🔄 *En Desarrollo*

Análisis de herramientas de procesamiento de imágenes y desarrollo de software para detección de marcadores con mínima tasa de falsos positivos/negativos y determinación precisa de centros ópticos.

**Estado actual:** Se han implementado técnicas preliminares, pero **el sistema NO cumple aún con los objetivos de precisión y robustez** establecidos. Se requiere trabajo adicional significativo.

**Técnicas implementadas (estado experimental):**

| Técnica | Propósito | Estado |
|---------|-----------|--------|
| **Conversión a escala de grises** | Simplificación del análisis (cámaras RGB con señal IR) | ✅ Implementado |
| **Espacio de color HSV** | Segmentación de regiones brillantes y saturadas | ⚠️ Implementado, requiere calibración |
| **Filtrado espacial (Gaussiano, mediana)** | Reducción de ruido sin pérdida de estructura | ✅ Implementado |
| **Umbralización adaptativa** | Aislamiento de regiones intensas con iluminación no uniforme | ⚠️ Implementado, parámetros no óptimos |
| **Detección de blobs brillantes** | Localización de agrupaciones de píxeles compatibles con LEDs | ⚠️ Implementado, genera falsos positivos |
| **Detección de bordes (Canny)** | Resaltado de contornos definidos | ✅ Implementado |
| **Transformada de Hough (círculos)** | Detección de estructuras circulares/elípticas | ⚠️ Implementado, insuficientemente restrictivo |
| **Filtro contextual (validación de vecindad)** | Verificación geométrica e intensidad en torno al LED | ⚠️ Parcial, requiere mejora |
| **Cálculo del centro geométrico** | Precisión subpíxel mediante centroide ponderado | ⚠️ Implementado, alta variabilidad |
| **Tracking temporal** | Identificación consistente de LEDs entre fotogramas | ⚠️ Básico, necesita filtro predictivo |
| **Filtrado estadístico (IQR)** | Eliminación automática de outliers | ⚠️ Insuficiente |
| **Detección de parpadeo sincronizado** | **CRÍTICO**: Aumentar contraste frente al fondo restando frames LED on/off | 🔴 **NO IMPLEMENTADO** |
| **Corrección de perspectiva** | Ajuste geométrico por ángulo de cámara | 🔴 **NO IMPLEMENTADO** |
| **Tracking predictivo (Kalman)** | Robustez temporal ante oclusiones | 🔴 **NO IMPLEMENTADO** |

**Estrategia multi-método:** El sistema combina **4 métodos de detección paralelos** cuyos resultados se fusionan mediante clustering espacial. Sin embargo, **esta estrategia es insuficiente** sin la implementación del método de parpadeo y validación contextual más estricta.

### **Etapa 2: Diseño de Ensayos de Validación** 🔄 *En planificación*

Definición del conjunto de ensayos para estimar el error en la determinación de coordenadas de centros ópticos bajo diferentes condiciones ambientales.

**Factores a evaluar:**
- Variación de iluminación ambiental
- Distancia cámara-marcadores
- Ángulo de observación
- Velocidad de movimiento del patrón
- Interferencias (reflejos, obstrucciones parciales)

### **Etapa 3: Ensayo y Análisis Comparativo** ⏳ *Pendiente*

Ensayo de los algoritmos desarrollados con el conjunto de pruebas diseñado, análisis estadístico de resultados y determinación del algoritmo óptimo.

---

## ✨ Características Principales

### Sistema de Detección Multi-Método (Experimental)

El detector combina 4 algoritmos complementarios en su versión actual:

1. **Umbralización de alta intensidad** - Detección directa de píxeles muy brillantes (genera falsos positivos)
2. **SimpleBlobDetector** - Análisis geométrico de regiones candidatas (criterios demasiado permisivos)
3. **Transformada de Hough para círculos** - Validación de geometría circular (insuficientemente restrictiva)
4. **Segmentación HSV** - Aislamiento por brillo y saturación (requiere calibración)

⚠️ **Limitación actual:** Sin el método de parpadeo sincronizado, estos algoritmos generan numerosos falsos positivos al confundir LEDs con otros objetos brillantes (reflejos, artefactos, ruido IR).

### Tracking Temporal Básico

- **Identificación por proximidad** entre fotogramas consecutivos
- **Memoria espacial limitada** - Predice posición basándose solo en frame anterior
- ⚠️ **Sin filtro predictivo robusto** (Kalman) - Vulnerable a oclusiones y movimientos bruscos
- ⚠️ **Pérdida de identidad** en casos de cruce de LEDs o detecciones ambiguas

### Procesamiento en Tiempo Real

- **Velocidad:** ~24 fps en hardware estándar
- **Configuración parametrizable** vía código (no archivo de configuración externo)
- **Múltiples modos de salida:** video anotado, JSON, reportes estadísticos
- ⚠️ **Advertencia:** Velocidad no garantiza precisión - muchas detecciones son erróneas

### Análisis Estadístico Automático

- Cálculo de **desviación estándar** por LED y por eje
- Detección automática de **outliers** (método IQR - insuficiente)
- Generación de **reportes detallados** con métricas
- ⚠️ **Problema crítico:** Las estadísticas incluyen falsos positivos sin filtrar, por lo que **no son confiables** para evaluación cuantitativa real

---

## 📊 Resultados Actuales

### **Etapa 1: Detección en Video de Prueba - Estado Experimental**

**Condiciones del Experimento:**

El experimento se realizó bajo las siguientes condiciones de laboratorio:

- **Patrón de prueba:** 3 LEDs infrarrojos montados en soporte móvil
- **Cámara:** Teléfono móvil estándar (no especializada en captura IR)
- **Entorno:** Laboratorio con iluminación natural variable
  - Presencia de luz solar indirecta
  - Reflejos sobre superficies del laboratorio
  - Condiciones de iluminación NO controladas
- **Video capturado:** `patron_leds.mp4` (1280×720 px, 24 fps, 854 frames, ~35 segundos)
- **Movimiento:** Patrón LED en movimiento manual continuo

⚠️ **Limitaciones del setup experimental:**
- Cámara de teléfono NO optimizada para captura de luz infrarroja
- Presencia de ruido IR ambiental y reflejos de luz solar
- Iluminación variable durante la captura
- Sin control de distancia ni ángulo de observación
- Sin marcadores ground-truth para validación de posiciones reales

Estas condiciones no controladas **aumentan significativamente la dificultad** de detección precisa y explican en parte la alta tasa de falsos positivos observada.

---

#### ⚠️ Estado Actual: **EXPERIMENTAL - REQUIERE VALIDACIÓN**

Si bien el sistema procesa los 854 fotogramas y genera detecciones, **los resultados NO están validados** y presentan **limitaciones críticas**:

- ⚠️ **Alta tasa de falsos positivos**: Muchas detecciones reportadas no corresponden a los centros ópticos reales
- ⚠️ **Error elevado**: Desviaciones de hasta 122 px (LED 3) son **inaceptables** para aplicaciones de trackeo de precisión
- ⚠️ **Falta de validación ground-truth**: No se han comparado las detecciones con posiciones reales conocidas
- ⚠️ **Estadísticas no confiables**: Los datos reportados incluyen detecciones erróneas sin filtrado adecuado

#### Datos Preliminares (NO VALIDADOS)

| LED | Posición Promedio (x, y) | Desviación σ | Observación |
|-----|-------------------------|--------------|-------------|
| **LED 1** | (344.71, 394.74) px | **54.68 px** | Error moderado-alto, requiere mejora |
| **LED 2** | (874.13, 360.16) px | **32.23 px** | Menor desviación, aún insuficiente |
| **LED 3** | (1151.53, 601.75) px | **98.07 px** | **Error crítico**, inaceptable para uso real |

![Ejemplo de detección](estimacion_centros_opticos/Informes/Informe1/image-1.png)

#### ⚠️ Problemas Identificados

**Errores de precisión:**

| LED | σ_x (px) | σ_y (px) | Problema Principal |
|-----|----------|----------|-------------------|
| LED 1 | 71.10 | 50.38 | Confusión con reflejos/ruido, desviación excesiva |
| LED 2 | 44.40 | 25.56 | Menor error pero aún por encima del umbral aceptable |
| LED 3 | 122.11 | 96.52 | **Error crítico**: probable confusión sistemática con otros objetos brillantes |

**Principales limitaciones detectadas:**
1. **Falsos positivos frecuentes**: El sistema detecta objetos brillantes que no son LEDs (reflejos, artefactos)
2. **Falta de discriminación contextual**: No valida suficientemente el entorno del LED (anillo negro, geometría esperada)
3. **Ausencia de validación temporal robusta**: No aprovecha la coherencia temporal para filtrar detecciones espurias
4. **Sin corrección de distorsión**: No considera distorsión de lente ni perspectiva
5. **Umbralización inadecuada**: Los parámetros actuales no son suficientemente selectivos

#### Técnicas Implementadas (Requieren Mejora)

- ⚠️ **Umbralización adaptativa** - Implementada pero con parámetros no optimizados
- ⚠️ **Detección geométrica de blobs** - Criterios demasiado permisivos, genera falsos positivos
- ⚠️ **Transformada de Hough** - No suficientemente restrictiva
- ⚠️ **Segmentación HSV** - Requiere calibración
- ⚠️ **Tracking temporal** - Básico, necesita filtro predictivo (Kalman)
- ⚠️ **Filtrado IQR** - Insuficiente para eliminar todos los outliers

![Pipeline de procesamiento](estimacion_centros_opticos/Informes/Informe1/image-2.png)

---

## 📁 Estructura del Proyecto

```
Estimacion-Pose-Casco/
│
├── README.md                          # Este archivo
│
└── estimacion_centros_opticos/        # Módulo principal
    │
    ├── led_detector_final.py          # ⭐ Detector final (4 métodos combinados)
    ├── led_detector_video_output.py   # Procesador con salida de video anotado
    ├── diagnostic.py                  # Herramienta de diagnóstico de video
    │
    ├── run.sh                         # Script de ejecución principal
    ├── run_live.sh                    # Script para ejecución en tiempo real
    ├── generate_marked_video.sh       # Generador de video con marcas
    │
    ├── .gitignore                     # Exclusiones de Git
    ├── .pylintrc                      # Configuración de linting
    ├── README.md                      # Documentación del módulo
    │
    ├── documentacion_codigo/          # 📚 Documentación técnica completa
    │   ├── DOCUMENTACION_CODIGO.md    # Documentación detallada del código
    │   ├── GUIA_RAPIDA.md             # Guía de inicio rápido
    │   ├── INICIO_RAPIDO.md           # Tutorial de primeros pasos
    │   ├── SINTAXIS_PYTHON.md         # Referencia de sintaxis
    │   ├── MAPA_MENTAL.md             # Mapa conceptual del proyecto
    │   ├── INDICE.md                  # Índice navegable
    │   └── INDICE_DOCUMENTACION.md    # Índice de documentación
    │
    ├── analisis_metodos_utilizados/   # 🔍 Análisis metodológico
    │   ├── 1. DIAGRAMA_VISUAL_METODOS.md
    │   ├── 2. ANALISIS_METODOS_IMPLEMENTADOS.md
    │   ├── 3. CONCLUSIONES_METODOS.md
    │   ├── 4. REFERENCIA_TECNICA_METODOS.md
    │   ├── 5. MAPEO_LINEAS_CODIGOS.md
    │   └── 6. MAPA_NAVEGACION_COMPLETO.md
    │
    ├── Informes/                      # 📄 Informes del proyecto
    │   └── Informe1/
    │       ├── INFORME_NARRATIVO_ETAPA_1.md  # Informe detallado Etapa 1
    │       ├── INFORME_FUNES_TOBIAS.pdf      # Informe formal
    │       └── *.png                          # Imágenes del informe
    │
    ├── patron_leds/                   # 🎥 Videos de prueba
    │   ├── patron_leds.mp4            # Video principal de prueba
    │   └── video_prueba.mp4           # Video alternativo
    │
    ├── resultados_v1/                 # 📊 Resultados versión 1
    │   ├── RESULTADOS_FINALES.md      # Resumen de resultados
    │   ├── reporte_deteccion.txt      # Reporte textual detallado
    │   ├── resultados_completos.json  # Base de datos frame-by-frame
    │   ├── resumen_estadisticas.json  # Estadísticas agregadas
    │   └── frames/                    # Fotogramas procesados con marcas
    │
    └── versiones_anteriores_descartadas/  # 🗃️ Versiones de desarrollo
        ├── led_detector_v1.py
        ├── led_detector_v2.py
        ├── led_detector_mejorado.py
        ├── led_detector_calibrado.py
        ├── led_detector_stable.py
        └── README_led_detector_v1_y_v2.md
```

---

## 🚀 Instalación y Uso

### Requisitos Previos

- **Python 3.10+**
- **OpenCV 4.x** (`opencv-python`)
- **NumPy**
- Sistema operativo: Linux, macOS, Windows

### Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/TOB1EH/Proyecto-Deteccion-de-centros-opticos-en-patrones-de-referencia-moviles-aplicados.git
cd Proyecto-Deteccion-de-centros-opticos-en-patrones-de-referencia-moviles-aplicados/estimacion_centros_opticos

# 2. Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# 3. Instalar dependencias
pip install opencv-python numpy
```

### Uso Básico

#### Procesamiento de Video con Salida Anotada

```bash
# Ejecutar detector sobre video de prueba
./run.sh

# O manualmente:
python led_detector_video_output.py patron_leds/patron_leds.mp4 resultados/
```

**Salidas generadas:**
- `resultados/frames/`: Fotogramas con LEDs marcados en color
- `resultados/resultados_completos.json`: Datos frame-by-frame
- `resultados/resumen_estadisticas.json`: Estadísticas agregadas
- `resultados/reporte_deteccion.txt`: Informe textual

#### Diagnóstico de Video

```bash
# Analizar propiedades del video
python diagnostic.py patron_leds/patron_leds.mp4
```

#### Generación de Video Marcado

```bash
# Crear video con LEDs marcados visualmente
./generate_marked_video.sh
```

### Configuración Avanzada

El detector es altamente parametrizable. Consulta `documentacion_codigo/GUIA_RAPIDA.md` para opciones de configuración.

---

## 📚 Documentación

La documentación completa del proyecto se encuentra organizada en:

### Documentación Técnica
- **[DOCUMENTACION_CODIGO.md](estimacion_centros_opticos/documentacion_codigo/DOCUMENTACION_CODIGO.md)** - Explicación detallada de cada módulo y función
- **[GUIA_RAPIDA.md](estimacion_centros_opticos/documentacion_codigo/GUIA_RAPIDA.md)** - Referencia rápida de uso
- **[INICIO_RAPIDO.md](estimacion_centros_opticos/documentacion_codigo/INICIO_RAPIDO.md)** - Tutorial para comenzar

### Análisis Metodológico
- **[ANALISIS_METODOS_IMPLEMENTADOS.md](estimacion_centros_opticos/analisis_metodos_utilizados/2.%20ANALISIS_METODOS_IMPLEMENTADOS.md)** - Evaluación de técnicas aplicadas
- **[CONCLUSIONES_METODOS.md](estimacion_centros_opticos/analisis_metodos_utilizados/3.%20CONCLUSIONES_METODOS.md)** - Conclusiones y recomendaciones

### Informes de Etapa
- **[INFORME_NARRATIVO_ETAPA_1.md](estimacion_centros_opticos/Informes/Informe1/INFORME_NARRATIVO_ETAPA_1.md)** - Informe completo de la Etapa 1

---

## 🔧 Estado del Proyecto

### ⚠️ Estado General: **EN DESARROLLO ACTIVO - NO LISTO PARA PRODUCCIÓN**

El proyecto se encuentra en fase experimental. Si bien se han implementado múltiples técnicas de detección, **el sistema NO es confiable** para aplicaciones reales debido a falsos positivos y errores de precisión significativos.

### ✅ Completado (Fase Experimental)

- [x] **Etapa 1 (Parcial):** Implementación inicial de algoritmo multi-método
- [x] Implementación de 4 técnicas de detección (requieren refinamiento)
- [x] Sistema de tracking temporal básico
- [x] Generación automática de reportes estadísticos
- [x] Procesamiento en tiempo real (~24 fps)
- [x] Documentación técnica del código base
- [x] Pruebas preliminares en video de laboratorio

### 🔴 Problemas Críticos Identificados

- [ ] **Alta tasa de falsos positivos** - El sistema detecta objetos que no son LEDs
- [ ] **Error de precisión inaceptable** - Desviaciones de hasta 122 px (LED 3)
- [ ] **Falta de validación ground-truth** - No hay comparación con posiciones reales conocidas
- [ ] **Parámetros no optimizados** - Umbrales y criterios geométricos demasiado permisivos
- [ ] **Ausencia de corrección de distorsión** - No se consideran aberraciones de lente
- [ ] **Tracking temporal insuficiente** - Falta filtro predictivo robusto (Kalman)

### 🔄 Trabajo Pendiente Crítico (Etapa 1)

- [ ] **Implementar método de parpadeo sincronizado** - Crucial para eliminar falsos positivos
  - Capturar frames con LED encendido/apagado
  - Restar frames para aislar LEDs reales
  - Aumentar contraste LED vs. ruido IR
- [ ] **Validación con ground-truth** - Establecer posiciones reales conocidas
- [ ] **Calibración de cámara** - Matriz intrínseca y corrección de distorsión
- [ ] **Filtro de Kalman** - Predicción temporal de posiciones
- [ ] **Refinamiento de parámetros** - Ajuste basado en validación cuantitativa
- [ ] **Mejora de filtro contextual** - Validar anillo negro/fondo oscuro estricto
- [ ] **Detección de oclusiones** - Manejo robusto de LEDs parcialmente ocultos
- [ ] **Reducción de error** - Objetivo: σ < 5 px por LED

### 🔄 Etapa 2: Diseño de Ensayos (No Iniciada)

- [ ] Definir protocolo de validación con ground-truth
- [ ] Diseñar ensayos bajo condiciones variables:
  - [ ] Iluminación ambiental (controlada, natural, variable)
  - [ ] Distancia cámara-marcadores (rango operativo)
  - [ ] Ángulo de observación (frontal, lateral, extremo)
  - [ ] Velocidad de movimiento (estático, lento, rápido)
  - [ ] Interferencias (reflejos, obstrucciones, ruido IR)
- [ ] Establecer métricas de calidad aceptables
- [ ] Crear conjunto de videos de prueba controlados

### ⏳ Etapa 3: Ensayo y Análisis (No Iniciada)

- [ ] Ensayo comparativo de algoritmos mejorados
- [ ] Análisis estadístico exhaustivo con datos validados
- [ ] Caracterización cuantitativa del error
- [ ] Comparación con literatura/sistemas comerciales
- [ ] Documentación de limitaciones y condiciones de uso
- [ ] Informe final con recomendaciones

### 🎯 Mejoras Planificadas (Prioridad Alta)

1. **Detección por parpadeo** - Esencial para eliminar ruido
2. **Calibración de cámara** - Corrección de distorsión geométrica
3. **Filtro de Kalman** - Predicción temporal robusta
4. **Validación ground-truth** - Establecer precisión real del sistema
5. **Ajuste de parámetros** - Optimización basada en datos validados
6. **Manejo de oclusiones** - Recuperación tras pérdida temporal
7. **Corrección de perspectiva 3D** - Transformación a coordenadas mundo
8. **Integración PnP** - Estimación de pose 6-DOF del casco

---

## 👨‍💻 Autor

**Tobias Funes**  
Facultad de Ingeniería - Instituto Universitario Aeronáutico (IUA)  
Proyecto: Sistema de Trackeo para HMD (Helmet Mounted Display)  
Período: Octubre-Noviembre 2025

---

## 🙏 Agradecimientos

- OpenCV Community por las herramientas de visión por computadora
- IUA - Facultad de Ingeniería por el soporte académico
- Proyecto de investigación en sistemas HMD para aviación

---

**🔗 Enlaces Útiles:**
- [Repositorio GitHub](https://github.com/TOB1EH/Proyecto-Deteccion-de-centros-opticos-en-patrones-de-referencia-moviles-aplicados)
- [Documentación OpenCV](https://docs.opencv.org/)
- [Issues y Sugerencias](https://github.com/TOB1EH/Proyecto-Deteccion-de-centros-opticos-en-patrones-de-referencia-moviles-aplicados/issues)
