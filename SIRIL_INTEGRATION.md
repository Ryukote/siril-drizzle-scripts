# Pokretanje fiDrizzle-MU iz Siril-a

Postoji **3 načina** da pokreneš fiDrizzle-MU direktno iz Siril-a:

---

## Metod 1: GUI iz Siril konzole ⭐ NAJLAKŠE

### Koraci:

1. **Registruj slike u Sirilu**:
   ```
   register pp_light
   ```

2. **Iz Siril konzole, pokreni GUI**:
   ```
   exec python3 /home/user/siril-drizzle-scripts/fidrizzle_mu_gui.py
   ```

3. **U GUI-u**:
   - Klikni "Izaberi slike"
   - Odaberi `r_pp_light_*.fit` slike
   - Izaberi preset ili prilagodi parametre
   - Klikni "POKRENI STACK"

4. **Kad se završi**, učitaj rezultat u Siril:
   ```
   load fidrizzle_result.fits
   ```

---

## Metod 2: Bash skripta iz Siril konzole

### Koraci:

1. **Registruj slike**:
   ```
   register pp_light
   ```

2. **Pokreni bash skriptu** iz Siril konzole:
   ```
   exec bash /home/user/siril-drizzle-scripts/run_fidrizzle_from_siril.sh
   ```

3. **Potvrdi** kada te pita

4. **Učitaj rezultat**:
   ```
   load fidrizzle_result.fits
   ```

---

## Metod 3: Direktna komanda iz Siril konzole

### Za Point Sources (zvezde, kvazari):

```
exec python3 /home/user/siril-drizzle-scripts/siril_fidrizzle_mu.py r_pp_light_*.fit -o fidrizzle_result.fits --psr 0.5 --iterations 65 --gamma 1.0
```

### Za Extended Sources (galaksije, maglice):

```
exec python3 /home/user/siril-drizzle-scripts/siril_fidrizzle_mu.py r_pp_light_*.fit -o fidrizzle_result.fits --psr 0.5 --iterations 100 --gamma 1.0
```

### Za High Resolution (4x finer):

```
exec python3 /home/user/siril-drizzle-scripts/siril_fidrizzle_mu.py r_pp_light_*.fit -o fidrizzle_result.fits --psr 0.25 --iterations 150 --gamma 1.0
```

---

## Metod 4: Kreiraj Custom Command u Sirilu

### Setup:

1. **Kreiraj command fajl**:
   ```bash
   mkdir -p ~/.config/siril/scripts
   cp /home/user/siril-drizzle-scripts/fidrizzle_mu.ssf ~/.config/siril/scripts/
   ```

2. **Uredi fajl** i prilagodi putanje:
   ```bash
   nano ~/.config/siril/scripts/fidrizzle_mu.ssf
   ```

3. **U Sirilu**, pokreni sa:
   ```
   load fidrizzle_mu.ssf
   ```

---

## Kompletni Workflow - Korak po Korak

### 1. Priprema slika

U Sirilu:
```
cd /path/to/your/lights
convert light -out=../process
cd ../process
```

### 2. Registracija

```
register pp_light
```

Siril će kreirati `r_pp_light_00001.fit`, `r_pp_light_00002.fit`, itd.

### 3. fiDrizzle-MU procesiranje

**Opcija A - GUI (preporučeno)**:
```
exec python3 /home/user/siril-drizzle-scripts/fidrizzle_mu_gui.py
```

**Opcija B - Bash skripta**:
```
exec bash /home/user/siril-drizzle-scripts/run_fidrizzle_from_siril.sh
```

**Opcija C - Direktna komanda**:
```
exec python3 /home/user/siril-drizzle-scripts/siril_fidrizzle_mu.py r_pp_light_*.fit -o drizzled.fits --psr 0.5 --iterations 65
```

### 4. Učitavanje rezultata

```
load fidrizzle_result.fits
```

ili (ako si koristio drugo ime):
```
load drizzled.fits
```

### 5. Dalja obrada

Nastavi sa standardnim Siril workflow-om:
- Background extraction
- Color calibration
- Histogram stretch
- Itd.

---

## Troubleshooting

### "Python script not found"

Provjeri putanju:
```bash
ls -la /home/user/siril-drizzle-scripts/siril_fidrizzle_mu.py
```

Ako ne postoji, prilagodi putanju u komandama.

### "No images found"

Proveri da li slike postoje:
```bash
ls r_pp_light_*.fit
```

Ako ne postoje, prvo registruj slike sa `register pp_light`.

### "Module not found"

Instaliraj zavisnosti:
```bash
pip install numpy scipy astropy
```

Za GUI:
```bash
pip install PyQt6
```

### Siril ne može pokrenuti Python

Proveri da li Python radi:
```bash
python3 --version
```

Ako je instaliran, koristi punu putanju:
```
exec /usr/bin/python3 /home/user/siril-drizzle-scripts/siril_fidrizzle_mu.py ...
```

---

## Napomene

1. **Registracija je obavezna**: fiDrizzle-MU radi najbolje sa registrovanim slikama
2. **Prilagodi parametre**: Point sources koriste manje iteracija od extended sources
3. **Pozitivnost**: Ostavi uključenu za smanjenje artefakata
4. **Output fajl**: Uvek specificuj `-o` opciju

---

## Preporučeni parametri

| Tip objekta | PSR | Iteracije | Gamma |
|-------------|-----|-----------|-------|
| Point sources (zvezde) | 0.5 | 65 | 1.0 |
| Extended (galaksije) | 0.5 | 100 | 1.0 |
| High resolution | 0.25 | 150 | 1.0 |

---

**Za više informacija**, pogledaj:
- `FIDRIZZLE_MU_GUIDE.md` - Kompletna dokumentacija
- `README.md` - Opšti pregled
- `documentation/fiDrizzle-MU.pdf` - Naučni rad
