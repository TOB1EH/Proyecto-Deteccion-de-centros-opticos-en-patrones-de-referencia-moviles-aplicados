#!/bin/bash

# Script para ejecutar el detector en tiempo real

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
echo "======================================================================"
echo "  DETECTOR DE LEDs EN TIEMPO REAL - Modo Visualización"
echo "======================================================================"
echo -e "${NC}"

# Configuración por defecto
VIDEO_PATH="${1:-patron_leds/patron_leds.mp4}"

# Verificar si existe entorno virtual
if [ -d ".venv" ]; then
    echo -e "${GREEN}✓ Entorno virtual encontrado${NC}"
    PYTHON_CMD=".venv/bin/python"
else
    echo -e "${YELLOW}⚠ Usando Python del sistema${NC}"
    PYTHON_CMD="python3"
fi

# Verificar que existe el archivo
if [ ! -f "led_detector_live.py" ]; then
    echo -e "${RED}✗ Error: No se encuentra 'led_detector_live.py'${NC}"
    exit 1
fi

# Verificar que existe el video
if [ ! -f "$VIDEO_PATH" ]; then
    echo -e "${RED}✗ Error: No se encuentra el video '$VIDEO_PATH'${NC}"
    echo ""
    echo "Uso: ./run_live.sh [video.mp4]"
    echo ""
    exit 1
fi

echo ""
echo -e "${BLUE}======================================================================"
echo "  INSTRUCCIONES"
echo "======================================================================${NC}"
echo ""
echo "El detector mostrará:"
echo "  • Detecciones instantáneas (círculos de colores)"
echo "  • Posición promedio acumulada (cruz)"
echo "  • Trayectoria reciente (línea)"
echo "  • Círculo de error (radio = desviación estándar)"
echo "  • Estadísticas en tiempo real (panel derecho)"
echo ""
echo "Controles disponibles:"
echo "  ESPACIO - Pausar/Reanudar reproducción"
echo "  Q       - Salir del programa"
echo "  R       - Reiniciar estadísticas"
echo "  S       - Guardar frame actual"
echo "  H       - Mostrar/Ocultar controles"
echo "  T       - Mostrar/Ocultar trayectorias"
echo ""
echo -e "${YELLOW}Presiona cualquier tecla para continuar...${NC}"
read -n 1 -s

echo ""
echo -e "${GREEN}======================================================================"
echo "  EJECUTANDO..."
echo "======================================================================${NC}"
echo ""

# Ejecutar el detector
$PYTHON_CMD led_detector_live.py "$VIDEO_PATH"

echo ""
echo -e "${GREEN}✓ Finalizado${NC}"
echo ""
