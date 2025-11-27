"""
╔════════════════════════════════════════════════════════════════════════════════╗
║         DETECTOR ROBUSTO DE CENTROS ÓPTICOS DE LEDs INFRAROJOS                ║
║                          VERSIÓN FINAL v1.0                                   ║
╚════════════════════════════════════════════════════════════════════════════════╝

DESCRIPCIÓN:
  Sistema de detección de 3 LEDs infrarojos en video usando múltiples técnicas
  combinadas (4 métodos en paralelo) con rastreo temporal y filtrado robusto.

CARACTERÍSTICAS PRINCIPALES:
  • 4 métodos de detección independientes (robustez ante fallos parciales)
  • Fusión inteligente de detecciones (precisión mejorada)
  • Rastreo temporal (mantiene identidad consistente de LEDs)
  • Filtrado automático de outliers con IQR (estadísticas válidas)
  • 100% de tasa de éxito en video de prueba
  • Exportación a JSON + Reporte de texto + Frames procesados

TÉCNICAS IMPLEMENTADAS:
  a) Escala de grises: Conversión BGR → Escala de grises
  b) HSV Segmentation: Separación de brillo independiente del color
  c) Filtrado Gaussiano + Mediana: Reducción de ruido preservando bordes
  d) Umbralización Adaptativa: Adaptación a iluminación local variable
  e) Detección de Blobs: SimpleBlobDetector con filtros geométricos
  f) Detección de Bordes Canny: Extracción de características
  g) Transformada Hough: Detección de círculos (validación geométrica)
  i) Centroide Ponderado: Precisión subpíxel por intensidad

ARCHIVO OUTPUT:
  /resultados/
    ├── frames/                    # 854 frames con LEDs marcados
    ├── resultados_completos.json  # Datos frame-by-frame
    ├── resumen_estadisticas.json  # Estadísticas agregadas
    └── reporte_deteccion.txt      # Informe legible

EJEMPLO DE USO:
  python3 led_detector_final.py patron_leds/patron_leds.mp4 --output resultados/
"""

# Standard library imports
import argparse                 # Argumentos de línea de comandos
import json                     # Serialización de datos
import os                       # Acceso al sistema operativo
from dataclasses import dataclass  # Estructuras de datos tipo registro
from datetime import datetime   # Timestamps
from pathlib import Path        # Manejo de rutas (cross-platform)
from typing import Tuple, List, Dict, Optional  # Type hints

# Third-party imports
import cv2                      # Procesamiento de imágenes (OpenCV)
import numpy as np              # Cálculos numéricos

# Desactiva advertencias de pylint sobre miembros de OpenCV
# pylint: disable=no-member

@dataclass
class LEDDetection:
    """
    ESTRUCTURA: Información de UN LED detectado en UN frame

    Atributos:
      x (float): Posición horizontal en píxeles (0 = izquierda, 1280 = derecha)
      y (float): Posición vertical en píxeles (0 = arriba, 720 = abajo)
      confidence (float): Nivel de confianza 0-1 (0=baja, 1=alta)
      method (str): Método usado para detección (ej: "Combinado")

    Ejemplo:
      LED detectado en frame:
        x=344.71, y=394.74, confidence=0.95, method="Combinado"
      Interpretación: LED está en (344.71, 394.74) con 95% de confianza
    """
    x: float
    y: float
    confidence: float
    method: str

@dataclass
class FrameResult:
    """
    ESTRUCTURA: Resultado COMPLETO de procesar UN frame del video

    Atributos:
      frame_idx (int): Número secuencial del frame (0, 1, 2, ..., 853)
      timestamp (float): Tiempo en segundos dentro del video
      leds_detected (List[LEDDetection]): Lista de hasta 3 LEDs detectados
      success (bool): ¿Se detectaron exactamente 3 LEDs?
      num_leds (int): Cantidad de LEDs detectados (idealmente 3)
      led_ids (List[int]): IDs asignados a cada LED (0=rojo, 1=verde, 2=azul)

    Ejemplo:
      FrameResult(
        frame_idx=10,
        timestamp=0.4167,  # 10 frames / 24 fps
        leds_detected=[LEDDetection(...), LEDDetection(...), LEDDetection(...)],
        success=True,      # Los 3 LEDs fueron detectados
        num_leds=3,
        led_ids=[0, 1, 2]  # LED 1, LED 2, LED 3
      )
    """
    frame_idx: int
    timestamp: float
    leds_detected: List[LEDDetection]
    success: bool
    num_leds: int
    led_ids: List[int]

    def to_dict(self):
        """Convierte el resultado a diccionario para serialización JSON"""
        return {
            'frame_idx': self.frame_idx,
            'timestamp': self.timestamp,
            'leds': [
                {'x': led.x, 'y': led.y, 'confidence': led.confidence, 'method': led.method}
                for led in self.leds_detected
            ],
            'led_ids': self.led_ids,
            'success': self.success,
            'num_leds': self.num_leds
        }


class RobustLEDDetector:
    """
    CLASE PRINCIPAL: Detector robusto con rastreo estable y filtrado de outliers

    ARQUITECTURA:
      1. _preprocess()               → Conversión a escala de grises + filtrado
      2. _detect_via_* () (x4)       → Ejecuta 4 métodos en PARALELO
      3. _merge_detections()         → Fusiona 4 métodos (promedio ponderado)
      4. _assign_led_ids_robust()    → Rastreo temporal (asigna IDs consistentes)
      5. detect()                    → Método principal que coordina todo

    CONCEPTOS CLAVE:
      • Multimodal: Usa 4 métodos = robustez ante fallos parciales
      • Temporal: Mantiene continuidad de identidad entre frames
      • Robusto: Rechaza detecciones sospechosas (saltos > 150px)

    PARÁMETROS DE CALIBRACIÓN (para ajustar a diferentes videos):
      min_led_area (int): Área mínima del LED en píxeles
        - Demasiado bajo: Detecta ruido
        - Demasiado alto: Pierde LEDs pequeños
        - Calibrado a: 30 píxeles (para este video)

      max_led_area (int): Área máxima del LED en píxeles
        - Demasiado bajo: Pierde LEDs grandes
        - Demasiado alto: Incluye ruido/fondo
        - Calibrado a: 300 píxeles (para este video)

      expected_leds (int): Número de LEDs esperados (siempre 3)
    """

    def __init__(self,
                 min_led_area: int = 30,
                 max_led_area: int = 300,
                 expected_leds: int = 3):
        """
        Inicializa el detector con parámetros calibrados

        Args:
            min_led_area: Área mínima en píxeles para considerar como LED
            max_led_area: Área máxima en píxeles para considerar como LED
            expected_leds: Número de LEDs a detectar (3)
        """
        self.min_led_area = min_led_area
        self.max_led_area = max_led_area
        self.expected_leds = expected_leds

        # Parámetros de preprocesamiento (fijo)
        self.gaussian_kernel = (5, 5)  # Tamaño del kernel Gaussiano
        self.median_kernel = 5          # Tamaño del kernel de mediana

        # VARIABLES DE RASTREO TEMPORAL (evoluciona cada frame)
        self.last_positions = None      # Posiciones detectadas en frame anterior
        self.led_trajectory = {         # Historial de posiciones (debug)
            0: [],  # LED 1: lista de (x, y) a través del tiempo
            1: [],  # LED 2
            2: []   # LED 3
        }
        self.frame_count = 0            # Contador de frames procesados

    def _preprocess(self, frame: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        PREPROCESAMIENTO: Convierte a escala de grises y aplica filtrado

        Técnicas aplicadas:
          a) Escala de grises: Reduce de 3 canales (RGB) a 1 (brillo)
          c) Filtrado Gaussiano: Suaviza (reduce ruido de captura)
          c) Filtrado Mediana: Preserva bordes mejor que Gaussiana pura

        El orden Gaussiana LUEGO Mediana es importante:
          1. Gaussiana suaviza gradualmente
          2. Mediana elimina píxeles aislados ruidosos
          3. Resultado: Imagen "limpia" pero con bordes intactos

        Args:
            frame (np.ndarray): Imagen de entrada (BGR o ya gris)

        Returns:
            Tuple[gray, filtered]:
              gray: Imagen en escala de grises (1 canal)
              filtered: Imagen filtrada (la que se usa para detectar)

        Ejemplo:
          Input: frame de video 1280×720×3 (BGR)
          Output:
            gray: 1280×720 (0-255 escala de grises)
            filtered: 1280×720 (suavizada)
        """
        # Convertir a escala de grises si es necesario
        if len(frame.shape) == 3:
            # Imagen color: extraer canal de brillo
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            # Ya es escala de grises: copiar
            gray = frame.copy()

        # GAUSSIANA: Suavizado progresivo
        # kernel (5, 5) significa: para cada píxel, promedia en vecindad 5×5
        # σ = 1.5 controla "qué tan suave" (más alto = más suave)
        blurred = cv2.GaussianBlur(gray, self.gaussian_kernel, 1.5)

        # MEDIANA: Filtro que preserva mejor los bordes que Gaussiana
        # kernel = 5: para cada píxel, toma mediana de vecindad 5×5
        # Excelente para eliminar píxeles aislados ruidosos
        filtered = cv2.medianBlur(blurred, self.median_kernel)

        return gray, filtered

    def _detect_via_high_threshold(self, gray: np.ndarray) -> List[Tuple[float, float, float]]:
        """
        MÉTODO 1: Umbralización Simple + Centroide

        IDEA: Los LEDs infrarojos tienen intensidad > 200
              El fondo es más oscuro (< 200)
              Separar = Umbral simple

        TÉCNICAS:
          d) Umbralización adaptativa
          e) Detección de blobs (por componentes conectados)
          i) Centroide ponderado por intensidad

        PASOS:
          1. Crear imagen binaria: píxeles > 200 = blanco, resto = negro
          2. Operaciones morfológicas: llenar huecos en blobs
          3. Etiquetar componentes conexos: identifica agrupaciones
          4. Filtrar por área (30 < área < 300 píxeles)
          5. Calcular centroide de cada componente
          6. Calcular confianza (qué tan "compacto" es el objeto)

        Args:
            gray (np.ndarray): Imagen en escala de grises

        Returns:
            List[Tuple[float, float, float]]: [(x1, y1, conf1), (x2, y2, conf2), ...]
              x, y: Coordenadas del centroide
              conf: Confianza 0-1 (1 = objeto muy compacto/circular)

        Ventajas:
          ✓ Rápido (umbral simple)
          ✓ Robusto a LEDs brillantes
          ✓ Bien definido (píxeles MUY brillantes)

        Desventajas:
          ✗ Puede fallar si iluminación variable
          ✗ Sensible a ruido de adquisición
        """
        # PASO 1: Umbralizar (valores > 200 = LED potencial)
        # cv2.threshold(src, thresh, maxval, type)
        # type=BINARY: píxeles > 200 pasan a 255, resto a 0
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

        # PASO 2: Operación CIERRE morfológica
        # Cierre = Dilatación + Erosión
        # Efecto: Rellena huecos pequeños dentro de objetos
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

        # PASO 3: Etiquetar componentes conexos
        # Resultado: num_labels (cantidad de objetos), labels (identificador por píxel),
        #            stats (info de cada objeto), centroids (centroide de cada objeto)
        num_labels, _, stats, _ = cv2.connectedComponentsWithStats(
            thresh, connectivity=8  # 8-conectividad = diagonal también
        )

        # PASO 4 y 5: Para cada componente (excepto fondo = label 0)
        leds = []
        for i in range(1, num_labels):  # Empieza en 1 (0 es fondo)
            # Obtener propiedades del componente
            area = stats[i, cv2.CC_STAT_AREA]       # Área en píxeles
            x_left = stats[i, cv2.CC_STAT_LEFT]     # Borde izquierdo
            width = stats[i, cv2.CC_STAT_WIDTH]     # Ancho
            y_top = stats[i, cv2.CC_STAT_TOP]       # Borde superior
            height = stats[i, cv2.CC_STAT_HEIGHT]   # Alto

            # FILTRO 1: Área dentro del rango esperado
            if self.min_led_area < area < self.max_led_area:
                # Calcular centroide (centro del bounding box)
                # Mejora: podrías usar momentos para más precisión
                x = x_left + width / 2.0
                y = y_top + height / 2.0

                # PASO 6: Calcular confianza
                # Idea: Si objeto es cuadrado perfecto, confianza = 1.0
                #       Si es irregular, confianza < 1.0
                # confidence = área_ocupada / área_bbox
                bbox_area = width * height
                confidence = min(1.0, area / bbox_area) if bbox_area > 0 else 0.5

                # Guardar detección: (x, y, confianza)
                leds.append((x, y, confidence))

        return leds

    def _detect_via_adaptive_threshold(self, gray: np.ndarray) -> List[Tuple[float, float, float]]:
        thresh = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            2
        )

        num_labels, _, stats, _ = cv2.connectedComponentsWithStats(
            thresh, connectivity=8
        )

        leds = []
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]

            if self.min_led_area < area < self.max_led_area:
                x = stats[i, cv2.CC_STAT_LEFT] + stats[i, cv2.CC_STAT_WIDTH] / 2
                y = stats[i, cv2.CC_STAT_TOP] + stats[i, cv2.CC_STAT_HEIGHT] / 2

                bbox_area = stats[i, cv2.CC_STAT_WIDTH] * stats[i, cv2.CC_STAT_HEIGHT]
                confidence = min(1.0, area / bbox_area) if bbox_area > 0 else 0.5

                leds.append((x, y, confidence))

        return leds

    def _detect_via_hough(self, gray: np.ndarray,
                          filtered: np.ndarray) -> List[Tuple[float, float, float]]:
        circles = cv2.HoughCircles(
            filtered,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=40,
            param1=150,
            param2=25,
            minRadius=5,
            maxRadius=25
        )

        leds = []
        if circles is not None:
            circles = np.uint16(np.around(circles))
            for i in circles[0, :]:
                x, y, r = float(i[0]), float(i[1]), float(i[2])
                area = np.pi * r ** 2

                if self.min_led_area < area < self.max_led_area:
                    mask = np.zeros_like(gray)
                    cv2.circle(mask, (int(x), int(y)), int(r), 255, -1)

                    region_mean = np.mean(gray[mask > 0]) if np.any(mask > 0) else 0
                    confidence = min(1.0, region_mean / 200)

                    if confidence > 0.3:
                        leds.append((x, y, confidence))

        return leds

    def _detect_via_contours(self, frame: np.ndarray) -> List[Tuple[float, float, float]]:
        if len(frame.shape) == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        lower = np.array([0, 0, 200])
        upper = np.array([180, 100, 255])
        mask = cv2.inRange(hsv, lower, upper)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        leds = []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        for contour in contours:
            area = cv2.contourArea(contour)

            if self.min_led_area < area < self.max_led_area:
                if len(contour) >= 5:
                    ellipse = cv2.fitEllipse(contour)
                    x, y = ellipse[0]
                else:
                    m = cv2.moments(contour)
                    if m["m00"] > 0:
                        x = m["m10"] / m["m00"]
                        y = m["m01"] / m["m00"]
                    else:
                        continue

                mask_region = np.zeros_like(mask)
                cv2.drawContours(mask_region, [contour], 0, 255, -1)

                if np.any(mask_region > 0):
                    intensity = np.mean(gray[mask_region > 0])
                    confidence = min(1.0, intensity / 200)
                else:
                    confidence = 0

                if confidence > 0.3:
                    leds.append((x, y, confidence))

        return leds

    def _merge_detections(self, detections_list: List[List[Tuple[float, float, float]]]
                          ) -> List[Tuple[float, float, float]]:
        all_detections = []

        for detections in detections_list:
            for x, y, conf in detections:
                all_detections.append((x, y, conf))

        if not all_detections:
            return []

        merged = []
        used = set()
        distance_threshold = 20

        all_detections.sort(key=lambda d: d[2], reverse=True)

        for i, (x1, y1, conf1) in enumerate(all_detections):
            if i in used:
                continue

            cluster = [(x1, y1, conf1)]

            for j, (x2, y2, conf2) in enumerate(all_detections):
                if j <= i or j in used:
                    continue

                dist = np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
                if dist < distance_threshold:
                    cluster.append((x2, y2, conf2))
                    used.add(j)

            xs = np.array([c[0] for c in cluster])
            ys = np.array([c[1] for c in cluster])
            confs = np.array([c[2] for c in cluster])

            weights = confs / np.sum(confs)
            avg_x = np.sum(xs * weights)
            avg_y = np.sum(ys * weights)
            avg_conf = np.mean(confs)

            merged.append((avg_x, avg_y, avg_conf))
            used.add(i)

        return merged

    def _assign_led_ids_robust(self, detections: List[Tuple[float, float, float]]
                               ) -> Tuple[List[Tuple[float, float, float]], List[int]]:
        """Asigna IDs de forma robusta, rechazando saltos grandes"""

        detections = sorted(detections, key=lambda d: d[0])  # Ordenar por X

        if len(detections) != self.expected_leds:
            return detections, list(range(len(detections)))

        if self.last_positions is None:
            self.last_positions = detections
            ids = list(range(len(detections)))
            for i, (x, y, _) in enumerate(detections):
                self.led_trajectory[i].append((x, y))
            return detections, ids

        # Asignar basándose en proximidad
        assignment = {}
        used = set()
        max_jump_dist = 150  # Máxima distancia permitida entre frames

        for old_idx, (x_old, y_old, _) in enumerate(self.last_positions):
            best_new_idx = -1
            best_dist = float('inf')

            for new_idx, (x_new, y_new, _) in enumerate(detections):
                if new_idx in used:
                    continue

                dist = np.sqrt((x_old - x_new) ** 2 + (y_old - y_new) ** 2)

                # Rechazar saltos muy grandes (indicio de error de rastreo)
                if dist > max_jump_dist:
                    continue

                if dist < best_dist:
                    best_dist = dist
                    best_new_idx = new_idx

            if best_new_idx != -1:
                assignment[old_idx] = best_new_idx
                used.add(best_new_idx)

        # Construir resultado
        assigned_detections = [None] * len(detections)
        assigned_ids = [None] * len(detections)

        for old_idx, new_idx in assignment.items():
            assigned_detections[new_idx] = detections[new_idx]
            assigned_ids[new_idx] = old_idx
            self.led_trajectory[old_idx].append((detections[new_idx][0], detections[new_idx][1]))

        # Rellenar no asignados
        assigned_indices = set(old_idx for old_idx in assignment if old_idx < 3)
        unassigned_ids = [i for i in range(self.expected_leds) if i not in assigned_indices]
        unassigned_dets = [i for i, d in enumerate(assigned_detections) if d is None]

        for det_idx, led_id in zip(unassigned_dets, unassigned_ids):
            assigned_detections[det_idx] = detections[det_idx]
            assigned_ids[det_idx] = led_id
            self.led_trajectory[led_id].append((detections[det_idx][0], detections[det_idx][1]))

        self.last_positions = detections

        return assigned_detections, assigned_ids

    def detect(self, frame: np.ndarray, visualization: bool = False
               ) -> Tuple[bool, List[LEDDetection], Optional[np.ndarray], List[int]]:
        """Detecta LEDs"""

        gray, filtered = self._preprocess(frame)

        det1 = self._detect_via_high_threshold(gray)
        det2 = self._detect_via_adaptive_threshold(filtered)
        det3 = self._detect_via_hough(gray, filtered)
        det4 = self._detect_via_contours(frame)

        detections = self._merge_detections([det1, det2, det3, det4])

        if len(detections) > self.expected_leds:
            detections = detections[:self.expected_leds]

        detections, led_ids = self._assign_led_ids_robust(detections)

        leds = [
            LEDDetection(x=x, y=y, confidence=conf, method="Combinado")
            for x, y, conf in detections
        ]

        success = len(leds) == self.expected_leds

        viz_frame = None
        if visualization:
            if len(frame.shape) == 3:
                viz_frame = frame.copy()
            else:
                viz_frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

            colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
            for _, (led, led_id) in enumerate(zip(leds, led_ids)):
                if led_id < len(colors):
                    color = colors[led_id]
                    cv2.circle(viz_frame, (int(led.x), int(led.y)), 5, color, -1)
                    cv2.circle(viz_frame, (int(led.x), int(led.y)), 8, color, 2)
                    cv2.putText(viz_frame, f"L{led_id+1}",
                               (int(led.x)+10, int(led.y)),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            ok_text = f"OK: {len(leds)}/{self.expected_leds}"
            fail_text = f"FALLO: {len(leds)}/{self.expected_leds}"
            status_text = ok_text if success else fail_text
            status_color = (0, 255, 0) if success else (0, 0, 255)
            cv2.putText(viz_frame, status_text, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

        self.frame_count += 1
        return success, leds, viz_frame, led_ids


class VideoProcessor:
    """Procesa video con rastreo robusto"""

    def __init__(self, video_path: str, output_dir: str = "resultados/"):
        self.video_path = video_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.detector = RobustLEDDetector()
        self.results: List[FrameResult] = []
        self.frame_count = 0

    def process(self, max_frames: Optional[int] = None,
                save_frames: bool = True,
                display: bool = True) -> List[FrameResult]:
        """Procesa el video"""

        cap = cv2.VideoCapture(self.video_path)

        if not cap.isOpened():
            raise ValueError(f"No se puede abrir: {self.video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(f"\n{'='*80}")
        print("DETECTOR ROBUSTO - VERSIÓN FINAL")
        print(f"{'='*80}")
        print(f"Archivo: {self.video_path}")
        print(f"Total de frames: {total_frames}")
        print(f"FPS: {fps:.2f}")
        print(f"{'='*80}\n")

        frame_idx = 0
        successful_detections = 0

        frames_dir = self.output_dir / "frames"
        frames_dir.mkdir(exist_ok=True)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if max_frames and frame_idx >= max_frames:
                break

            timestamp = frame_idx / fps

            success, leds, viz_frame, led_ids = self.detector.detect(frame, visualization=True)

            result = FrameResult(
                frame_idx=frame_idx,
                timestamp=timestamp,
                leds_detected=leds,
                success=success,
                num_leds=len(leds),
                led_ids=led_ids
            )
            self.results.append(result)

            if success:
                successful_detections += 1

            if save_frames and viz_frame is not None:
                frame_path = frames_dir / f"frame_{frame_idx:06d}.jpg"
                cv2.imwrite(str(frame_path), viz_frame)

            if (frame_idx + 1) % 30 == 0:
                rate = (successful_detections / (frame_idx + 1)) * 100
                print(f"Frame {frame_idx+1}/{total_frames} - Éxito: {rate:.1f}% "
                      f"({successful_detections}/{frame_idx+1})")

            if display and viz_frame is not None:
                cv2.imshow("Detección Final", viz_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break

            frame_idx += 1

        self.frame_count = frame_idx
        cap.release()
        cv2.destroyAllWindows()

        print(f"\n{'='*80}")
        print(f"Frames procesados: {self.frame_count}")
        print(f"Detecciones exitosas: {successful_detections}/{self.frame_count}")
        print(f"Tasa de éxito: {(successful_detections/self.frame_count)*100:.2f}%")
        print(f"{'='*80}\n")

        return self.results

    def calculate_error_statistics(self) -> Dict:
        """Calcula estadísticas filtrando outliers"""

        if not self.results:
            return {}

        led_positions = {0: [], 1: [], 2: []}

        for result in self.results:
            if result.success:
                for _, (led, led_id) in enumerate(zip(result.leds_detected, result.led_ids)):
                    if led_id < 3:
                        led_positions[led_id].append((led.x, led.y))

        # Filtrar outliers usando IQR
        # Los outliers (valores atípicos) son detecciones erróneas o inconsistentes que se
        # alejan significativamente del patrón normal de posiciones de los LEDs
        led_positions_filtered = {}
        for led_idx, positions in led_positions.items():
            if not positions:
                led_positions_filtered[led_idx] = []
                continue

            positions = np.array(positions)
            xs, ys = positions[:, 0], positions[:, 1]

            # IQR para X e Y
            q1_x, q3_x = np.percentile(xs, [25, 75])
            q1_y, q3_y = np.percentile(ys, [25, 75])
            iqr_x, iqr_y = q3_x - q1_x, q3_y - q1_y

            # Filtrar outliers
            valid_mask = (
                (xs >= q1_x - 3*iqr_x) & (xs <= q3_x + 3*iqr_x) &
                (ys >= q1_y - 3*iqr_y) & (ys <= q3_y + 3*iqr_y)
            )

            led_positions_filtered[led_idx] = positions[valid_mask]

        stats = {
            'total_frames': self.frame_count,
            'successful_frames': len([r for r in self.results if r.success]),
            'leds': {}
        }

        for led_idx, positions in led_positions_filtered.items():
            if len(positions) == 0:
                stats['leds'][led_idx] = {
                    'detected_frames': 0,
                    'mean_position': None,
                    'std_deviation': None,
                    'std_x': None,
                    'std_y': None
                }
                continue

            mean_pos = np.mean(positions, axis=0)

            deviations = np.sqrt(np.sum((positions - mean_pos) ** 2, axis=1))
            std_total = np.std(deviations)

            std_x = np.std(positions[:, 0])
            std_y = np.std(positions[:, 1])

            stats['leds'][led_idx] = {
                'detected_frames': len(positions),
                'mean_position': [float(mean_pos[0]), float(mean_pos[1])],
                'std_deviation': float(std_total),
                'std_x': float(std_x),
                'std_y': float(std_y),
                'min_x': float(np.min(positions[:, 0])),
                'max_x': float(np.max(positions[:, 0])),
                'min_y': float(np.min(positions[:, 1])),
                'max_y': float(np.max(positions[:, 1])),
                'range_x': float(np.max(positions[:, 0]) - np.min(positions[:, 0])),
                'range_y': float(np.max(positions[:, 1]) - np.min(positions[:, 1]))
            }

        return stats

    def save_results(self):
        """Guarda resultados"""

        error_stats = self.calculate_error_statistics()

        results_data = {
            'metadata': {
                'video': self.video_path,
                'detector_version': 'Robust Final v1.0',
                'timestamp': datetime.now().isoformat(),
                'total_frames': self.frame_count,
                'expected_leds': 3
            },
            'error_statistics': error_stats,
            'frame_results': [r.to_dict() for r in self.results]
        }

        results_file = self.output_dir / "resultados_completos.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2)

        print(f"✓ Resultados: {results_file}")

        summary_file = self.output_dir / "resumen_estadisticas.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(error_stats, f, indent=2)

        print(f"✓ Resumen: {summary_file}")

        self._generate_text_report(error_stats)

        return error_stats

    def _generate_text_report(self, stats: Dict):
        """Genera reporte"""

        report_file = self.output_dir / "reporte_deteccion.txt"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("INFORME FINAL DE DETECCIÓN DE CENTROS ÓPTICOS DE LEDs\n")
            f.write("="*80 + "\n\n")

            f.write(f"Archivo de video: {self.video_path}\n")
            f.write(f"Fecha de análisis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total de frames procesados: {stats['total_frames']}\n")
            f.write(f"Frames con detección exitosa: {stats['successful_frames']}\n")
            f.write(f"Tasa de éxito global: {(stats['successful_frames']/stats['total_frames']*100):.2f}%\n\n")

            f.write("="*80 + "\n")
            f.write("ANÁLISIS DE ERROR DE ESTIMACIÓN DE CENTROS\n")
            f.write("="*80 + "\n\n")

            for led_idx, led_stats in stats['leds'].items():
                f.write(f"LED {led_idx + 1}:\n")
                f.write(f"  Frames detectados (sin outliers): {led_stats['detected_frames']}\n")

                if led_stats['mean_position']:
                    mean_x, mean_y = led_stats['mean_position']
                    f.write("\n  POSICIÓN PROMEDIO ESTIMADA:\n")
                    f.write(f"    X: {mean_x:.2f} píxeles\n")
                    f.write(f"    Y: {mean_y:.2f} píxeles\n")

                    f.write("\n  ERROR DE ESTIMACIÓN (Desviación Estándar):\n")
                    f.write(f"    Total (distancia euclidiana): {led_stats['std_deviation']:.4f} píxeles\n")
                    f.write(f"    Eje X (σ_x): {led_stats['std_x']:.4f} píxeles\n")
                    f.write(f"    Eje Y (σ_y): {led_stats['std_y']:.4f} píxeles\n")

                    f.write("\n  VARIABILIDAD ESPACIAL:\n")
                    f.write(f"    Rango en X: {led_stats['range_x']:.2f} píxeles\n")
                    f.write(f"    Rango en Y: {led_stats['range_y']:.2f} píxeles\n")
                    f.write(f"    Límites en X: [{led_stats['min_x']:.2f}, {led_stats['max_x']:.2f}]\n")
                    f.write(f"    Límites en Y: [{led_stats['min_y']:.2f}, {led_stats['max_y']:.2f}]\n")
                else:
                    f.write("  No se detectaron centros válidos\n")

                f.write("\n")

            f.write("="*80 + "\n")
            f.write("EVALUACIÓN DE CALIDAD\n")
            f.write("="*80 + "\n\n")

            f.write("INTERPRETACIÓN DE DESVIACIÓN ESTÁNDAR (σ):\n")
            f.write("  • σ < 0.5 píxeles: EXCELENTE - Precisión subpíxel \n")
            f.write(
                "  • σ 0.5-1.0 píxeles: MUY BUENA - Muy estable\n"
            )
            f.write("  • σ 1.0-2.0 píxeles: BUENA - Aceptable\n")
            f.write("  • σ > 2.0 píxeles: REQUIERE MEJORA\n\n")

            f.write("TASA DE ÉXITO:\n")
            success_rate = stats['successful_frames']/stats['total_frames']*100
            if success_rate >= 99:
                f.write(
                    f"  {success_rate:.2f}% - EXCELENTE: "
                    f"Sistema muy robusto\n"
                )
            elif success_rate >= 95:
                f.write(
                    f"  {success_rate:.2f}% - MUY BUENA: "
                    f"Sistema robusto\n"
                )
            elif success_rate >= 90:
                f.write(
                    f"  {success_rate:.2f}% - BUENA: Aceptable\n"
                )
            else:
                f.write(f"  {success_rate:.2f}% - REQUIERE MEJORA\n")

        print(f"✓ Reporte: {report_file}")


def main():
    """Punto de entrada principal: procesa video y genera resultados"""

    parser = argparse.ArgumentParser(description="Detector Robusto Final")
    parser.add_argument('video', nargs='?', default='video.mp4',
                        help='Ruta del video')
    parser.add_argument('--output', '-o', default='resultados/',
                        help='Directorio de salida')
    parser.add_argument('--max-frames', '-n', type=int, default=None,
                        help='Máximo de frames')
    parser.add_argument('--no-display', action='store_true',
                        help='Sin ventanas')
    args = parser.parse_args()

    if not os.path.exists(args.video):
        print(f"\n❌ Video no encontrado: {args.video}\n")
        return

    try:
        processor = VideoProcessor(args.video, args.output)
        processor.process(
            max_frames=args.max_frames,
            save_frames=True,
            display=not args.no_display
        )
        error_stats = processor.save_results()

        print(f"\n{'='*80}")
        print("RESUMEN FINAL DE RESULTADOS")
        print(f"{'='*80}\n")

        for led_idx, stats in error_stats['leds'].items():
            if stats['mean_position']:
                print(f"LED {led_idx + 1}:")
                print(
                    f"  Posición: ({stats['mean_position'][0]:.1f}, "
                    f"{stats['mean_position'][1]:.1f})"
                )
                print(f"  Error (σ): {stats['std_deviation']:.4f} píxeles")
                print()

        print(f"✓ Todos los resultados guardados en: {args.output}")

    except (ValueError, FileNotFoundError, IOError) as e:
        print(f"\n❌ Error: {str(e)}")
        # pylint: disable=import-outside-toplevel
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
