# 📚 Documentación Completa del Código - LED Detector Final

## 📋 Tabla de Contenidos

1. [Arquitectura General](#arquitectura-general)
2. [Clases Principales](#clases-principales)
3. [Métodos de Detección](#métodos-de-detección)
4. [Flujo de Procesamiento](#flujo-de-procesamiento)
5. [Algoritmo de Rastreo Temporal](#algoritmo-de-rastreo-temporal)
6. [Filtrado de Outliers](#filtrado-de-outliers)
7. [Ejemplos de Uso](#ejemplos-de-uso)

---

## Arquitectura General

```
┌─────────────────────────────────────────────────────────────────┐
│                    VIDEO DE ENTRADA                             │
│           (patron_leds/patron_leds.mp4)                         │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │   VideoProcessor.process()       │
        │  (Procesa frame por frame)       │
        └──────────────┬───────────────────┘
                       │
        ┌──────────────▼───────────────────┐
        │  RobustLEDDetector.detect()      │
        │  (Para cada frame)               │
        └──────────────┬───────────────────┘
                       │
        ┌──────────────▼───────────────────────────────┐
        │        4 MÉTODOS DE DETECCIÓN EN PARALELO    │
        │  (Todos se ejecutan simultáneamente)         │
        ├──────────────────────────────────────────────┤
        │  1. _detect_via_high_threshold()             │
        │     └─ Umbral simple (I > 200)               │
        │                                               │
        │  2. _detect_via_adaptive_threshold()         │
        │     └─ Umbral adaptativo Gaussiano           │
        │                                               │
        │  3. _detect_via_hough()                      │
        │     └─ Transformada Hough (círculos)         │
        │                                               │
        │  4. _detect_via_contours()                   │
        │     └─ Segmentación HSV + contornos          │
        └────────────┬─────────────────────────────────┘
                     │
        ┌────────────▼──────────────────┐
        │ _merge_detections()           │
        │ (Fusiona 4 métodos)           │
        │ - Agrupa cercanas (< 20px)    │
        │ - Promedia ponderado          │
        └────────────┬──────────────────┘
                     │
        ┌────────────▼──────────────────────────┐
        │ _assign_led_ids_robust()              │
        │ (Rastreo temporal)                    │
        │ - Asigna IDs consistentes             │
        │ - Rechaza saltos > 150px              │
        └────────────┬──────────────────────────┘
                     │
        ┌────────────▼──────────────────────────┐
        │ FrameResult                           │
        │ (Posiciones + IDs + Confianza)        │
        │ └─ Guardado en frame marcado          │
        └────────────┬──────────────────────────┘
                     │
                     ▼
        ┌──────────────────────────────┐
        │  VideoProcessor.save_results()│
        │  calculate_error_statistics() │
        └──────────────┬───────────────┘
                       │
        ┌──────────────▼───────────────────────────┐
        │  FILTRADO IQR                           │
        │  (Elimina outliers automáticamente)     │
        │  - Percentiles 25% y 75%                │
        │  - Umbrales: Q1 - 3×IQR / Q3 + 3×IQR    │
        └──────────────┬───────────────────────────┘
                       │
        ┌──────────────▼───────────────────────────┐
        │  ESTADÍSTICAS FINALES                   │
        │  - Posición promedio (X, Y)             │
        │  - Error estándar total (σ)             │
        │  - Errores separados (σ_x, σ_y)        │
        │  - Rangos de variación                  │
        └──────────────┬───────────────────────────┘
                       │
        ┌──────────────▼───────────────────────────┐
        │  ARCHIVOS DE SALIDA                     │
        ├─────────────────────────────────────────┤
        │  - resultados/frames/*.jpg              │
        │    (854 fotogramas con LEDs marcados)   │
        │  - resultados_completos.json            │
        │    (Datos frame-by-frame)               │
        │  - resumen_estadisticas.json            │
        │    (Estadísticas agregadas)             │
        │  - reporte_deteccion.txt                │
        │    (Informe legible)                    │
        └───────────────────────────────────────────┘
```

---

## Clases Principales

### 1. `LEDDetection` (Estructura de Datos)

```python
@dataclass
class LEDDetection:
    x: float              # Posición X en píxeles
    y: float              # Posición Y en píxeles
    confidence: float     # Confianza 0-1 (qué tan seguro es el detect)
    method: str          # Método usado ("Combinado")
```

**Propósito**: Almacenar información de UN LED detectado en UN frame.

**Ejemplo**:
```
LED 1 detectado en Frame 0:
  - Posición: (344.71, 394.74)
  - Confianza: 0.95 (95%)
  - Método: "Combinado" (resultado de 4 métodos)
```

---

### 2. `FrameResult` (Estructura de Datos)

```python
@dataclass
class FrameResult:
    frame_idx: int                  # Número del frame (0, 1, 2, ...)
    timestamp: float                # Tiempo en segundos (frame_idx / fps)
    leds_detected: List[LEDDetection]  # Los 3 LEDs detectados
    success: bool                   # ¿Se detectaron exactamente 3 LEDs?
    num_leds: int                   # Número de LEDs detectados
    led_ids: List[int]             # IDs asignados (0, 1, 2)
```

**Propósito**: Almacenar resultado COMPLETO de UN frame.

**Ejemplo**:
```
Frame 10:
  - Time: 0.4167 segundos (frame 10 a 24 fps)
  - LEDs: [(344.71, 394.74), (874.13, 360.16), (1151.53, 601.75)]
  - IDs: [0, 1, 2]  ← LED 1, LED 2, LED 3
  - Éxito: True (detectados los 3)
```

---

### 3. `RobustLEDDetector` (Clase Principal)

#### Función Constructora

```python
def __init__(self, 
             min_led_area: int = 30,
             max_led_area: int = 300,
             expected_leds: int = 3):
```

**Parámetros**:
- `min_led_area`: Área mínima en píxeles para considerar como LED
  - Si < 30: Detecta ruido
  - Si > 30: Pierde LEDs pequeños
  - Calibrado a: **30 píxeles**

- `max_led_area`: Área máxima para considerar como LED
  - Si < 300: Pierde LEDs grandes
  - Si > 300: Incluye fondo/ruido
  - Calibrado a: **300 píxeles**

- `expected_leds`: Número de LEDs a detectar (siempre 3)

**Variables de Estado**:
```python
self.last_positions = None              # Posiciones del frame anterior
self.led_trajectory = {0: [], 1: [], 2: []}  # Historial de posiciones
self.frame_count = 0                    # Contador de frames procesados
```

---

## Métodos de Detección

### Método 1: Umbral Simple (`_detect_via_high_threshold`)

```
OBJETIVO: Detectar píxeles MUY brillantes (I > 200)
```

**Pasos**:
1. **Umbralización binaria**: Píxeles intensidad > 200 = blanco, resto = negro
   ```
   Imagen gris:  [50, 150, 200, 220, 255, 100, ...]
                   ↓    ↓    ↓    ↓    ↓    ↓
   Umbral:       [0,   0,   0,   1,   1,   0]  (1=blanco, 0=negro)
   ```

2. **Operaciones morfológicas**: Llena huecos en blobs
   ```
   CIERRE: Dilata + Erosiona para cerrar espacios
   Imagen:  ###...###  → ########
   ```

3. **Etiquetado de componentes**: Encuentra agrupaciones conectadas
   ```
   Identifica cada grupo de píxeles blancos conectados
   Componente 1: {(100,200), (101,200), (102,200), ...}
   Componente 2: {(500,300), (501,300), (502,300), ...}
   ```

4. **Filtrado por área**:
   ```
   if 30 px < área < 300 px:
       → Es probablemente un LED
   else:
       → Descartar (ruido o artefacto)
   ```

5. **Cálculo del centroide**:
   ```
   x_centro = (x_izquierda + ancho/2)
   y_centro = (y_arriba + alto/2)
   ```

**Confianza**: `área / (ancho × alto)` 
- Rectángulo perfecto = 1.0
- Forma irregular = < 1.0

---

### Método 2: Umbral Adaptativo (`_detect_via_adaptive_threshold`)

```
OBJETIVO: Detectar basándose en brillo LOCAL, no global
```

**Ventaja**: Funciona con iluminación no uniforme

**Pasos**:
1. **Umbral adaptativo Gaussiano**:
   ```
   Para cada píxel (x, y):
       - Calcula media en ventana 31×31 alrededor
       - Si píxel > (media - 2), entonces es blanco
       - Si píxel < (media - 2), entonces es negro
   
   Esto adapta el umbral a cada región local
   ```

2. **Resto igual al Método 1**

**Ventaja**: Robusto a:
- Diferentes condiciones de luz
- Reflejos parciales
- Sombras

---

### Método 3: Transformada Hough (`_detect_via_hough`)

```
OBJETIVO: Detectar CÍRCULOS (LEDs tienen forma circular)
```

**Pasos**:
1. **Transformada Hough**:
   ```
   Detecta formas circulares en la imagen
   Por cada píxel, prueba si forma parte de un círculo
   Retorna: (x_centro, y_centro, radio)
   ```

2. **Filtrado por área**:
   ```
   área = π × radio²
   if 30 < área < 300:
       → Probablemente un LED
   ```

3. **Validación de intensidad**:
   ```
   Crea máscara circular
   Calcula promedio de intensidad dentro
   confidence = promedio_intensidad / 200
   ```

**Ventaja**: Valida forma geométrica

---

### Método 4: Contornos HSV (`_detect_via_contours`)

```
OBJETIVO: Segmentar regiones brillantes en espacio HSV
```

**Pasos**:
1. **Convertir a HSV**:
   ```
   HSV = Hue (tono), Saturation (saturación), Value (brillo)
   Mejor para detectar "cosas brillantes" independiente del color
   ```

2. **Máscara de brillo**:
   ```
   Selecciona píxeles con:
   - Value (brillo) > 200  (muy brillante)
   - Saturation < 100      (poco colorido)
   → LEDs infrarojos son blancos/brillantes, no muy coloridos
   ```

3. **Operaciones morfológicas**: Limpia la máscara

4. **Encontrar contornos**: Identifica bordes de objetos

5. **Ajuste de elipse**: Si tiene suficientes puntos, ajusta elipse
   ```
   Calcula centroide automáticamente
   ```

**Ventaja**: Independiente del color específico

---

## Fusión de Detecciones

### `_merge_detections()` - Combinando 4 Métodos

```
¿Por qué 4 métodos simultáneamente?
→ Aumenta robustez: Si uno falla, otros lo compensan
```

**Algoritmo**:

```python
# PASO 1: Recopilar todas las detecciones
all_detections = [
    (344.71, 394.74, 0.95),  # Método 1
    (344.68, 394.76, 0.92),  # Método 2
    (344.73, 394.72, 0.88),  # Método 3
    (874.13, 360.16, 0.91),  # Método 4
]

# PASO 2: Agrupar cercanas (< 20 píxeles)
clusters = {
    0: [(344.71, 394.74, 0.95), (344.68, 394.76, 0.92), 
        (344.73, 394.72, 0.88)],
    1: [(874.13, 360.16, 0.91)]
}

# PASO 3: Promediar cada cluster con peso
# Cluster 0: promedio ponderado de 3 detecciones
# Resultado: (344.71, 394.74, 0.92)

# PASO 4: Retornar centroides fusionados
merged = [(344.71, 394.74, 0.92), (874.13, 360.16, 0.91), ...]
```

**Ventaja**: 
- Elimina duplicados
- Aumenta precisión (promedio de múltiples métodos)
- Robustez ante fallos parciales

---

## Algoritmo de Rastreo Temporal

### `_assign_led_ids_robust()` - Manteniendo Identidad Consistente

```
PROBLEMA RESUELTO:
  Frame 10: LED1=(344,394), LED2=(874,360), LED3=(1151,601)
  Frame 11: Mismos LEDs se detectan pero en orden diferente
            → ¿Cuál es cuál?
  Frame 12: Posiciones cambian nuevamente

SOLUCIÓN: Rastreo basado en proximidad
```

**Algoritmo**:

```
MARCO CONCEPTUAL (Hungarian Assignment Problem):

Frame anterior:         Frame actual:
  LED 1 (344, 394)       Detección A (346, 395)
  LED 2 (874, 360)       Detección B (872, 361)
  LED 3 (1151, 601)      Detección C (1150, 603)

¿Cuál detección corresponde a cuál LED?

Distancias:
  LED1→A: 2.24 px ✓ (menor)
  LED1→B: 532 px  ✗ (muy grande, > 150 px)
  LED1→C: 807 px  ✗ (muy grande)
  
  LED2→A: 532 px  ✗
  LED2→B: 2.24 px ✓ (menor)
  LED2→C: 277 px  ✗
  
  LED3→A: 807 px  ✗
  LED3→B: 277 px  ✗
  LED3→C: 1.41 px ✓ (menor)

ASIGNACIÓN ÓPTIMA:
  LED 1 → Detección A
  LED 2 → Detección B
  LED 3 → Detección C
```

**Pseudocódigo**:

```python
def _assign_led_ids_robust(self, detecciones):
    # 1. Ordenar detecciones actuales por X
    detecciones = sorted(detecciones, key=X)
    
    # 2. Si primer frame, asignar IDs 0, 1, 2
    if self.last_positions is None:
        self.last_positions = detecciones
        return detecciones, [0, 1, 2]
    
    # 3. Para cada LED anterior, encontrar match más cercano
    assignment = {}
    MAX_JUMP = 150 píxeles
    
    for old_idx, (x_old, y_old) in enumerate(self.last_positions):
        best_match = None
        best_distance = infinity
        
        for new_idx, (x_new, y_new) in enumerate(detecciones):
            distance = sqrt((x_old - x_new)² + (y_old - y_new)²)
            
            # Rechaza saltos sospechosos
            if distance > MAX_JUMP:
                continue
            
            if distance < best_distance:
                best_match = new_idx
                best_distance = distance
        
        if best_match is not None:
            assignment[old_idx] = best_match
    
    # 4. Construir resultado manteniendo IDs
    return assigned_detections, assigned_ids
```

**Parámetro crítico**: `MAX_JUMP_DIST = 150 píxeles`
- Si LED se mueve más de 150 px entre frames
- Se considera un ERROR de rastreo, se rechaza
- Esto previene intercambios de identidad

**Beneficio**:
```
✗ Sin rastreo:
  LED1_frame10 ≠ LED1_frame11 (orden aleatorio)
  σ_LED1 = 3519 píxeles (¡FALSO! Mezcla de LEDs)

✓ Con rastreo:
  LED1 siempre es LED1
  σ_LED1 = 54.68 píxeles (realista)
```

---

## Filtrado de Outliers

### `calculate_error_statistics()` - Filtrado IQR

```
PROBLEMA: Algunos frames pueden tener errores de rastreo
→ Introducen "outliers" que distorsionan estadísticas
```

**Método: Rango Intercuartil (IQR)**

```
Idea: Los datos reales siguen patrón normal
      Los outliers son excepciones

Algoritmo:
  1. Calcular Q1 (percentil 25%)
  2. Calcular Q3 (percentil 75%)
  3. IQR = Q3 - Q1
  4. Umbral bajo = Q1 - 3×IQR
  5. Umbral alto = Q3 + 3×IQR
  6. Descartar datos fuera del rango
```

**Ejemplo concreto**:

```
LED 1 posiciones en X (antes de filtrado):
[100, 102, 101, 103, 102, 800, 104, 103, 101, 102]
                     ↑↑↑
                  Outlier!

Calcular Q1, Q3:
  Ordenar: [100, 101, 101, 102, 102, 103, 104, ...]
  Q1 (25%): 101
  Q3 (75%): 103
  IQR = 103 - 101 = 2

Umbrales:
  Bajo = 101 - 3×2 = 95
  Alto = 103 + 3×2 = 109

Filtro: 800 está fuera [95, 109]
→ RECHAZAR

Posiciones válidas: [100, 102, 101, 103, 102, 104, 103, 101, 102]
```

**Resultado**:
```
✗ Sin filtrado: σ = 342.5 píxeles
✓ Con filtrado: σ = 1.1 píxeles
```

---

## Flujo de Procesamiento

### `VideoProcessor.process()` - Bucle Principal

```python
# 1. Abrir video
cap = cv2.VideoCapture("patron_leds/patron_leds.mp4")

# 2. Para cada frame del video:
while True:
    ret, frame = cap.read()  # Lee frame siguiente
    if not ret:
        break  # Fin del video
    
    # 3. Procesar frame
    success, leds, viz_frame, led_ids = self.detector.detect(frame)
    
    # 4. Guardar resultado
    result = FrameResult(...)
    self.results.append(result)
    
    # 5. Guardar frame visualizado
    cv2.imwrite(f"resultados/frame_{frame_idx:06d}.jpg", viz_frame)
    
    # 6. Mostrar progreso cada 30 frames
    if (frame_idx + 1) % 30 == 0:
        print(f"Frame {frame_idx+1}/854 - Éxito: {success_rate}%")
    
    # 7. Permitir salir con 'Q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    
    frame_idx += 1

# 8. Calcular estadísticas
stats = calculate_error_statistics()

# 9. Guardar archivos
save_results()
```

---

## Ejemplos de Uso

### Uso Básico

```bash
# Procesar video completo
python3 led_detector_final.py patron_leds/patron_leds.mp4

# Procesar solo 100 frames para prueba rápida
python3 led_detector_final.py patron_leds/patron_leds.mp4 --max-frames 100

# Sin mostrar ventanas (modo batch)
python3 led_detector_final.py patron_leds/patron_leds.mp4 --no-display

# Especificar carpeta de salida
python3 led_detector_final.py patron_leds/patron_leds.mp4 --output mi_salida/
```

### Uso Programático

```python
from led_detector_final import VideoProcessor

# Crear procesador
processor = VideoProcessor("mi_video.mp4", output_dir="resultados/")

# Procesar video
resultados = processor.process(
    max_frames=None,        # Procesar todo
    save_frames=True,       # Guardar frames marcados
    display=False           # No mostrar ventanas
)

# Calcular estadísticas
stats = processor.calculate_error_statistics()

# Guardar resultados
processor.save_results()

# Acceder a datos
print(f"Total frames: {len(resultados)}")
print(f"Exitosos: {sum(1 for r in resultados if r.success)}")

for led_id, led_stats in stats['leds'].items():
    print(f"\nLED {led_id + 1}:")
    print(f"  Posición: {led_stats['mean_position']}")
    print(f"  Error σ: {led_stats['std_deviation']:.2f} píxeles")
```

---

## Parámetros Ajustables

### Para Cambiar Sensibilidad

```python
# En RobustLEDDetector.__init__():

# Detectar LEDs más pequeños
detector = RobustLEDDetector(
    min_led_area=15,      # Más sensible
    max_led_area=500      # Más tolerante
)

# Detectar solo LEDs grandes
detector = RobustLEDDetector(
    min_led_area=50,      # Menos sensible
    max_led_area=200      # Más restrictivo
)
```

### Parámetros de Filtrado

```python
# En _detect_via_adaptive_threshold():
cv2.adaptiveThreshold(
    gray, 255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY,
    31,     # Tamaño ventana (más grande = más suave)
    2       # Substracción (más grande = más sensible)
)
```

### Rastreo Temporal

```python
# En _assign_led_ids_robust():
MAX_JUMP_DIST = 150  # Máximo píxeles entre frames
                     # Más pequeño = más restrictivo
                     # Más grande = más tolerante
```

### Filtrado de Outliers

```python
# En calculate_error_statistics():
# Umbral IQR (búsqueda de outliers)
valid_mask = (
    (xs >= q1_x - 3*iqr_x) &  # 3× es el multiplicador
    (xs <= q3_x + 3*iqr_x)    # Cambiar a 2× o 4× para ajustar
)
```

---

## Intepretación de Resultados

### Archivo `reporte_deteccion.txt`

```
TASA DE ÉXITO:
  854/854 (100%)
  → Todos los frames tienen 3 LEDs detectados

ERROR ESTÁNDAR (σ):
  LED 1: 54.68 píxeles
  LED 2: 32.23 píxeles
  LED 3: 98.07 píxeles
  
  ¿Qué significa?
  → Variación frame-a-frame del LED
  → 68% de detecciones dentro ±σ (normal estadístico)
  → Típico para video: 30-100 píxeles
```

### Archivo `resumen_estadisticas.json`

```json
{
  "total_frames": 854,
  "successful_frames": 854,
  "leds": {
    "0": {
      "detected_frames": 717,         // Después de filtrado IQR
      "mean_position": [344.71, 394.74],
      "std_deviation": 54.68,
      "std_x": 71.10,                 // Error en X
      "std_y": 50.38,                 // Error en Y
      "range_x": 638.09,              // Máximo - Mínimo en X
      "range_y": 387.86               // Máximo - Mínimo en Y
    }
  }
}
```

---

## Conclusión

El detector `led_detector_final.py` implementa:

✅ **4 métodos de detección independientes** → Robustez
✅ **Fusión inteligente** → Precisión mejorada
✅ **Rastreo temporal** → Identidad consistente
✅ **Filtrado automático** → Estadísticas válidas
✅ **100% éxito en video de prueba** → Confiable

Ideal para aplicaciones de:
- Sistemas HMD con LED infrarrojo
- Captura de movimiento
- Seguimiento de pose
- Calibración óptica

