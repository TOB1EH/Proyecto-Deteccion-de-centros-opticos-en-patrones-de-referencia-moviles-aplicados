# 📑 Índice Rápido del Proyecto

## 🎯 Comienza aquí

Si es tu **PRIMERA VEZ** leyendo sobre este proyecto, sigue este orden:

```
1️⃣  GUIA_RAPIDA.md (10 min)
    👉 Entiende qué hace el proyecto en términos simples
    └─ Diagramas ASCII, explicaciones claras
    
2️⃣  SINTAXIS_PYTHON.md (15 min, opcional)
    👉 Si no entiendes Python, lee esto primero
    └─ 20 conceptos explicados con ejemplos
    
3️⃣  MAPA_MENTAL.md (5 min)
    👉 Visión estructural del proyecto
    └─ Diagrama general, flujos, conceptos clave
    
4️⃣  led_detector_final.py (20 min)
    👉 Lee el código comentado
    └─ Cada función está explicada línea por línea
    
5️⃣  DOCUMENTACION_CODIGO.md (30 min)
    👉 Profundiza en los algoritmos
    └─ Rastreo temporal, filtrado IQR, etc.
```

---

## 📚 Por Tema

### Entender la Idea General
- 📄 **GUIA_RAPIDA.md** - Explicación ejecutiva
- 📄 **MAPA_MENTAL.md** - Estructura visual

### Aprender Python Usado
- 📄 **SINTAXIS_PYTHON.md** - 20 conceptos clave
- 🐍 **led_detector_final.py** - Código comentado

### Entender Algoritmos Técnicos
- 📄 **DOCUMENTACION_CODIGO.md** - Arquitectura detallada
- 🔬 Secciones:
  - "Métodos de Detección"
  - "Algoritmo de Rastreo Temporal"
  - "Filtrado de Outliers"

### Ver Resultados
- 📊 **resultados/resumen_estadisticas.json** - Datos agregados
- 📄 **resultados/reporte_deteccion.txt** - Informe legible
- 🖼️ **resultados/frames/*.jpg** - 854 frames visualizados

---

## 🔍 Buscar Específico

### "¿Cuál archivo uso?"
→ **led_detector_final.py** (único archivo de producción)

### "¿Cómo funcionan los 4 métodos?"
→ **GUIA_RAPIDA.md**, sección "4 MÉTODOS EXPLICADOS EN SIMPLE"

### "¿Cómo mantiene los IDs consistentes?"
→ **DOCUMENTACION_CODIGO.md**, sección "Algoritmo de Rastreo Temporal"

### "¿Qué son dataclasses?"
→ **SINTAXIS_PYTHON.md**, sección 1 "Dataclasses"

### "¿Cómo modifi parámetros?"
→ **GUIA_RAPIDA.md**, sección "AJUSTES SI NECESITAS CAMBIAR ALGO"

### "¿Qué significan los números de error?"
→ **DOCUMENTACION_CODIGO.md**, sección "Intepretación de Resultados"

### "¿Cómo funciona el filtrado IQR?"
→ **GUIA_RAPIDA.md**, sección "FILTRADO DE OUTLIERS"

### "¿Qué archivos puedo eliminar?"
→ Esta misma página, abajo

---

## ✅ Checklist de Lectura

- [ ] GUIA_RAPIDA.md (10 minutos)
- [ ] Uno de: SINTAXIS_PYTHON.md O led_detector_final.py (20 minutos)
- [ ] MAPA_MENTAL.md (5 minutos)
- [ ] DOCUMENTACION_CODIGO.md (30 minutos, opcional)

**Tiempo mínimo para entender**: 15 minutos (GUIA_RAPIDA.md)
**Tiempo para experto**: 60 minutos (todo)

---

## 🗑️ Archivos a Eliminar (Desarrollo Antiguo)

```bash
# Estos archivos eran pasos intermedios, ya NO son necesarios
rm led_detector_mejorado.py       # Prototipo inicial
rm led_detector_calibrado.py      # Intermedio
rm led_detector_stable.py         # Intermedio
rm led_detector_v1.py             # Versión vieja
rm led_detector_v2.py             # Versión vieja
```

**Archivos a MANTENER:**
```bash
✓ led_detector_final.py           # Producción
✓ diagnostic.py                   # Auxiliar (opcional)
✓ *.md (documentación)            # Todos los MD
✓ run.sh                          # Script shell
```

---

## 📞 Guía de Referencia Rápida

| Pregunta | Respuesta Rápida |
|----------|-----------------|
| ¿Cuál archivo uso? | `led_detector_final.py` |
| ¿Tasa de éxito? | 100% (854/854 frames) |
| ¿Por qué 4 métodos? | Robustez: si uno falla, otros 3 funcionan |
| ¿Qué es rastreo? | Mantiene IDs LED1, LED2, LED3 consistentes |
| ¿Qué es IQR? | Método para eliminar outliers automáticamente |
| ¿Error promedio? | 32-98 píxeles (muy normal para video) |
| ¿Cuántos frames? | 854 procesados exitosamente |
| ¿Cómo ejecutar? | `python3 led_detector_final.py video.mp4` |
| ¿Dónde están resultados? | Carpeta `resultados/` |
| ¿Cómo modificar? | Cambia parámetros en `RobustLEDDetector.__init__()` |

---

## 🎓 Nivel de Dificultad

### Fácil (Entender idea general)
- GUIA_RAPIDA.md ⭐ Comienza aquí
- MAPA_MENTAL.md
- RESULTADOS_FINALES.md

### Intermedio (Entender algoritmos)
- DOCUMENTACION_CODIGO.md
- led_detector_final.py (código comentado)

### Avanzado (Modificar/Extender)
- SINTAXIS_PYTHON.md (si no sabes Python)
- Modificar parámetros
- Agregar nuevos métodos de detección

---

## 🚀 Flujo de Trabajo

### Si Quieres USAR el código:
1. Lee GUIA_RAPIDA.md (5 min)
2. Ejecuta: `python3 led_detector_final.py tu_video.mp4`
3. Ve resultados en `resultados/`

### Si Quieres ENTENDER el código:
1. Lee GUIA_RAPIDA.md (10 min)
2. Lee MAPA_MENTAL.md (5 min)
3. Lee led_detector_final.py (20 min)
4. Lee DOCUMENTACION_CODIGO.md (30 min)

### Si Quieres MODIFICAR el código:
1. Lee SINTAXIS_PYTHON.md (si no sabes Python)
2. Identifica qué quieres cambiar
3. Encuentra en DOCUMENTACION_CODIGO.md
4. Lee la sección relevante
5. Modifica en led_detector_final.py
6. Prueba con `--max-frames 10` para test rápido

---

## 📊 Archivos por Tipo

### 🐍 Python (Código)
- `led_detector_final.py` ⭐ - Producción (USA ESTE)
- `diagnostic.py` - Herramienta auxiliar

### 📄 Markdown (Documentación)
- `GUIA_RAPIDA.md` ⭐ - Empezar aquí
- `DOCUMENTACION_CODIGO.md` - Técnico
- `SINTAXIS_PYTHON.md` - Referencia Python
- `MAPA_MENTAL.md` - Visual
- `RESULTADOS_FINALES.md` - Resultados

### 📁 Carpetas
- `resultados/` - Salida del programa
  - `frames/` - 854 JPG con LEDs
  - `*.json` - Datos estructurados
  - `*.txt` - Reporte legible
- `patron_leds/` - Video de entrada

---

## ⚡ Comandos Útiles

```bash
# Ejecutar detector
python3 led_detector_final.py patron_leds/patron_leds.mp4

# Con opciones
python3 led_detector_final.py video.mp4 --output mi_salida/ --max-frames 100

# Ver resultados
cat resultados/reporte_deteccion.txt

# Ver JSON
python3 -m json.tool resultados/resumen_estadisticas.json | less

# Ver frame específico
display resultados/frames/frame_000010.jpg

# Contar frames
ls resultados/frames/ | wc -l
```

---

## 💡 Pro Tips

1. **Para test rápido:** Usa `--max-frames 50` para procesar solo 50 frames
2. **Para otro video:** Primero usa `diagnostic.py` para analizar
3. **Para cambiar parámetros:** Solo edita `RobustLEDDetector.__init__()`
4. **Para debug:** Mira `DOCUMENTACION_CODIGO.md`, sección de algoritmo
5. **Para entender error:** Lee `resultados/reporte_deteccion.txt`

---

## 🎯 Objetivo Alcanzado

✅ **Sistema funcional**: Detección 100% exitosa
✅ **Bien documentado**: ~15,000 palabras en documentación
✅ **Fácil de entender**: Múltiples niveles de explicación
✅ **Listo para producción**: Código robusto y testeado
✅ **Modificable**: Parámetros claramente documentados

---

**¿Preguntas? Revisa el índice arriba o abre los archivos MD correspondientes.**

**Última actualización:** 23 de octubre de 2025
**Versión:** Final v1.0
**Estado:** Completamente documentado ✅

