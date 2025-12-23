#!/bin/bash
# Wrapper skripta za pokretanje fiDrizzle-MU iz Siril-a
# ======================================================
#
# Instalacija:
#   1. Kopiraj ovaj fajl u folder sa slikama
#   2. U Sirilu, posle registracije, pokreni:
#      exec bash run_fidrizzle_from_siril.sh
#
# Ili pokreni direktno iz terminala u folderu sa slikama

# Boje za terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}fiDrizzle-MU - Brzi Iterativni Drizzle${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""

# Parametri - PRILAGODI PO POTREBI
PSR=0.5
ITERATIONS=65
GAMMA=1.0
OUTPUT="fidrizzle_result.fits"

# Putanja do Python skripte
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
FIDRIZZLE_SCRIPT="${SCRIPT_DIR}/siril_fidrizzle_mu.py"

# Proveri da li postoji skripta
if [ ! -f "$FIDRIZZLE_SCRIPT" ]; then
    echo -e "${RED}GREŠKA: Nije pronađena skripta: ${FIDRIZZLE_SCRIPT}${NC}"
    exit 1
fi

# Pronađi registrovane slike
echo -e "${GREEN}Tražim registrovane slike...${NC}"
IMAGES=$(ls r_pp_light_*.fit 2>/dev/null | head -n 100)

if [ -z "$IMAGES" ]; then
    echo -e "${RED}GREŠKA: Nisu pronađene registrovane slike (r_pp_light_*.fit)${NC}"
    echo ""
    echo "Prvo registruj slike u Sirilu sa:"
    echo "  register pp_light"
    exit 1
fi

COUNT=$(echo "$IMAGES" | wc -l)
echo -e "${GREEN}✓ Pronađeno ${COUNT} slika${NC}"
echo ""

# Prikaži parametre
echo "Parametri:"
echo "  PSR (rezolucija): ${PSR}"
echo "  Iteracije: ${ITERATIONS}"
echo "  Gamma: ${GAMMA}"
echo "  Output: ${OUTPUT}"
echo ""

# Pitaj za potvrdu
read -p "Nastavi sa procesiranjem? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Otkazano."
    exit 0
fi

echo ""
echo -e "${BLUE}Pokrećem fiDrizzle-MU...${NC}"
echo ""

# Pokreni Python skriptu
python3 "$FIDRIZZLE_SCRIPT" $IMAGES \
    -o "$OUTPUT" \
    --psr "$PSR" \
    --iterations "$ITERATIONS" \
    --gamma "$GAMMA"

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}================================================================${NC}"
    echo -e "${GREEN}✓ USPEŠNO ZAVRŠENO!${NC}"
    echo -e "${GREEN}================================================================${NC}"
    echo ""
    echo "Rezultat sačuvan u: ${OUTPUT}"
    echo ""
    echo "Učitaj u Sirilu sa:"
    echo "  load ${OUTPUT}"
else
    echo -e "${RED}================================================================${NC}"
    echo -e "${RED}✗ GREŠKA: Procesiranje neuspešno${NC}"
    echo -e "${RED}================================================================${NC}"
    exit $EXIT_CODE
fi
