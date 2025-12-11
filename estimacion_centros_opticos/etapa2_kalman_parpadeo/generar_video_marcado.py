#!/usr/bin/env python3
# pylint: disable=no-member
"""
╔════════════════════════════════════════════════════════════════════════════════╗
║    GENERADOR DE VIDEO CON CENTROS ÓPTICOS MARCADOS                            ║
║                          VERSIÓN 1.0                                          ║
╚════════════════════════════════════════════════════════════════════════════════╝

DESCRIPCIÓN:
    Genera un video de salida donde se marcan los centros ópticos (LEDs)
    detectados en tiempo real. Usa el detector estricto con validación
    geométrica y filtro de Kalman para suavizar las trayectorias.

EJECUCIÓN:
    Desde la carpeta etapa2_kalman_parpadeo/:

    # Opción 1: Video original → Video marcado
    python3 generar_video_marcado.py ../patron_leds/patron_leds.mp4

    # Opción 2: Especificar video de salida
    python3 generar_video_marcado.py ../patron_leds/patron_leds.mp4 -o video_marcado.mp4

    # Opción 3: Con video de parpadeo
    python3 generar_video_marcado.py videos_parpadeo/patron_parpadeo.mp4 -o parpadeo_marcado.mp4

SALIDA:
    - Video MP4 con los 3 LEDs marcados (círculos de colores)
    - Líneas conectando los LEDs cuando se detecta patrón válido
    - Información de estado en cada frame (OK/NO PATRÓN)
    - Métricas de geometría (colinealidad, ratio)

CODIFICACIÓN DE COLORES:
    - LED 1 (izquierda): Rojo
    - LED 2 (centro): Verde
    - LED 3 (derecha): Azul
    - Línea de conexión: Amarillo (cuando patrón válido)
    - Trayectoria: Línea punteada mostrando historial

Autor: Tobias Funes
Fecha: Diciembre 2025
"""

import argparse
import os
from pathlib import Path
from typing import List, Optional
from collections import deque

import cv2
import numpy as np

# Importar el detector del módulo principal
from led_detector_estricto import StrictLEDDetector, LEDDetection


class VideoMarker:
    """
    Genera video con centros ópticos marcados en tiempo real.
    """

    def __init__(self,
                 show_trajectory: bool = True,
                 trajectory_length: int = 30,
                 show_metrics: bool = True):
        """
        Args:
            show_trajectory: Mostrar trayectoria histórica de cada LED
            trajectory_length: Número de frames de historial para trayectoria
            show_metrics: Mostrar métricas de geometría en pantalla
        """
        self.detector = StrictLEDDetector()
        self.show_trajectory = show_trajectory
        self.trajectory_length = trajectory_length
        self.show_metrics = show_metrics

        # Historial de posiciones para trayectoria
        self.trajectories: dict = {0: deque(maxlen=trajectory_length),
                                   1: deque(maxlen=trajectory_length),
                                   2: deque(maxlen=trajectory_length)}

        # Colores para cada LED (BGR)
        self.led_colors = [
            (0, 0, 255),    # LED 0: Rojo
            (0, 255, 0),    # LED 1: Verde
            (255, 0, 0)     # LED 2: Azul
        ]

        # Estadísticas
        self.total_frames = 0
        self.valid_frames = 0

    def _draw_trajectory(self, frame: np.ndarray, led_id: int) -> np.ndarray:
        """Dibuja la trayectoria histórica de un LED."""
        trajectory = list(self.trajectories[led_id])
        if len(trajectory) < 2:
            return frame

        color = self.led_colors[led_id]
        # Color más tenue para la trayectoria
        faded_color = tuple(int(c * 0.5) for c in color)

        for i in range(1, len(trajectory)):
            pt1 = (int(trajectory[i-1][0]), int(trajectory[i-1][1]))
            pt2 = (int(trajectory[i][0]), int(trajectory[i][1]))

            # Grosor decrece con la antigüedad
            thickness = max(1, int(3 * i / len(trajectory)))
            cv2.line(frame, pt1, pt2, faded_color, thickness)

        return frame

    def _draw_detection(self, frame: np.ndarray,
                        leds: List[LEDDetection],
                        success: bool,
                        col_error: float,
                        spacing_ratio: float) -> np.ndarray:
        """Dibuja la detección completa en el frame."""
        frame = frame.copy()

        # Dibujar trayectorias primero (debajo de todo)
        if self.show_trajectory:
            for led_id in range(3):
                frame = self._draw_trajectory(frame, led_id)

        if success and len(leds) == 3:
            # Actualizar trayectorias
            for led in leds:
                self.trajectories[led.led_id].append((led.x, led.y))

            # Dibujar línea de conexión entre LEDs
            pts = [(int(led.x), int(led.y)) for led in leds]
            cv2.line(frame, pts[0], pts[1], (0, 255, 255), 2)  # Amarillo
            cv2.line(frame, pts[1], pts[2], (0, 255, 255), 2)

            # Dibujar cada LED
            for led in leds:
                color = self.led_colors[led.led_id]
                x, y = int(led.x), int(led.y)

                # Círculo exterior (borde)
                cv2.circle(frame, (x, y), 12, color, 2)
                # Círculo interior (relleno)
                cv2.circle(frame, (x, y), 6, color, -1)
                # Centro exacto
                cv2.circle(frame, (x, y), 2, (255, 255, 255), -1)

                # Etiqueta
                label = f"L{led.led_id + 1}"
                cv2.putText(frame, label, (x + 15, y + 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            # Status: OK
            status_color = (0, 255, 0)
            status_text = "PATRON DETECTADO"
        else:
            # Status: NO PATRÓN
            status_color = (0, 0, 255)
            status_text = "SIN PATRON VALIDO"

        # Panel de información superior
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (350, 90), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)

        # Texto de estado
        cv2.putText(frame, status_text, (10, 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

        # Frame actual
        cv2.putText(frame, f"Frame: {self.total_frames}", (10, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Tasa de éxito
        if self.total_frames > 0:
            rate = 100 * self.valid_frames / self.total_frames
            cv2.putText(frame, f"Exito: {rate:.1f}%", (150, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Métricas de geometría (solo si detección válida)
        if self.show_metrics and success:
            cv2.putText(frame, f"Colinealidad: {col_error:.2f}px", (10, 75),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            cv2.putText(frame, f"Ratio: {spacing_ratio:.3f}", (200, 75),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        return frame

    def process_video(self,
                      input_path: str,
                      output_path: str,
                      max_frames: Optional[int] = None,
                      show_preview: bool = False) -> dict:
        """
        Procesa el video y genera la versión marcada.

        Args:
            input_path: Ruta al video de entrada
            output_path: Ruta al video de salida
            max_frames: Límite de frames (None = todo el video)
            show_preview: Mostrar ventana de preview en tiempo real

        Returns:
            Diccionario con estadísticas del procesamiento
        """
        # Abrir video de entrada
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"No se puede abrir: {input_path}")

        # Obtener propiedades
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Crear directorio de salida si no existe
        output_dir = Path(output_path).parent
        if output_dir and not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)

        # Configurar video de salida
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        print(f"\n{'='*70}")
        print("GENERADOR DE VIDEO CON CENTROS ÓPTICOS MARCADOS")
        print(f"{'='*70}")
        print(f"Entrada: {input_path}")
        print(f"Salida:  {output_path}")
        print(f"Resolución: {width}x{height} @ {fps:.1f} FPS")
        print(f"Total frames: {total_frames}")
        print(f"{'='*70}\n")

        self.total_frames = 0
        self.valid_frames = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if max_frames and self.total_frames >= max_frames:
                break

            # Detectar LEDs
            success, leds, col_error, spacing_ratio = self.detector.detect(frame)

            if success:
                self.valid_frames += 1

            # Dibujar detección
            marked_frame = self._draw_detection(
                frame, leds, success, col_error, spacing_ratio
            )

            # Escribir frame marcado
            out.write(marked_frame)

            # Preview opcional
            if show_preview:
                cv2.imshow('Preview - Centros Opticos', marked_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("\n⚠ Cancelado por usuario")
                    break

            self.total_frames += 1

            # Progreso cada 100 frames
            if self.total_frames % 100 == 0:
                pct = 100 * self.valid_frames / self.total_frames
                print(f"  Frame {self.total_frames}/{total_frames}: {pct:.1f}% válidos")

        cap.release()
        out.release()
        if show_preview:
            cv2.destroyAllWindows()

        # Estadísticas finales
        rate = 100 * self.valid_frames / self.total_frames if self.total_frames > 0 else 0

        print(f"\n{'='*70}")
        print("PROCESO COMPLETADO")
        print(f"{'='*70}")
        print(f"Frames procesados: {self.total_frames}")
        print(f"Patrones válidos: {self.valid_frames} ({rate:.1f}%)")
        print(f"Video generado: {output_path}")
        print(f"{'='*70}\n")

        return {
            'total_frames': self.total_frames,
            'valid_frames': self.valid_frames,
            'success_rate': rate,
            'output_path': output_path
        }


def main():
    """Punto de entrada principal."""
    parser = argparse.ArgumentParser(
        description="Genera video con centros ópticos marcados"
    )
    parser.add_argument(
        'video',
        nargs='?',
        default='../patron_leds/patron_leds.mp4',
        help='Video de entrada'
    )
    parser.add_argument(
        '--output', '-o',
        default=None,
        help='Video de salida (default: <nombre>_marcado.mp4)'
    )
    parser.add_argument(
        '--max-frames', '-n',
        type=int,
        default=None,
        help='Límite de frames a procesar'
    )
    parser.add_argument(
        '--preview', '-p',
        action='store_true',
        help='Mostrar preview en tiempo real'
    )
    parser.add_argument(
        '--no-trajectory',
        action='store_true',
        help='No mostrar trayectoria histórica'
    )
    parser.add_argument(
        '--trajectory-length', '-t',
        type=int,
        default=30,
        help='Longitud de trayectoria en frames (default: 30)'
    )

    args = parser.parse_args()

    # Verificar video de entrada
    if not os.path.exists(args.video):
        print(f"❌ Video no encontrado: {args.video}")
        return

    # Generar nombre de salida si no se especifica
    if args.output is None:
        input_path = Path(args.video)
        output_name = f"{input_path.stem}_marcado.mp4"
        args.output = str(input_path.parent / output_name)

    # Crear procesador
    marker = VideoMarker(
        show_trajectory=not args.no_trajectory,
        trajectory_length=args.trajectory_length
    )

    # Procesar video
    stats = marker.process_video(
        args.video,
        args.output,
        max_frames=args.max_frames,
        show_preview=args.preview
    )

    print(f"✓ Video guardado: {stats['output_path']}")
    print(f"✓ Tasa de éxito: {stats['success_rate']:.1f}%")


if __name__ == "__main__":
    main()
