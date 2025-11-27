#!/bin/bash

# Script para generar video con centros ópticos marcados

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}"
echo "======================================================================"
echo "  GENERADOR DE VIDEO CON CENTROS ÓPTICOS MARCADOS"
echo "======================================================================"
echo -e "${NC}"

# Video de entrada
VIDEO_INPUT="${1:-patron_leds/patron_leds.mp4}"
VIDEO_OUTPUT="${2:-video_marcado.mp4}"

# Verificar entorno virtual
if [ -d ".venv" ]; then
    echo -e "${GREEN}✓ Usando entorno virtual${NC}"
    PYTHON_CMD=".venv/bin/python"
else
    echo -e "${YELLOW}⚠ Usando Python del sistema${NC}"
    PYTHON_CMD="python3"
fi

# Verificar que existe el video
if [ ! -f "$VIDEO_INPUT" ]; then
    echo -e "${RED}✗ Error: No se encuentra '$VIDEO_INPUT'${NC}"
    echo ""
    echo "Uso: ./generate_marked_video.sh [video_entrada.mp4] [video_salida.mp4]"
    echo ""
    exit 1
fi

echo ""
echo -e "${BLUE}Configuración:${NC}"
echo "  Video entrada:  $VIDEO_INPUT"
echo "  Video salida:   $VIDEO_OUTPUT"
echo ""
echo "El video generado mostrará:"
echo "  • Círculos de colores en centros ópticos detectados"
echo "  • Etiquetas de identificación (LED1, LED2, LED3)"
echo "  • Cruz en posición promedio acumulada"
echo "  • Trayectoria de movimiento"
echo "  • Estadísticas de error en pantalla"
echo ""

# Ejecutar
echo -e "${GREEN}Procesando video...${NC}"
echo ""

$PYTHON_CMD led_detector_video_output.py "$VIDEO_INPUT" --output "$VIDEO_OUTPUT"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}======================================================================"
    echo "  ✓ VIDEO GENERADO EXITOSAMENTE"
    echo "======================================================================${NC}"
    echo ""
    echo "Video guardado en: ${GREEN}$VIDEO_OUTPUT${NC}"
    echo ""
    echo "Puedes reproducirlo con:"
    echo "  vlc $VIDEO_OUTPUT"
    echo "  mpv $VIDEO_OUTPUT"
    echo ""
else
    echo ""
    echo -e "${RED}✗ Error al generar el video${NC}"
    echo ""
fi

exit $EXIT_CODE
