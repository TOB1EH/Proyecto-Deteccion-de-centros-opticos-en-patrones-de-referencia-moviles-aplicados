# Etapa 2: Detección de LEDs con Filtro de Kalman

## Resumen Ejecutivo

Se implementó un detector de LEDs con validación geométrica estricta y filtro de Kalman para suavizado de trayectorias.

### Resultados Principales

| Métrica | Valor |
|---------|-------|
| **Tasa de detección** | 87.0% (743/854 frames) |
| **Error de colinealidad** | 0.68px ± 0.47px |
| **Colinealidad máxima** | 4.87px |
| **Ratio de espaciamiento** | 1.052 ± 0.045 |

## Problema Identificado en Etapa 1

El detector original (`led_detector_final.py`) reportaba 100% de éxito, pero un análisis detallado reveló:

- **Falsos positivos**: Encontraba "3 puntos brillantes" que NO eran los LEDs reales
- **Errores de colinealidad**: Hasta 238px (cuando debería ser <5px)
- **Ratios de distancia**: 1.4-1.8 (cuando debería ser ~1.0 para LEDs equidistantes)

El detector encontraba *cualquier* 3 puntos brillantes, sin validar que formaran el patrón geométrico conocido.

## Solución: Detector Estricto (v3.0)

### Filosofía
> "Mejor NO detectar que detectar MAL"

### Restricciones Geométricas

```
Patrón de LEDs:    ●————●————●
                   L1   L2   L3
                   
Restricciones:
  - Colinealidad: < 5.0px (error perpendicular a la línea)
  - Equiespaciamiento: ratio d12/d23 entre 0.90 y 1.10
  - Distancia entre LEDs: 50-400px
```

### Algoritmo

1. **Detección de candidatos**: Umbral adaptativo (percentil 95 de brillo)
2. **Búsqueda exhaustiva**: Evalúa TODAS las combinaciones de 3 blobs
3. **Validación geométrica**: Rechaza tripletes que no cumplan restricciones
4. **Selección óptima**: Si hay múltiples válidos, elige el de menor error
5. **Suavizado Kalman**: Filtra ruido de alta frecuencia en posiciones

### Filtro de Kalman

```
Estado: [x, y, vx, vy]  (posición + velocidad)
Modelo: Velocidad constante
Ruido de proceso (Q): 1.0 (permite cambios moderados de velocidad)
Ruido de medición (R): 5.0 (incertidumbre de detección ~5px)
```

## Análisis de Resultados

### Frames Sin Detección (13%)

Los 111 frames sin patrón válido corresponden a:

1. **LEDs cerca del borde**: Cuando el casco está en el extremo de la imagen
2. **LEDs fusionados**: A ciertas distancias, los LEDs aparecen como un blob
3. **Muchos reflejos**: Frames con 16+ blobs brillantes dificultan la selección

### Jitter (Variación Frame-a-Frame)

| LED | Media | Mediana | Máximo |
|-----|-------|---------|--------|
| LED1 | 85.1px | 22.8px | 445.3px |
| LED2 | 54.8px | 18.6px | 298.4px |
| LED3 | 43.9px | 16.9px | 227.4px |

**Interpretación**:
- La **mediana** (17-23px) representa el movimiento típico del casco
- La **media** alta refleja movimientos bruscos ocasionales
- Los **máximos** corresponden a saltos después de frames sin detección

### Posición del Patrón

```
Centro del patrón (primeros 100 frames):
  X: 735.5 ± 46.8px
  Y: 348.4 ± 58.6px
```

El casco se mueve ~50px en cada dirección durante la grabación.

## Archivos Generados

```
resultados_estricto_full/
├── resultados.json      # Datos completos (posiciones, métricas)
├── reporte.txt          # Resumen estadístico
├── video_deteccion.mp4  # Visualización (300 frames)
└── frames/              # Imágenes cada 20 frames
```

## Comparación con Etapa 1

| Aspecto | Etapa 1 | Etapa 2 |
|---------|---------|---------|
| Tasa de "éxito" | 100% | 87% |
| Falsos positivos | Alto (238px colinealidad) | Bajo (<5px) |
| Validación geométrica | No | Sí (estricta) |
| Filtrado temporal | No | Kalman |
| Confianza en resultados | Baja | Alta |

## Código Principal

```python
# Archivo: led_detector_estricto.py

class StrictLEDDetector:
    """Detecta LEDs solo si cumplen geometría del patrón."""
    
    def __init__(self, max_collinearity_error=5.0, spacing_tolerance=0.10):
        self.max_collinearity_error = max_collinearity_error
        self.spacing_tolerance = spacing_tolerance
        self.trackers = {}  # Kalman por LED
    
    def detect(self, frame):
        blobs = self._find_bright_blobs(frame)
        triplet = self._find_best_triplet(blobs)  # Busca combinación válida
        
        if triplet is None:
            return False, [], inf, inf  # Rechaza frame
        
        # Suaviza con Kalman
        leds = []
        for i, (x, y, conf) in enumerate(triplet):
            if i not in self.trackers:
                self.trackers[i] = KalmanTracker(x, y)
            smoothed_x, smoothed_y = self.trackers[i].update(x, y)
            leds.append(LEDDetection(smoothed_x, smoothed_y, conf, i))
        
        return True, leds, collinearity_error, spacing_ratio
```

## Próximos Pasos

1. **Mejorar tasa de detección**: 
   - Ajustar umbrales para frames difíciles
   - Considerar detección multi-escala

2. **Integrar predicción Kalman**:
   - Usar predicción cuando no hay detección
   - Validar predicción contra geometría

3. **Análisis de pose**:
   - Usar posiciones de LEDs para estimar orientación del casco
   - Calcular ángulos de cabeceo/guiñada/balanceo

## Conclusión

El detector estricto sacrifica tasa de detección (87% vs 100%) a cambio de **confiabilidad**. Las detecciones reportadas son geométricamente correctas (colinealidad <5px, equiespaciamiento 0.9-1.1), eliminando los falsos positivos del detector original.

---
*Fecha: Diciembre 2025*
*Autor: Tobias Funes*
