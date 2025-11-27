"""
╔════════════════════════════════════════════════════════════════════════════════╗
║         GENERADOR DE VIDEO CON CENTROS ÓPTICOS MARCADOS                      ║
║                          Versión Final v1.0                                   ║
╚════════════════════════════════════════════════════════════════════════════════╝

DESCRIPCIÓN:
  Procesa un video y genera otro video de salida con:
  - Centros ópticos de LEDs marcados con círculos de colores
  - Etiquetas de identificación (LED1, LED2, LED3)
  - Promedio acumulado mostrado con cruz
  - Trayectorias opcionales
  - Estadísticas de error en pantalla

CARACTERÍSTICAS:
  • Genera video MP4 con marcadores visuales
  • Muestra posición instantánea y promedio acumulado
  • Calcula y muestra error de estimación
  • Permite controlar tamaño de marcadores y colores

EJEMPLO DE USO:
  python3 led_detector_video_output.py patron_leds/patron_leds.mp4 \
      --output video_marcado.mp4
"""

# Standard library imports
import argparse
import sys
from pathlib import Path
from typing import List, Tuple, Dict

# Third-party imports
import cv2
import numpy as np

# pylint: disable=no-member


class VideoMarker:
    """
    Procesa video y genera salida con centros ópticos marcados
    """

    def __init__(self, min_led_area: int = 30, max_led_area: int = 300):
        """
        Inicializa el marcador de video

        Args:
            min_led_area: Área mínima del LED en píxeles²
            max_led_area: Área máxima del LED en píxeles²
        """
        self.min_led_area = min_led_area
        self.max_led_area = max_led_area
        self.expected_leds = 3

        # Parámetros de procesamiento
        self.gaussian_kernel = (5, 5)
        self.median_kernel = 5

        # Estadísticas acumuladas por LED
        self.led_positions = {0: [], 1: [], 2: []}
        
        # Colores para cada LED (BGR)
        self.led_colors = [
            (0, 0, 255),    # LED 1: Rojo
            (0, 255, 0),    # LED 2: Verde
            (255, 0, 0)     # LED 3: Azul
        ]
        
        self.led_names = ["LED1", "LED2", "LED3"]

        # Variables de rastreo
        self.last_positions = None
        self.frame_count = 0

    def _preprocess(self, frame: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Preprocesa el frame"""
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame.copy()

        blurred = cv2.GaussianBlur(gray, self.gaussian_kernel, 1.5)
        filtered = cv2.medianBlur(blurred, self.median_kernel)

        return gray, filtered

    def _detect_leds(self, gray: np.ndarray) -> List[Tuple[float, float, float]]:
        """Detecta LEDs en el frame"""
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)

        num_labels, _, stats, _ = cv2.connectedComponentsWithStats(
            thresh, connectivity=8
        )

        leds = []
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]

            if self.min_led_area < area < self.max_led_area:
                x = stats[i, cv2.CC_STAT_LEFT] + stats[i, cv2.CC_STAT_WIDTH] / 2
                y = stats[i, cv2.CC_STAT_TOP] + stats[i, cv2.CC_STAT_HEIGHT] / 2

                bbox_area = (stats[i, cv2.CC_STAT_WIDTH] * 
                            stats[i, cv2.CC_STAT_HEIGHT])
                confidence = min(1.0, area / bbox_area) if bbox_area > 0 else 0.5

                leds.append((x, y, confidence))

        return leds

    def _assign_led_ids(
        self,
        detections: List[Tuple[float, float, float]]
    ) -> List[Tuple[int, float, float, float]]:
        """Asigna IDs a las detecciones"""
        detections = sorted(detections, key=lambda d: d[0])

        if not detections:
            return []

        if (self.last_positions is None or 
            len(self.last_positions) != len(detections)):
            self.last_positions = detections
            return [(i, x, y, c) for i, (x, y, c) in enumerate(detections)]

        assigned = []
        used_ids = set()
        max_jump_dist = 150

        for x_new, y_new, conf_new in detections:
            best_id = -1
            best_dist = float('inf')

            for old_id, (x_old, y_old, _) in enumerate(self.last_positions):
                if old_id in used_ids:
                    continue

                dist = np.sqrt((x_old - x_new) ** 2 + (y_old - y_new) ** 2)

                if dist < max_jump_dist and dist < best_dist:
                    best_dist = dist
                    best_id = old_id

            if best_id != -1:
                assigned.append((best_id, x_new, y_new, conf_new))
                used_ids.add(best_id)
            else:
                for led_id in range(self.expected_leds):
                    if led_id not in used_ids:
                        assigned.append((led_id, x_new, y_new, conf_new))
                        used_ids.add(led_id)
                        break

        self.last_positions = [(x, y, c) for _, x, y, c in assigned]
        return assigned

    def _calculate_statistics(self, led_id: int) -> Dict:
        """Calcula estadísticas acumuladas"""
        positions = self.led_positions[led_id]

        if len(positions) < 2:
            return {
                'mean_x': positions[0][0] if positions else 0,
                'mean_y': positions[0][1] if positions else 0,
                'std_total': 0,
                'count': len(positions)
            }

        positions_array = np.array(positions)
        mean_pos = np.mean(positions_array, axis=0)

        deviations = np.sqrt(np.sum((positions_array - mean_pos) ** 2, axis=1))
        std_total = np.std(deviations)

        return {
            'mean_x': mean_pos[0],
            'mean_y': mean_pos[1],
            'std_total': std_total,
            'count': len(positions)
        }

    def _draw_markers(
        self,
        frame: np.ndarray,
        assigned_detections: List[Tuple[int, float, float, float]],
        show_trails: bool = True,
        show_stats: bool = True
    ) -> np.ndarray:
        """
        Dibuja marcadores en el frame
        """
        marked_frame = frame.copy()

        # Dibujar cada LED detectado
        for led_id, x, y, _ in assigned_detections:
            if led_id < self.expected_leds:
                # Guardar posición
                self.led_positions[led_id].append((x, y))

                color = self.led_colors[led_id]

                # Círculo exterior (más grande)
                cv2.circle(marked_frame, (int(x), int(y)), 12, color, 2)
                
                # Círculo interior (punto central)
                cv2.circle(marked_frame, (int(x), int(y)), 4, color, -1)

                # Etiqueta del LED
                cv2.putText(
                    marked_frame,
                    self.led_names[led_id],
                    (int(x) + 15, int(y) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    color,
                    2
                )

                # Calcular estadísticas
                stats = self._calculate_statistics(led_id)

                # Dibujar promedio acumulado (cruz grande)
                if stats['count'] > 5:
                    mean_x, mean_y = int(stats['mean_x']), int(stats['mean_y'])
                    cross_size = 20
                    
                    # Cruz en el promedio
                    cv2.line(
                        marked_frame,
                        (mean_x - cross_size, mean_y),
                        (mean_x + cross_size, mean_y),
                        color,
                        3
                    )
                    cv2.line(
                        marked_frame,
                        (mean_x, mean_y - cross_size),
                        (mean_x, mean_y + cross_size),
                        color,
                        3
                    )

                    # Círculo de error (radio = desviación estándar)
                    if stats['std_total'] > 0:
                        cv2.circle(
                            marked_frame,
                            (mean_x, mean_y),
                            int(stats['std_total']),
                            color,
                            1
                        )

                    # Línea conectando detección actual con promedio
                    cv2.line(
                        marked_frame,
                        (int(x), int(y)),
                        (mean_x, mean_y),
                        color,
                        1,
                        cv2.LINE_AA
                    )

                # Dibujar trayectoria (últimos 30 puntos)
                if show_trails and len(self.led_positions[led_id]) > 1:
                    trail = self.led_positions[led_id][-30:]
                    for i in range(len(trail) - 1):
                        pt1 = (int(trail[i][0]), int(trail[i][1]))
                        pt2 = (int(trail[i+1][0]), int(trail[i+1][1]))
                        cv2.line(marked_frame, pt1, pt2, color, 2, cv2.LINE_AA)

        # Mostrar estadísticas en pantalla
        if show_stats:
            # Fondo semi-transparente para texto
            overlay = marked_frame.copy()
            cv2.rectangle(overlay, (10, 10), (400, 150), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, marked_frame, 0.3, 0, marked_frame)

            # Título
            cv2.putText(
                marked_frame,
                f"Frame: {self.frame_count}",
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            # Estadísticas por LED
            y_offset = 65
            for led_id in range(self.expected_leds):
                if assigned_detections and any(
                    lid == led_id for lid, _, _, _ in assigned_detections
                ):
                    stats = self._calculate_statistics(led_id)
                    color = self.led_colors[led_id]
                    
                    text = (
                        f"{self.led_names[led_id]}: "
                        f"({stats['mean_x']:.1f}, {stats['mean_y']:.1f}) "
                        f"Error: {stats['std_total']:.2f}px"
                    )
                    
                    cv2.putText(
                        marked_frame,
                        text,
                        (20, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        color,
                        1
                    )
                    y_offset += 25

        return marked_frame

    def process_video(
        self,
        input_path: str,
        output_path: str,
        show_trails: bool = True,
        show_stats: bool = True
    ):
        """
        Procesa el video completo y genera salida con marcadores
        """
        cap = cv2.VideoCapture(input_path)

        if not cap.isOpened():
            print(f"✗ Error: No se puede abrir {input_path}")
            return False

        # Obtener propiedades del video
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(f"\n{'='*80}")
        print("GENERADOR DE VIDEO CON MARCADORES")
        print(f"{'='*80}")
        print(f"Entrada: {input_path}")
        print(f"Salida: {output_path}")
        print(f"Resolución: {width}x{height}")
        print(f"FPS: {fps:.2f}")
        print(f"Total frames: {total_frames}")
        print(f"{'='*80}\n")

        # Crear writer de video
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        if not out.isOpened():
            print(f"✗ Error: No se puede crear {output_path}")
            cap.release()
            return False

        print("Procesando video...")
        successful_detections = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            self.frame_count += 1

            # Detectar LEDs
            gray, _ = self._preprocess(frame)
            detections = self._detect_leds(gray)
            assigned = self._assign_led_ids(detections)

            # Marcar frame
            marked_frame = self._draw_markers(
                frame,
                assigned,
                show_trails=show_trails,
                show_stats=show_stats
            )

            # Escribir frame al video de salida
            out.write(marked_frame)

            if len(assigned) == self.expected_leds:
                successful_detections += 1

            # Progreso cada 30 frames
            if self.frame_count % 30 == 0:
                progress = (self.frame_count / total_frames) * 100
                rate = (successful_detections / self.frame_count) * 100
                print(
                    f"  Progreso: {progress:.1f}% "
                    f"({self.frame_count}/{total_frames}) - "
                    f"Éxito: {rate:.1f}%"
                )

        # Limpiar
        cap.release()
        out.release()

        # Reporte final
        print(f"\n{'='*80}")
        print("PROCESO COMPLETADO")
        print(f"{'='*80}")
        print(f"Frames procesados: {self.frame_count}")
        print(f"Detecciones exitosas: {successful_detections}/{self.frame_count}")
        print(
            f"Tasa de éxito: "
            f"{(successful_detections/self.frame_count)*100:.2f}%"
        )
        print(f"\nVideo guardado: {output_path}")
        print(f"{'='*80}\n")

        # Estadísticas finales por LED
        print("ESTADÍSTICAS FINALES:\n")
        for led_id in range(self.expected_leds):
            stats = self._calculate_statistics(led_id)
            print(f"{self.led_names[led_id]}:")
            print(f"  Posición promedio: ({stats['mean_x']:.2f}, {stats['mean_y']:.2f})")
            print(f"  Error (σ): {stats['std_total']:.4f} píxeles")
            print(f"  Muestras: {stats['count']}/{self.frame_count}")
            print()

        return True


def main():
    """Punto de entrada principal"""
    parser = argparse.ArgumentParser(
        description="Genera video con centros ópticos de LEDs marcados"
    )
    parser.add_argument('input', help='Video de entrada')
    parser.add_argument(
        '--output',
        '-o',
        default='video_marcado.mp4',
        help='Video de salida (default: video_marcado.mp4)'
    )
    parser.add_argument(
        '--min-area',
        type=int,
        default=30,
        help='Área mínima del LED'
    )
    parser.add_argument(
        '--max-area',
        type=int,
        default=300,
        help='Área máxima del LED'
    )
    parser.add_argument(
        '--no-trails',
        action='store_true',
        help='No mostrar trayectorias'
    )
    parser.add_argument(
        '--no-stats',
        action='store_true',
        help='No mostrar estadísticas'
    )
    args = parser.parse_args()

    # Verificar que existe el video de entrada
    if not Path(args.input).exists():
        print(f"\n✗ Error: No se encuentra '{args.input}'\n")
        sys.exit(1)

    # Crear procesador
    marker = VideoMarker(
        min_led_area=args.min_area,
        max_led_area=args.max_area
    )

    # Procesar video
    try:
        success = marker.process_video(
            args.input,
            args.output,
            show_trails=not args.no_trails,
            show_stats=not args.no_stats
        )

        if success:
            print(f"✓ Video generado exitosamente: {args.output}")
            sys.exit(0)
        else:
            print("✗ Error al generar el video")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n✓ Interrumpido por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
