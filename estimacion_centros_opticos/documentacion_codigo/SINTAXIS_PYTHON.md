# 🐍 Guía de Sintaxis Python - Para Entender el Código

Esta guía explica los conceptos de Python usados en `led_detector_final.py` para que puedas entender y modificar el código.

---

## 1. Dataclasses (`@dataclass`)

```python
@dataclass
class LEDDetection:
    x: float
    y: float
    confidence: float
    method: str
```

**¿Qué es?**: Una forma moderna de crear "estructuras de datos" en Python.

**Equivalente antiguo (sin dataclass)**:
```python
# Versión antigua y tediosa:
class LEDDetection:
    def __init__(self, x, y, confidence, method):
        self.x = x
        self.y = y
        self.confidence = confidence
        self.method = method
```

**Con dataclass** (automático):
```python
# Versión moderna: el decorator genera __init__ automáticamente
@dataclass
class LEDDetection:
    x: float
    y: float
    confidence: float
    method: str
```

**Uso**:
```python
# Crear instancia
led1 = LEDDetection(x=344.71, y=394.74, confidence=0.95, method="Combinado")

# Acceder
print(led1.x)           # 344.71
print(led1.confidence)  # 0.95

# Convertir a diccionario
print(vars(led1))
# {'x': 344.71, 'y': 394.74, 'confidence': 0.95, 'method': 'Combinado'}
```

---

## 2. Type Hints (Anotaciones de Tipo)

```python
def _preprocess(self, frame: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
                        ↑                     ↑
                    Input type            Output type
```

**¿Qué es?**: Documentación sobre qué tipos de datos espera/retorna una función.

**Ejemplos**:
```python
def calculate_distance(x1: float, y1: float) -> float:
    """Calcula distancia desde origen"""
    return (x1**2 + y1**2) ** 0.5

# Correcto
result = calculate_distance(3.0, 4.0)  # ✓ retorna float (5.0)

# Python NO lo previene, pero el IDE sí:
result = calculate_distance("3", "4")  # ⚠ IDE avisa que tipo incorrecto
```

**Tipos comunes**:
```python
int                           # Entero
float                         # Decimal
str                          # Texto
bool                         # Booleano (True/False)
List[int]                    # Lista de enteros
Dict[str, float]             # Diccionario {texto: decimal}
Tuple[int, int, float]       # Tupla (x, y, confianza)
Optional[np.ndarray]         # Puede ser ndarray o None
```

---

## 3. List Comprehensions (Comprensión de Listas)

```python
# Versión larga (tradicional)
leds = []
for i in range(1, num_labels):
    area = stats[i, cv2.CC_STAT_AREA]
    if 30 < area < 300:
        leds.append((x, y, conf))

# Versión corta (list comprehension)
leds = [(x, y, conf) for i in range(1, num_labels) if 30 < area < 300]
```

**¿Cuándo usarla?**:
```python
# Transformar lista
numbers = [1, 2, 3, 4, 5]
squared = [n**2 for n in numbers]
# squared = [1, 4, 9, 16, 25]

# Filtrar
even = [n for n in numbers if n % 2 == 0]
# even = [2, 4]

# Combinar transformación + filtro
big_even_squared = [n**2 for n in numbers if n % 2 == 0 and n > 2]
# big_even_squared = [16, 25]
```

---

## 4. Dictionary (Diccionarios)

```python
# Crear
stats = {
    'total_frames': 854,
    'leds': {
        0: {'mean_position': [344.71, 394.74]},
        1: {'mean_position': [874.13, 360.16]},
        2: {'mean_position': [1151.53, 601.75]}
    }
}

# Acceder
stats['total_frames']                    # 854
stats['leds'][0]['mean_position']        # [344.71, 394.74]

# Iterar
for led_idx, led_data in stats['leds'].items():
    print(f"LED {led_idx}: {led_data['mean_position']}")

# Actualizar
stats['total_frames'] = 900
stats['leds'][0]['processed'] = True
```

---

## 5. NumPy Arrays

```python
import numpy as np

# Crear
arr = np.array([1, 2, 3, 4, 5])

# Operaciones
mean = np.mean(arr)                 # Promedio: 3
std = np.std(arr)                   # Desviación estándar
max_val = np.max(arr)               # Máximo: 5

# 2D (matriz)
matrix = np.array([[1, 2], [3, 4]])
matrix[0, 0]                        # Primera fila, primera columna: 1
matrix[0]                           # Primera fila: [1, 2]
matrix[:, 0]                        # Primera columna: [1, 3]

# Operaciones booleanas (mask)
arr = np.array([1, 2, 3, 100, 5])
mask = arr < 50                     # [True, True, True, False, True]
filtered = arr[mask]                # [1, 2, 3, 5] (sin 100)
```

---

## 6. Tuplas vs Listas

```python
# LISTA: modificable
lista = [1, 2, 3]
lista[0] = 10           # ✓ Permitido
lista.append(4)         # ✓ Permitido

# TUPLA: inmutable (no se puede cambiar)
tupla = (1, 2, 3)
tupla[0] = 10           # ✗ Error: TypeError
tupla.append(4)         # ✗ Error: no tiene método append

# PERO... tupla puede desempaquetarse
x, y, z = tupla         # ✓ x=1, y=2, z=3

# Retornar múltiples valores (tupla implícita)
def get_coordinates():
    return 344.71, 394.74  # Retorna tupla (344.71, 394.74)

x, y = get_coordinates()  # Desempaquetar automáticamente
```

---

## 7. Diccionarios y Listas Anidadas

```python
# Estructura compleja
led_trajectory = {
    0: [(344.71, 394.74), (344.73, 394.76), (344.68, 394.72)],  # LED 1
    1: [(874.13, 360.16), (874.15, 360.17)],                     # LED 2
    2: [(1151.53, 601.75)]                                        # LED 3
}

# Acceder
first_position_led_1 = led_trajectory[0][0]     # (344.71, 394.74)
x = led_trajectory[0][0][0]                     # 344.71

# Agregar
led_trajectory[0].append((344.70, 394.77))

# Iterar
for led_id, positions in led_trajectory.items():
    print(f"LED {led_id} tiene {len(positions)} posiciones")
```

---

## 8. Lambda (Funciones Inline)

```python
# Versión larga
def sort_key(detection):
    return detection[0]  # Ordenar por X

detections.sort(key=sort_key)

# Versión corta con lambda
detections.sort(key=lambda d: d[0])  # Mismo resultado, 1 línea

# Otro ejemplo: ordenar por confianza (descendente)
sorted_by_conf = sorted(detections, key=lambda d: d[2], reverse=True)
```

---

## 9. Operadores Lógicos

```python
# AND: Ambas condiciones deben ser True
if min_led_area < area < max_led_area:  # Lo mismo que:
if area > min_led_area and area < max_led_area:
    print("Área válida")

# OR: Al menos una condición debe ser True
if frame_idx == 0 or frame_idx == last_frame:
    print("Es primer o último frame")

# NOT: Invierte la condición
if not success:                    # Si success = False
    print("Fallo la detección")
```

---

## 10. Slicing (Cortes de Secuencias)

```python
arr = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

# Básico
arr[0]              # 0 (primer elemento)
arr[-1]             # 9 (último elemento)
arr[1:4]            # [1, 2, 3] (desde 1 hasta 3, sin incluir 4)
arr[:5]             # [0, 1, 2, 3, 4] (desde el inicio hasta 4)
arr[5:]             # [5, 6, 7, 8, 9] (desde 5 hasta final)
arr[::2]            # [0, 2, 4, 6, 8] (cada 2 elementos)
arr[::-1]           # [9, 8, 7, 6, ...] (invertido)

# Matriz 2D (NumPy)
matrix = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
matrix[0]           # [1, 2, 3] (primera fila)
matrix[:, 0]        # [1, 4, 7] (primera columna)
matrix[0, 2]        # 3 (fila 0, columna 2)
```

---

## 11. f-strings (Formato de Texto)

```python
# Antiguo
print("Frame " + str(frame_idx) + " de " + str(total_frames))

# Moderno (f-string)
print(f"Frame {frame_idx} de {total_frames}")

# Con formato
x, y = 344.71, 394.74
print(f"LED en ({x:.2f}, {y:.2f})")  # LED en (344.71, 394.74)

# Expresiones dentro
rate = 100.0
print(f"Éxito: {rate:.1f}%")  # Éxito: 100.0%
```

---

## 12. Métodos Comunes

```python
# LISTA
lista = [3, 1, 2]
lista.append(4)         # Agregar: [3, 1, 2, 4]
lista.sort()            # Ordenar: [1, 2, 3, 4]
lista.reverse()         # Invertir: [4, 3, 2, 1]
len(lista)              # Largo: 4

# DICCIONARIO
d = {'a': 1, 'b': 2}
d['c'] = 3              # Agregar nueva clave
d.keys()                # dict_keys(['a', 'b', 'c'])
d.values()              # dict_values([1, 2, 3])
d.items()               # dict_items([('a', 1), ('b', 2), ('c', 3)])

# NUMPY
arr = np.array([1, 2, 3])
arr.shape               # (3,)
arr.dtype               # dtype('int64')
arr.max()               # 3
arr.min()               # 1
```

---

## 13. Operador Ternario

```python
# Versión larga
if success:
    message = "Detectados 3 LEDs"
else:
    message = "Error: detectados < 3"

# Versión corta (ternario)
message = "Detectados 3 LEDs" if success else "Error: detectados < 3"

# Uso en el código
confidence = min(1.0, area / bbox_area) if bbox_area > 0 else 0.5
```

---

## 14. `self` en Clases

```python
class RobustLEDDetector:
    def __init__(self):
        self.min_led_area = 30      # Atributo de instancia
    
    def detect(self, frame):
        # self se refiere a la instancia actual
        print(f"Área mínima: {self.min_led_area}")
        self.frame_count += 1        # Modificar atributo

# Crear instancia
detector = RobustLEDDetector()
detector.detect(frame)  # 'self' apunta a 'detector'
```

---

## 15. Args y Kwargs

```python
def process(self, max_frames=None, save_frames=True, display=True):
    # max_frames, save_frames, display son argumentos con VALORES POR DEFECTO
    pass

# Llamadas equivalentes
processor.process()                                  # Usa todos los defaults
processor.process(max_frames=100)                   # Cambia max_frames
processor.process(max_frames=100, display=False)    # Cambia dos parámetros
```

---

## 16. Operador `*` en NumPy

```python
import numpy as np

# Elemento a elemento
a = np.array([1, 2, 3])
b = np.array([2, 2, 2])

a * b                   # [2, 4, 6] (multiplicación elemento a elemento)
a ** 2                  # [1, 4, 9] (potencia elemento a elemento)

# Matriz
matrix = np.array([[1, 2], [3, 4]])
matrix * 2              # [[2, 4], [6, 8]] (cada elemento × 2)
matrix ** 2             # [[1, 4], [9, 16]]
```

---

## 17. Operador `@` (Decoradores)

```python
# Sin decorador
def my_function():
    print("Hola")

# Con decorador
@dataclass
class MyClass:
    x: int
    y: int

# El decorador modifica la clase/función después de definirla
# @dataclass automáticamente genera __init__, __repr__, etc.
```

---

## 18. Imports y Módulos

```python
# Importar todo
import cv2
cv2.imread(...)         # Usar con prefijo

# Importar específico
from pathlib import Path
Path('mi/ruta')         # Usar directamente

# Importar con alias
import numpy as np
np.array([1, 2, 3])

# Type hints
from typing import List, Dict, Tuple, Optional
def func(a: List[int]) -> Dict[str, float]:
    pass
```

---

## 19. Try-Except (Manejo de Errores)

```python
try:
    result = 10 / 0  # Error: división por cero
except ZeroDivisionError:
    print("No puedes dividir por cero")

# Versión con múltiples errores
try:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"No se puede abrir: {video_path}")
except ValueError as e:
    print(f"Error: {e}")
```

---

## 20. Context Managers (`with`)

```python
# Versión antigua (riesgosa)
f = open('archivo.txt')
contenido = f.read()
f.close()  # ¿Y si falla antes de llegar aquí?

# Versión moderna (segura)
with open('archivo.txt') as f:
    contenido = f.read()
# El archivo se cierra automáticamente

# Lo mismo con JSON
import json
with open('datos.json') as f:
    data = json.load(f)  # Se cierra automáticamente
```

---

## Referencia Rápida

| Concepto | Ejemplo |
|----------|---------|
| **Dataclass** | `@dataclass class MyClass: x: int` |
| **Type hints** | `def func(x: int) -> str:` |
| **List comp** | `[x**2 for x in arr if x > 0]` |
| **Dict** | `{'key': value, 'key2': value2}` |
| **NumPy** | `np.array([1, 2, 3])` |
| **Lambda** | `sorted(arr, key=lambda x: x[0])` |
| **f-string** | `f"Valor: {variable:.2f}"` |
| **Slicing** | `arr[1:5]`, `arr[::2]` |
| **Ternario** | `x if condition else y` |
| **Decorador** | `@dataclass` |

---

¡Ahora puedes leer y entender `led_detector_final.py`! 🎓

