"""
Script de diagnóstico para analizar el video y calibrar parámetros del detector
"""

import cv2
import numpy as np

# pylint: disable=no-member

def diagnose_video(video_path, num_frames=5):
    """Analiza los primeros frames del video para calibrar el detector"""
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: No se puede abrir {video_path}")
        return
    
    print(f"\n{'='*80}")
    print(f"DIAGNÓSTICO DEL VIDEO: {video_path}")
    print(f"{'='*80}\n")
    
    # Información del video
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"Resolución: {width}x{height}")
    print(f"Total de frames: {total_frames}")
    print(f"FPS: {fps:.2f}")
    print(f"Duración: {total_frames/fps:.2f} segundos\n")
    
    frame_idx = 0
    
    while frame_idx < num_frames:
        ret, frame = cap.read()
        if not ret:
            break
        
        print(f"\n{'-'*80}")
        print(f"FRAME {frame_idx}")
        print(f"{'-'*80}")
        
        # Convertir a escala de grises
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Estadísticas básicas
        print(f"Rango de intensidad: [{gray.min()}, {gray.max()}]")
        print(f"Intensidad media: {gray.mean():.2f}")
        print(f"Desviación estándar: {gray.std():.2f}")
        
        # Histograma
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        peak_intensity = np.argmax(hist)
        print(f"Pico de histograma: {peak_intensity} (píxeles brillantes = {hist[peak_intensity][0]:.0f})")
        
        # Análisis de regiones brillantes
        for threshold in [150, 180, 200, 220]:
            _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
            num_pixels = np.count_nonzero(binary)
            percent = (num_pixels / (width * height)) * 100
            print(f"Píxeles > {threshold}: {num_pixels} ({percent:.2f}%)")
        
        # Encontrar contornos en umbralización adaptativa
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, 31, 2)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        print(f"\nContornos encontrados con threshold adaptativo: {len(contours)}")
        
        areas = [cv2.contourArea(c) for c in contours]
        if areas:
            areas_sorted = sorted(areas, reverse=True)
            print(f"Top 5 áreas más grandes: {areas_sorted[:5]}")
            print(f"Área promedio: {np.mean(areas):.2f}")
            print(f"Área mínima: {np.min(areas):.2f}")
            print(f"Área máxima: {np.max(areas):.2f}")
        
        # Detectar blobs
        params = cv2.SimpleBlobDetector_Params()
        params.minThreshold = 100
        params.maxThreshold = 255
        params.filterByArea = True
        params.minArea = 15
        params.maxArea = 800
        params.filterByCircularity = True
        params.minCircularity = 0.5
        params.filterByConvexity = True
        params.minConvexity = 0.7
        
        detector = cv2.SimpleBlobDetector_create(params)
        keypoints = detector.detect(gray)
        print(f"Blobs detectados: {len(keypoints)}")
        if keypoints:
            sizes = [kp.size for kp in keypoints]
            print(f"Tamaños de blobs: {sizes}")
        
        # Detectar círculos con Hough
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 30,
                                   param1=50, param2=30, minRadius=5, maxRadius=40)
        if circles is not None:
            print(f"Círculos detectados (Hough): {circles.shape[1]}")
            for circle in circles[0][:3]:  # Top 3
                print(
                    f"  - Centro: ({circle[0]:.1f}, {circle[1]:.1f}), "
                    f"Radio: {circle[2]:.1f}"
                )
        else:
            print("Círculos detectados (Hough): 0")
        
        # Análisis HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        lower = np.array([0, 0, 200])
        upper = np.array([180, 50, 255])
        mask_hsv = cv2.inRange(hsv, lower, upper)
        hsv_pixels = np.count_nonzero(mask_hsv)
        print(
            f"\nPíxeles HSV (V>200, S<50): {hsv_pixels} "
            f"({(hsv_pixels/(width*height))*100:.2f}%)"
        )
        
        # Guardar frame de diagnóstico
        viz = frame.copy()
        
        # Dibujar contornos grandes
        cv2.drawContours(viz, contours, -1, (0, 255, 0), 2)
        
        # Dibujar blobs
        for kp in keypoints:
            cv2.circle(
                viz,
                (int(kp.pt[0]), int(kp.pt[1])),
                int(kp.size/2),
                (255, 0, 0),
                2
            )
        
        # Dibujar círculos Hough
        if circles is not None:
            for circle in circles[0]:
                cv2.circle(
                    viz,
                    (int(circle[0]), int(circle[1])),
                    int(circle[2]),
                    (0, 0, 255),
                    2
                )
        
        cv2.imwrite(f"resultados/diagnostico_frame_{frame_idx:03d}.jpg", viz)
        print(
            f"✓ Frame guardado: "
            f"resultados/diagnostico_frame_{frame_idx:03d}.jpg"
        )
        
        frame_idx += 1
    
    cap.release()
    
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    diagnose_video("patron_leds/patron_leds.mp4", num_frames=10)
