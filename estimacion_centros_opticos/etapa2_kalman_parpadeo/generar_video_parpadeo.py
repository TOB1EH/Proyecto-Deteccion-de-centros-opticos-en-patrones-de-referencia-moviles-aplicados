#!/usr/bin/env python3
# pylint: disable=no-member
# Nota: cv2 (OpenCV) es una biblioteca C++ con bindings dinámicos.
# Pylint no puede detectar sus miembros en tiempo estático, pero funcionan correctamente.
"""
╔════════════════════════════════════════════════════════════════════════════════╗
║     GENERADOR DE VIDEO CON PARPADEO SIMULADO DE LEDs                          ║
║                                                                                ║
║  Utilidad para crear videos de prueba con diferentes frecuencias de parpadeo  ║
╚════════════════════════════════════════════════════════════════════════════════╝

DESCRIPCIÓN:
    Este script toma un video original y simula el efecto de parpadeo de LEDs,
    alternando frames "encendidos" (original) y "apagados" (oscurecidos).
    
    Es útil para:
    - Probar algoritmos de detección por parpadeo
    - Generar datasets de prueba a diferentes frecuencias
    - Simular comportamiento de LEDs infrarojos parpadeantes

EJECUCIÓN:
    Desde la carpeta etapa2_kalman_parpadeo/:

    # Paso 1: Generar video con parpadeo simulado (10 Hz por defecto)
    python3 generar_video_parpadeo.py ../patron_leds/patron_leds.mp4 \
        videos_parpadeo/patron_parpadeo.mp4

    # Con frecuencia personalizada (5 Hz = parpadeo lento)
    python3 generar_video_parpadeo.py ../patron_leds/patron_leds.mp4 \
        videos_parpadeo/patron_parpadeo_5hz.mp4 --frecuencia 5

SALIDA:
    videos_parpadeo/
    └── patron_parpadeo.mp4       # Video con LEDs parpadeantes simulados

EJEMPLOS ADICIONALES:
    # Parpadeo a 20 Hz (más rápido)
    python3 generar_video_parpadeo.py ../patron_leds/patron_leds.mp4 \
        videos_parpadeo/salida.mp4 -f 20

ARGUMENTOS:
    video_entrada       Ruta al video original (requerido)
    video_salida        Ruta donde guardar el video con parpadeo (requerido)
    -f, --frecuencia    Frecuencia de parpadeo en Hz (default: 10)
    --factor-oscuro     Factor de oscurecimiento 0.0-1.0 (default: 0.3)
                        0.0 = completamente negro, 1.0 = sin cambio

FUNCIONAMIENTO:
    1. Lee el video original frame por frame
    2. Calcula patrón ON/OFF según frecuencia y FPS del video
    3. Frames ON: Se mantienen sin cambios (LEDs visibles)
    4. Frames OFF: Se oscurecen (simula LEDs apagados)
    5. Genera video de salida con el patrón aplicado

NOTAS:
    - La frecuencia efectiva depende del FPS del video original
    - Si frecuencia > FPS/2, el patrón será irregular
    - Recomendado: frecuencia <= FPS/4 para buen contraste

Autor: Tobias Funes
Fecha: Diciembre 2025
Proyecto: Detección de Centros Ópticos en Patrones de Referencia Móviles
"""

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np


def simular_parpadeo(video_entrada, video_salida, frecuencia_hz=10):
    """
    Genera video con parpadeo simulado alternando frames originales y oscurecidos.

    Parámetros:
    -----------
    video_entrada : str
        Ruta al video original
    video_salida : str
        Ruta donde guardar el video con parpadeo
    frecuencia_hz : float
        Frecuencia de parpadeo en Hz (ciclos por segundo)

    Funcionamiento:
    ---------------
    - Frame "ON": Video original (LEDs visibles)
    - Frame "OFF": Video oscurecido excepto regiones muy brillantes (LEDs)
    - Alterna ON/OFF según frecuencia especificada
    """

    print("\n" + "="*60)
    print("GENERACIÓN DE VIDEO CON PARPADEO SIMULADO")
    print("="*60 + "\n")

    # ========================================
    # 1. ABRIR VIDEO DE ENTRADA
    # ========================================
    cap = cv2.VideoCapture(video_entrada)

    if not cap.isOpened():
        print(f"❌ Error: No se pudo abrir el video {video_entrada}")
        sys.exit(1)

    # Obtener propiedades del video
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"📹 Video de entrada: {video_entrada}")
    print(f"   Resolución: {width}x{height}")
    print(f"   FPS: {fps:.2f}")
    print(f"   Total frames: {total_frames}")
    print(f"   Frecuencia parpadeo: {frecuencia_hz} Hz\n")

    # ========================================
    # 2. CALCULAR PATRÓN DE PARPADEO
    # ========================================
    # Determinar cuántos frames por cada estado (ON/OFF)
    frames_por_ciclo = fps / frecuencia_hz
    frames_on = int(frames_por_ciclo / 2)
    frames_off = int(frames_por_ciclo / 2)

    print("⚙️  Patrón de parpadeo:")
    print(f"   Frames ON: {frames_on}")
    print(f"   Frames OFF: {frames_off}")
    print(f"   Ciclo completo: {frames_on + frames_off} frames\n")

    # ========================================
    # 3. CONFIGURAR VIDEO DE SALIDA
    # ========================================
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_salida, fourcc, fps, (width, height))

    if not out.isOpened():
        print(f"❌ Error: No se pudo crear el video de salida {video_salida}")
        cap.release()
        sys.exit(1)

    # ========================================
    # 4. PROCESAR VIDEO FRAME POR FRAME
    # ========================================
    frame_count = 0
    ciclo_pos = 0  # Posición dentro del ciclo ON/OFF

    print("🎬 Procesando video...")
    print("   [", end="", flush=True)
    progreso_anterior = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # ========================================
        # 4.1 DETERMINAR ESTADO (ON/OFF)
        # ========================================
        # Alternar entre ON y OFF según posición en ciclo
        if ciclo_pos < frames_on:
            estado = "ON"
        else:
            estado = "OFF"

        # ========================================
        # 4.2 APLICAR EFECTO SEGÚN ESTADO
        # ========================================
        if estado == "ON":
            # Frame ON: Mantener original (LEDs visibles)
            frame_salida = frame.copy()

        else:  # estado == "OFF"
            # Frame OFF: Oscurecer todo excepto LEDs (puntos muy brillantes)

            # Convertir a escala de grises para analizar brillo
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Crear máscara de regiones MUY brillantes (probable LEDs)
            # Solo píxeles con intensidad > 200 se consideran LEDs
            _, mascara_leds = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

            # Crear frame oscurecido (reducir brillo 90%)
            frame_oscuro = (frame * 0.1).astype(np.uint8)

            # Mantener LEDs visibles en frame oscuro
            mascara_leds_3ch = cv2.cvtColor(mascara_leds, cv2.COLOR_GRAY2BGR)
            frame_salida = np.where(mascara_leds_3ch > 0, frame, frame_oscuro)

        # ========================================
        # 4.3 ESCRIBIR FRAME AL VIDEO DE SALIDA
        # ========================================
        out.write(frame_salida)

        # ========================================
        # 4.4 ACTUALIZAR CONTADOR DE CICLO
        # ========================================
        ciclo_pos += 1
        if ciclo_pos >= (frames_on + frames_off):
            ciclo_pos = 0  # Reiniciar ciclo

        frame_count += 1

        # Mostrar progreso
        progreso = int((frame_count / total_frames) * 50)
        if progreso > progreso_anterior:
            print("█", end="", flush=True)
            progreso_anterior = progreso

    print("] ✓\n")

    # ========================================
    # 5. LIBERAR RECURSOS
    # ========================================
    cap.release()
    out.release()

    print("✅ Video con parpadeo generado exitosamente:")
    print(f"   {video_salida}")
    print(f"   Total frames procesados: {frame_count}\n")


def main():
    """Función principal - parsea argumentos y ejecuta generación de video"""

    parser = argparse.ArgumentParser(
        description='Genera video simulando parpadeo de LEDs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python generar_video_parpadeo.py patron_leds.mp4 patron_parpadeo.mp4
  python generar_video_parpadeo.py patron_leds.mp4 patron_parpadeo.mp4 --frecuencia 15
        """
    )

    parser.add_argument(
        'video_entrada',
        type=str,
        help='Ruta al video original de entrada'
    )

    parser.add_argument(
        'video_salida',
        type=str,
        help='Ruta donde guardar el video con parpadeo'
    )

    parser.add_argument(
        '--frecuencia',
        type=float,
        default=10.0,
        help='Frecuencia de parpadeo en Hz (por defecto: 10 Hz)'
    )

    args = parser.parse_args()

    # Verificar que el video de entrada existe
    if not Path(args.video_entrada).exists():
        print(f"❌ Error: El archivo {args.video_entrada} no existe")
        sys.exit(1)

    # Generar video con parpadeo
    simular_parpadeo(args.video_entrada, args.video_salida, args.frecuencia)


if __name__ == "__main__":
    main()
