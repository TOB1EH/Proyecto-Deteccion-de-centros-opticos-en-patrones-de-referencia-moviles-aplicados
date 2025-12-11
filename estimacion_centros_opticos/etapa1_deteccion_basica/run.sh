#!/bin/bash

# Script para ejecutar el detector de LEDs - Versión Final v1.0

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
echo "======================================================================"
echo "  DETECTOR ROBUSTO DE CENTROS ÓPTICOS DE LEDs - VERSIÓN FINAL v1.0"
echo "======================================================================"
echo -e "${NC}"

# Configuración por defecto
# El video está en la carpeta padre (../patron_leds/)
VIDEO_PATH="../patron_leds/patron_leds.mp4"
OUTPUT_DIR="resultados/"
MAX_FRAMES=""
NO_DISPLAY=""

# Verificar que Python3 está instalado
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python3 no está instalado${NC}"
    exit 1
fi

# Verificar si existe entorno virtual
if [ -d ".venv" ]; then
    echo -e "${GREEN}✓ Entorno virtual encontrado${NC}"
    PYTHON_CMD=".venv/bin/python"
else
    echo -e "${YELLOW}⚠ No se encontró entorno virtual, usando Python del sistema${NC}"
    PYTHON_CMD="python3"
fi

# Verificar dependencias
echo -e "${YELLOW}Verificando dependencias...${NC}"
$PYTHON_CMD -c "import cv2; print('✓ OpenCV instalado')" 2>/dev/null || {
    echo -e "${RED}✗ OpenCV no está instalado. Instalando...${NC}"
    $PYTHON_CMD -m pip install opencv-python
}

$PYTHON_CMD -c "import numpy; print('✓ NumPy instalado')" 2>/dev/null || {
    echo -e "${RED}✗ NumPy no está instalado. Instalando...${NC}"
    $PYTHON_CMD -m pip install numpy
}

# Verificar que existe el archivo del detector
if [ ! -f "led_detector_final.py" ]; then
    echo -e "${RED}Error: No se encuentra 'led_detector_final.py'${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}======================================================================"
echo "  CONFIGURACIÓN"
echo "======================================================================${NC}"
echo -e "Video de entrada:    ${GREEN}${VIDEO_PATH}${NC}"
echo -e "Directorio salida:   ${GREEN}${OUTPUT_DIR}${NC}"
echo ""
echo "Videos soportados: .mp4, .avi, .mov, .mkv"
echo ""

# Verificar que existe el video
if [ ! -f "$VIDEO_PATH" ]; then
    echo -e "${RED}Error: No se encuentra el video '$VIDEO_PATH'${NC}"
    echo ""
    echo "Por favor, especifica la ruta del video:"
    echo "  ./run.sh /ruta/a/tu/video.mp4"
    echo ""
    exit 1
fi

# Procesar argumentos si se proporcionan
if [ $# -ge 1 ]; then
    VIDEO_PATH="$1"
    echo -e "${YELLOW}Usando video personalizado: $VIDEO_PATH${NC}"
fi

if [ $# -ge 2 ]; then
    OUTPUT_DIR="$2"
    echo -e "${YELLOW}Usando directorio de salida: $OUTPUT_DIR${NC}"
fi

# Ejecutar el detector
echo ""
echo -e "${GREEN}======================================================================"
echo "  EJECUTANDO DETECTOR..."
echo "======================================================================${NC}"
echo ""

$PYTHON_CMD led_detector_final.py "$VIDEO_PATH" \
    --output "$OUTPUT_DIR" \
    $MAX_FRAMES \
    $NO_DISPLAY

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}======================================================================"
    echo "  ✓ COMPLETADO EXITOSAMENTE"
    echo "======================================================================${NC}"
    echo ""
    echo "Los resultados están guardados en: ${GREEN}${OUTPUT_DIR}${NC}"
    echo ""
    echo "Archivos generados:"
    echo "  • ${OUTPUT_DIR}reporte_deteccion.txt  - Reporte de detección"
    echo "  • ${OUTPUT_DIR}frames/                - Frames procesados"
    echo ""
else
    echo -e "${RED}======================================================================"
    echo "  ✗ ERROR EN LA EJECUCIÓN"
    echo "======================================================================${NC}"
    echo ""
    echo "Revisa los mensajes de error anteriores"
    echo ""
fi

exit $EXIT_CODE

