#!/usr/bin/env python3
# pylint: disable=no-member
"""
╔════════════════════════════════════════════════════════════════════════════════╗
║    DETECTOR ESTRICTO DE LEDs CON VALIDACIÓN GEOMÉTRICA                        ║
║                          VERSIÓN 3.0                                          ║
╚════════════════════════════════════════════════════════════════════════════════╝

DESCRIPCIÓN:
    Detector de LEDs con validación geométrica estricta + Filtro de Kalman.
    Solo acepta detecciones que cumplan el patrón conocido (3 LEDs en línea).

PROBLEMA QUE RESUELVE:
    El detector de Etapa 1 encontraba "3 puntos brillantes" pero NO validaba
    que fueran el patrón de LEDs real. Muchos frames tenían:
    - Error de colinealidad > 200px (debería ser <5px)
    - Ratio de distancias 1.4-1.8 (debería ser ~1.0)

EJECUCIÓN:
    Desde la carpeta etapa2_kalman_parpadeo/:

    # Opción 1: Video original
    python3 led_detector_estricto.py ../patron_leds/patron_leds.mp4

    # Opción 2: Video con parpadeo simulado
    python3 led_detector_estricto.py videos_parpadeo/patron_parpadeo.mp4

    # Opción 3: Con carpeta de salida personalizada
    python3 led_detector_estricto.py ../patron_leds/patron_leds.mp4 -o mis_resultados/

SALIDA:
    resultados_estricto/
    ├── frames/                   # TODOS los frames procesados
    │   ├── frame_000000.jpg
    │   ├── frame_000001.jpg
    │   └── ...
    └── reporte.txt               # Resumen de detección

RESTRICCIONES GEOMÉTRICAS DEL PATRÓN:
    - 3 LEDs en línea recta (colinealidad < 5px)
    - Equiespaciados (ratio distancias 0.9-1.1)
    - Distancia mínima entre LEDs: 50px
    - Distancia máxima entre LEDs: 400px

Autor: Tobias Funes
Fecha: Diciembre 2025
"""

import argparse
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Tuple, List, Dict, Optional
from itertools import combinations

import cv2
import numpy as np


# =============================================================================
# ESTRUCTURAS DE DATOS
# =============================================================================

@dataclass
class LEDDetection:
    """Información de un LED detectado."""
    x: float
    y: float
    confidence: float
    led_id: int  # 0=izquierda, 1=centro, 2=derecha


@dataclass
class FrameResult:
    """Resultado de procesar un frame."""
    frame_idx: int
    timestamp: float
    leds: List[LEDDetection]
    success: bool
    geometry_error: float  # Error de colinealidad en px
    spacing_ratio: float   # Ratio d12/d23 (ideal=1.0)

    def to_dict(self):
        """Convierte el resultado a diccionario para serialización JSON."""
        return {
            'frame_idx': self.frame_idx,
            'timestamp': self.timestamp,
            'success': self.success,
            'geometry_error': self.geometry_error,
            'spacing_ratio': self.spacing_ratio,
            'leds': [
                {'x': led.x, 'y': led.y, 'confidence': led.confidence, 'led_id': led.led_id}
                for led in self.leds
            ]
        }


# =============================================================================
# FILTRO DE KALMAN
# =============================================================================

class KalmanTracker:
    """Filtro de Kalman para suavizar trayectoria de un LED."""

    def __init__(self, x: float, y: float):
        self.kalman = cv2.KalmanFilter(4, 2)

        # Transición: velocidad constante
        self.kalman.transitionMatrix = np.array([
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ], dtype=np.float32)

        # Medición: solo posición
        self.kalman.measurementMatrix = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ], dtype=np.float32)

        # Ruido de proceso (Q): permite movimiento moderado
        self.kalman.processNoiseCov = np.eye(4, dtype=np.float32) * 1.0

        # Ruido de medición (R): incertidumbre de detección
        self.kalman.measurementNoiseCov = np.eye(2, dtype=np.float32) * 5.0

        # Estado inicial
        self.kalman.statePost = np.array([[x], [y], [0], [0]], dtype=np.float32)
        self.kalman.errorCovPost = np.eye(4, dtype=np.float32)

    def update(self, x: float, y: float) -> Tuple[float, float]:
        """Predice y corrige con nueva medición."""
        self.kalman.predict()
        measurement = np.array([[x], [y]], dtype=np.float32)
        corrected = self.kalman.correct(measurement)
        return float(corrected[0][0]), float(corrected[1][0])

    def predict_only(self) -> Tuple[float, float]:
        """Solo predice (cuando no hay medición)."""
        predicted = self.kalman.predict()
        return float(predicted[0][0]), float(predicted[1][0])


# =============================================================================
# DETECTOR ESTRICTO
# =============================================================================

class StrictLEDDetector:
    """
    Detector de LEDs con validación geométrica estricta.

    Solo acepta detecciones que cumplan:
    - 3 puntos colineales (error < max_collinearity_error)
    - Equiespaciados (ratio entre 1-tolerance y 1+tolerance)
    """

    def __init__(self,
                 max_collinearity_error: float = 5.0,
                 spacing_tolerance: float = 0.10,
                 min_led_distance: float = 50.0,
                 max_led_distance: float = 400.0,
                 min_blob_area: int = 20,
                 max_blob_area: int = 500):

        self.max_collinearity_error = max_collinearity_error
        self.spacing_tolerance = spacing_tolerance
        self.min_led_distance = min_led_distance
        self.max_led_distance = max_led_distance
        self.min_blob_area = min_blob_area
        self.max_blob_area = max_blob_area

        # Kalman trackers (uno por LED)
        self.trackers: Dict[int, KalmanTracker] = {}

        # Historial para métricas
        self.frame_count = 0
        self.last_valid_detection = None

    def _find_bright_blobs(self, gray: np.ndarray) -> List[Tuple[float, float, float]]:
        """
        Encuentra todos los blobs brillantes en la imagen.
        Usa umbral adaptativo basado en el percentil de la imagen.
        """
        # Calcular umbral dinámico basado en percentil 95
        p95 = np.percentile(gray, 95)
        thresh_value = max(int(p95), 100)  # Mínimo 100 para evitar ruido

        _, thresh = cv2.threshold(gray, thresh_value, 255, cv2.THRESH_BINARY)

        # Operaciones morfológicas
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)

        # Encontrar componentes
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            thresh, connectivity=8
        )

        blobs = []
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]

            if self.min_blob_area < area < self.max_blob_area:
                cx, cy = centroids[i]

                # Calcular intensidad promedio como confianza
                mask = labels == i
                mean_intensity = np.mean(gray[mask]) if np.any(mask) else 0
                confidence = mean_intensity / 255.0

                blobs.append((float(cx), float(cy), confidence))

        return blobs

    def _calculate_geometry(self, triplet: List[Tuple[float, float, float]]
                           ) -> Tuple[float, float, float, float]:
        """
        Calcula métricas geométricas de un triplete.

        Returns:
            (collinearity_error, spacing_ratio, d12, d23)
        """
        # Ordenar por X
        sorted_t = sorted(triplet, key=lambda p: p[0])
        p1 = np.array([sorted_t[0][0], sorted_t[0][1]])
        p2 = np.array([sorted_t[1][0], sorted_t[1][1]])
        p3 = np.array([sorted_t[2][0], sorted_t[2][1]])

        # Distancias
        d12 = np.linalg.norm(p2 - p1)
        d23 = np.linalg.norm(p3 - p2)

        if d12 < 1 or d23 < 1:
            return float('inf'), float('inf'), 0, 0

        # Ratio de espaciamiento
        spacing_ratio = d12 / d23

        # Error de colinealidad: distancia de p2 a la línea p1-p3
        line_vec = p3 - p1
        line_len = np.linalg.norm(line_vec)

        if line_len < 1:
            return float('inf'), float('inf'), 0, 0

        # Proyección de p2 sobre la línea
        t = np.dot(p2 - p1, line_vec) / (line_len ** 2)
        closest_point = p1 + t * line_vec
        collinearity_error = np.linalg.norm(p2 - closest_point)

        return collinearity_error, spacing_ratio, d12, d23

    def _validate_triplet(self, triplet: List[Tuple[float, float, float]]) -> bool:
        """Valida si un triplete cumple todas las restricciones geométricas."""
        col_error, spacing_ratio, d12, d23 = self._calculate_geometry(triplet)

        # Verificar colinealidad
        if col_error > self.max_collinearity_error:
            return False

        # Verificar equiespaciamiento
        if (spacing_ratio < 1 - self.spacing_tolerance or
                spacing_ratio > 1 + self.spacing_tolerance):
            return False

        # Verificar distancias
        if d12 < self.min_led_distance or d12 > self.max_led_distance:
            return False
        if d23 < self.min_led_distance or d23 > self.max_led_distance:
            return False

        return True

    def _find_best_triplet(self, blobs: List[Tuple[float, float, float]]
                          ) -> Optional[List[Tuple[float, float, float]]]:
        """
        Encuentra el mejor triplete que cumpla las restricciones.

        Si hay múltiples válidos, elige el de menor error de colinealidad.
        """
        if len(blobs) < 3:
            return None

        best_triplet = None
        best_score = float('inf')

        for triplet in combinations(blobs, 3):
            triplet_list = list(triplet)

            if not self._validate_triplet(triplet_list):
                continue

            col_error, spacing_ratio, _, _ = self._calculate_geometry(triplet_list)

            # Score: menor colinealidad + penalización por ratio lejos de 1
            score = col_error + abs(spacing_ratio - 1.0) * 10

            if score < best_score:
                best_score = score
                best_triplet = triplet_list

        return best_triplet

    def detect(self, frame: np.ndarray) -> Tuple[bool, List[LEDDetection], float, float]:
        """
        Detecta los 3 LEDs en el frame.

        Returns:
            (success, leds, geometry_error, spacing_ratio)
        """
        # Convertir a gris
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame

        # Encontrar blobs brillantes
        blobs = self._find_bright_blobs(gray)

        # Buscar triplete válido
        triplet = self._find_best_triplet(blobs)

        if triplet is None:
            # No se encontró patrón válido
            self.frame_count += 1
            return False, [], float('inf'), float('inf')

        # Calcular métricas
        col_error, spacing_ratio, _, _ = self._calculate_geometry(triplet)

        # Ordenar por X y asignar IDs
        sorted_triplet = sorted(triplet, key=lambda p: p[0])

        # Aplicar Kalman para suavizar
        leds = []
        for i, (x, y, conf) in enumerate(sorted_triplet):
            if i not in self.trackers:
                self.trackers[i] = KalmanTracker(x, y)
                smoothed_x, smoothed_y = x, y
            else:
                smoothed_x, smoothed_y = self.trackers[i].update(x, y)

            leds.append(LEDDetection(
                x=smoothed_x,
                y=smoothed_y,
                confidence=conf,
                led_id=i
            ))

        self.last_valid_detection = leds
        self.frame_count += 1

        return True, leds, col_error, spacing_ratio

    def draw_detection(self, frame: np.ndarray, leds: List[LEDDetection],
                       success: bool, col_error: float, spacing_ratio: float
                       ) -> np.ndarray:
        """Dibuja la detección en el frame."""
        if len(frame.shape) == 2:
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        else:
            frame = frame.copy()

        colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0)]  # BGR: Rojo, Verde, Azul

        if success and len(leds) == 3:
            # Dibujar línea entre LEDs
            pts = [(int(led.x), int(led.y)) for led in leds]
            cv2.line(frame, pts[0], pts[1], (255, 255, 0), 2)
            cv2.line(frame, pts[1], pts[2], (255, 255, 0), 2)

            # Dibujar LEDs
            for led in leds:
                color = colors[led.led_id]
                cv2.circle(frame, (int(led.x), int(led.y)), 8, color, -1)
                cv2.circle(frame, (int(led.x), int(led.y)), 12, color, 2)
                cv2.putText(frame, f"L{led.led_id+1}",
                           (int(led.x)+15, int(led.y)+5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            # Status
            cv2.putText(frame, f"OK - Col:{col_error:.1f}px Ratio:{spacing_ratio:.2f}",
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "NO PATRON VALIDO",
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.putText(frame, f"Frame: {self.frame_count}",
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        return frame


# =============================================================================
# PROCESADOR DE VIDEO
# =============================================================================

class VideoProcessor:
    """Procesa video y genera resultados."""

    def __init__(self, video_path: str, output_dir: str = "resultados_estricto/"):
        self.video_path = video_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.detector = StrictLEDDetector()
        self.results: List[FrameResult] = []

    def process(self, max_frames: Optional[int] = None,
                save_frames: bool = True) -> List[FrameResult]:
        """Procesa el video."""

        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise ValueError(f"No se puede abrir: {self.video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(f"\n{'='*70}")
        print("DETECTOR ESTRICTO DE LEDs - VERSIÓN 3.0")
        print(f"{'='*70}")
        print(f"Archivo: {self.video_path}")
        print(f"Total frames: {total_frames}")
        tol = self.detector.spacing_tolerance
        col_err = self.detector.max_collinearity_error
        print(f"Restricciones: colinealidad<{col_err}px, ratio={1-tol:.2f}-{1+tol:.2f}")
        print(f"{'='*70}\n")

        frames_dir = self.output_dir / "frames"
        frames_dir.mkdir(exist_ok=True)

        frame_idx = 0
        success_count = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if max_frames and frame_idx >= max_frames:
                break

            success, leds, col_error, spacing_ratio = self.detector.detect(frame)

            result = FrameResult(
                frame_idx=frame_idx,
                timestamp=frame_idx / fps,
                leds=leds,
                success=success,
                geometry_error=col_error if success else float('inf'),
                spacing_ratio=spacing_ratio if success else float('inf')
            )
            self.results.append(result)

            if success:
                success_count += 1

            # Guardar TODOS los frames procesados
            if save_frames:
                viz = self.detector.draw_detection(
                    frame, leds, success, col_error, spacing_ratio
                )
                cv2.imwrite(str(frames_dir / f"frame_{frame_idx:06d}.jpg"), viz)

            # Progreso cada 100 frames
            if (frame_idx + 1) % 100 == 0:
                pct = 100 * success_count / (frame_idx + 1)
                print(f"  Frame {frame_idx+1}/{total_frames}: {pct:.1f}% válidos")

            frame_idx += 1

        cap.release()

        total = frame_idx
        rate = 100 * success_count / total if total > 0 else 0

        print(f"\n{'='*70}")
        print(f"Frames procesados: {total}")
        print(f"Patrones válidos: {success_count}/{total} ({rate:.1f}%)")
        print(f"{'='*70}\n")

        return self.results

    def save_results(self):
        """Guarda resultados."""

        # Calcular estadísticas
        valid_results = [r for r in self.results if r.success]

        if valid_results:
            col_errors = [r.geometry_error for r in valid_results]
            ratios = [r.spacing_ratio for r in valid_results]

            # Jitter (variación frame-a-frame)
            led_positions = {0: [], 1: [], 2: []}
            for r in valid_results:
                for led in r.leds:
                    led_positions[led.led_id].append((led.x, led.y))

            jitter = {}
            for led_id, positions in led_positions.items():
                if len(positions) > 1:
                    positions = np.array(positions)
                    diffs = np.diff(positions, axis=0)
                    distances = np.linalg.norm(diffs, axis=1)
                    jitter[led_id] = {
                        'mean': float(np.mean(distances)),
                        'std': float(np.std(distances)),
                        'max': float(np.max(distances))
                    }
        else:
            col_errors = []
            ratios = []
            jitter = {}

        stats = {
            'total_frames': len(self.results),
            'valid_frames': len(valid_results),
            'success_rate': len(valid_results) / len(self.results) if self.results else 0,
            'geometry': {
                'collinearity_mean': float(np.mean(col_errors)) if col_errors else None,
                'collinearity_max': float(np.max(col_errors)) if col_errors else None,
                'spacing_ratio_mean': float(np.mean(ratios)) if ratios else None,
                'spacing_ratio_std': float(np.std(ratios)) if ratios else None
            },
            'jitter': jitter
        }

        # Solo reporte de texto (sin JSON)
        report_file = self.output_dir / "reporte.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("REPORTE - DETECTOR ESTRICTO v3.0\n")
            f.write("="*70 + "\n\n")

            f.write(f"Video: {self.video_path}\n")
            f.write(f"Fecha: {datetime.now()}\n\n")

            f.write(f"Frames procesados: {stats['total_frames']}\n")
            valid = stats['valid_frames']
            rate = stats['success_rate'] * 100
            f.write(f"Patrones válidos: {valid} ({rate:.1f}%)\n\n")

            if stats['geometry']['collinearity_mean']:
                f.write("GEOMETRÍA:\n")
                col_mean = stats['geometry']['collinearity_mean']
                col_max = stats['geometry']['collinearity_max']
                ratio_mean = stats['geometry']['spacing_ratio_mean']
                ratio_std = stats['geometry']['spacing_ratio_std']
                f.write(f"  Colinealidad media: {col_mean:.2f}px\n")
                f.write(f"  Colinealidad máxima: {col_max:.2f}px\n")
                f.write(f"  Ratio espaciamiento: {ratio_mean:.3f} ± {ratio_std:.3f}\n\n")

            if jitter:
                f.write("JITTER (variación frame-a-frame):\n")
                for led_id, j in jitter.items():
                    f.write(f"  LED{led_id+1}: media={j['mean']:.2f}px, máx={j['max']:.2f}px\n")

        print(f"✓ Reporte: {report_file}")

        return stats


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Punto de entrada principal del detector."""
    parser = argparse.ArgumentParser(description="Detector Estricto de LEDs v3.0")
    parser.add_argument('video', nargs='?', default='../patron_leds/patron_leds.mp4')
    parser.add_argument('--output', '-o', default='resultados_estricto/')
    parser.add_argument('--max-frames', '-n', type=int, default=None)

    args = parser.parse_args()

    if not os.path.exists(args.video):
        print(f"❌ Video no encontrado: {args.video}")
        return

    processor = VideoProcessor(args.video, args.output)
    processor.process(max_frames=args.max_frames)
    stats = processor.save_results()

    print("\nRESUMEN:")
    print(f"  Tasa de éxito: {stats['success_rate']*100:.1f}%")
    if stats['geometry']['collinearity_mean']:
        print(f"  Colinealidad: {stats['geometry']['collinearity_mean']:.2f}px")
        print(f"  Ratio espaciamiento: {stats['geometry']['spacing_ratio_mean']:.3f}")


if __name__ == "__main__":
    main()
