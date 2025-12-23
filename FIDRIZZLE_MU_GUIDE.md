# fiDrizzle-MU Guide

## Šta je fiDrizzle-MU?

**fiDrizzle-MU (Fast Iterative Drizzle with Multiplicative Updates)** je napredni algoritam za stackiranje (kombinovanje) više dithered slika koji daje **značajno bolje rezultate** od standardnog Drizzle metoda.

### Prednosti fiDrizzle-MU:

✅ **Brža konvergencija** - potrebno 5x manje iteracija od fiDrizzle-DC
✅ **Bolja dekorelacija piksela** - smanjuje noise između susednih piksela
✅ **Visoka rezolucija** - rekonstruiše fine detalje i sharp strukture
✅ **Supresija ringing efekata** - pozitivnost constraint eliminiše artefakte
✅ **Optimalno za JWST/HST podatke** - posebno za under-sampled slike

### Naučna osnova:

Algoritam je baziran na radu:
> "fiDrizzle-MU: A Fast Iterative Drizzle with Multiplicative Updates"
> Shen Zhang et al., arXiv:2511.09881v1

## Kako funkcioniše?

fiDrizzle-MU koristi **iterativni multiplicative update** umesto aditivnih korekcija:

```
F_(i+1) = F_i × (R_i)^γ
```

Gde:
- `F_i` = slika u i-toj iteraciji
- `R_i` = ratio korekcija (originalna slika / simulirana slika)
- `γ` = step-size parametar (default: 1.0)

### Koraci algoritma:

1. **Početni Drizzle**: Kombinuj sve slike standardnim shift-and-add metodom → `F_0`
2. **Iterativno poboljšanje**:
   - Simuliraj kako bi svaka input slika izgledala iz trenutne `F_i`
   - Izračunaj ratio `I_k / G_k` (original / simuliran)
   - Drizzle sve ratio slike nazad na fine grid
   - Multiplikuj `F_i` sa ratio slikom → `F_(i+1)`
3. **Positivity constraint**: Ako pikseli postanu negativni, vrati ih na prethodnu vrednost
4. **Ponavljaj** dok se ne postigne konvergencija

---

## Upotreba

### 1. Osnovni primer

Najjednostavnije - ako su slike već registrovane u Sirilu:

```bash
./siril_fidrizzle_mu.py registered_*.fit -o result.fits
```

### 2. Sa custom parametrima

```bash
./siril_fidrizzle_mu.py image_*.fit -o result.fits \
    --psr 0.5 \
    --iterations 100 \
    --gamma 1.0
```

### 3. Korišćenje shift podataka

Ako imaš file sa shift podacima (dx, dy za svaku sliku):

```bash
./siril_fidrizzle_mu.py image_*.fit -o result.fits \
    --shifts shifts.txt
```

Format `shifts.txt`:
```
# dx    dy
0.0     0.0
0.5     0.3
-0.2    0.7
1.1     -0.4
...
```

### 4. Bez positivity constraint

Ako želiš da dozvolis negativne piksele (npr. za testiranje):

```bash
./siril_fidrizzle_mu.py image_*.fit -o result.fits \
    --no-positivity
```

---

## Parametri

### `--psr` (Pixel Scale Ratio)

**Default**: `0.5`

Odnos veličine output piksela prema input pikselima:
- `PSR = 0.5` → output pikseli su 2x manji (2x bolja rezolucija) ✓ **Preporučeno**
- `PSR = 0.25` → output pikseli su 4x manji (4x bolja rezolucija)
- `PSR = 0.1` → output pikseli su 10x manji (10x bolja rezolucija)

**Napomena**: Manji PSR = bolja rezolucija, ali više iteracija potrebno za konvergenciju.

### `--gamma` (Step-size parametar)

**Default**: `1.0`

Kontroliše brzinu konvergencije:
- `gamma = 1.0` → standardna brzina ✓ **Preporučeno**
- `gamma > 1.0` → brža konvergencija (ali može biti nestabilno)
- `gamma < 1.0` → sporija konvergencija (konzervativnije)

**Napomena**: Rad preporučuje `gamma = 1` kao teoretski opravdan izbor za stabilnost.

### `--iterations` (Maksimalni broj iteracija)

**Default**: `100`

Broj iterativnih koraka:
- **10-30 iteracija**: Za brze rezultate sa manje dithered slika
- **50-100 iteracija**: Za optimalne rezultate (rad koristi 65 iteracija za JWST)
- **100+ iteracija**: Za ekstremno fine detalje, ali opasan od overfitting-a

**Napomena**: Algoritam će automatski stati ako postigne konvergenciju.

### `--no-positivity`

**Default**: Positivity constraint je **uključen**

Ako se specificira `--no-positivity`:
- Dozvoljava negativne vrednosti piksela
- Može dovesti do ringing artefakata
- Korisno samo za dijagnostiku/istraživanje

**Preporuka**: NEMOJ koristiti ovu opciju osim ako ne znaš šta radiš!

---

## Workflow sa Siril-om

### Kompletna procedura:

#### Korak 1: Registruj slike u Sirilu

1. Otvori Siril
2. Učitaj sekvencu slika
3. Pokreni registraciju:
   ```
   register pp_light
   ```
4. Siril će kreirati `r_pp_light_*.fit` slike

#### Korak 2: Pokreni fiDrizzle-MU

```bash
./siril_fidrizzle_mu.py r_pp_light_*.fit -o fidrizzle_result.fits \
    --psr 0.5 \
    --iterations 75
```

#### Korak 3: Učitaj rezultat u Siril

1. U Sirilu: `File → Open`
2. Izaberi `fidrizzle_result.fits`
3. Nastavi sa dalјom obradom (color balance, stretch, itd.)

---

## Primer Output-a

Kada pokreneš skriptu, videćeš:

```
[fiDrizzle-MU] ============================================================
[fiDrizzle-MU] Starting fiDrizzle-MU processing
[fiDrizzle-MU] ============================================================
[fiDrizzle-MU] Parameters: PSR=0.5, gamma=1.0, max_iter=100, positivity=True
[fiDrizzle-MU] Loading 20 dithered images...
[fiDrizzle-MU] Input image shape: (2048, 2048)
[fiDrizzle-MU] Output image shape: (4096, 4096) (PSR=0.5)
[fiDrizzle-MU] Creating initial drizzle (F_0)...
[fiDrizzle-MU] Initial drizzle complete. Non-zero pixels: 16777216
[fiDrizzle-MU]
[fiDrizzle-MU] Starting iterations...
[fiDrizzle-MU] Iteration   1: rel_change=4.523156e-02, mean_flux=152.34, max_flux=65432.12
[fiDrizzle-MU] Iteration  10: rel_change=1.234567e-03, mean_flux=153.21, max_flux=65521.34
[fiDrizzle-MU] Iteration  20: rel_change=5.432167e-04, mean_flux=153.45, max_flux=65534.56
[fiDrizzle-MU] Iteration  30: rel_change=2.345678e-04, mean_flux=153.56, max_flux=65542.78
[fiDrizzle-MU] Iteration  40: rel_change=1.234567e-04, mean_flux=153.62, max_flux=65547.89
[fiDrizzle-MU] Iteration  50: rel_change=6.543210e-05, mean_flux=153.65, max_flux=65550.12
[fiDrizzle-MU] Iteration  60: rel_change=3.456789e-05, mean_flux=153.67, max_flux=65551.34
[fiDrizzle-MU] Iteration  65: rel_change=2.345678e-05, mean_flux=153.68, max_flux=65551.89
[fiDrizzle-MU] ============================================================
[fiDrizzle-MU] Processing complete in 245.67 seconds
[fiDrizzle-MU] Final image shape: (4096, 4096)
[fiDrizzle-MU] Total flux: 26482134.56
[fiDrizzle-MU] ============================================================
[fiDrizzle-MU] Saving result to fidrizzle_result.fits...
[fiDrizzle-MU] Result saved successfully

✓ fiDrizzle-MU processing complete!
  Output: fidrizzle_result.fits
  Shape: (4096, 4096)
  Total flux: 26482134.56
```

---

## Kada koristiti fiDrizzle-MU?

### ✅ KORISTI fiDrizzle-MU kada:

- Imaš **multiple dithered exposures** (10+ slika)
- Trebaš **maksimalnu rezoluciju** i fine detalje
- Radiš sa **under-sampled slikama** (HST, JWST, neke kamere)
- Želiš **najbolju moguću kvalitetu** rekonstrukcije
- Trebaš da **razrešiš bliske objekte** (gravitational lensing, binary stars, itd.)

### ❌ NE KORISTI fiDrizzle-MU kada:

- Imaš samo **1-3 slike** (nedovoljno informacije)
- Slike **nisu dithered** (nema sub-pixel shifts)
- Trebaš **brz rezultat** (standardni drizzle je brži)
- Slike su **već Nyquist-sampled** (nema potrebe za super-resolution)

---

## Poređenje sa drugim metodama

| Metoda | Brzina | Kvalitet | Noise | Ringing | Upotreba |
|--------|--------|----------|-------|---------|----------|
| **Standardni stack** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ✓ Ne | Brz preview |
| **Drizzle** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐ Malo | HST pipeline |
| **iDrizzle** | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ Nešto | Retko |
| **fiDrizzle-DC** | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ Dosta | Istraživanje |
| **fiDrizzle-MU** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✓ Ne | **NAJBOLJE!** |

### Vreme procesiranja (iz rada, za PSNR=20):

- **Drizzle**: 1.2s (referenca)
- **iDrizzle**: 2407s (~40 minuta) - 164 iteracije
- **fiDrizzle-DC**: 268s (~4.5 minuta) - 123 iteracije
- **fiDrizzle-MU**: **67s (~1 minut)** - samo 27 iteracija! ⚡

---

## Troubleshooting

### Problem: "No convergence after max iterations"

**Rešenje**:
- Povećaj `--iterations` (npr. na 200)
- Proveri da li su slike pravilno registrovane
- Smanji `--psr` (npr. 0.7 umesto 0.5)

### Problem: "Out of memory"

**Rešenje**:
- PSR je previsok (prevelika output slika)
- Smanji rezoluciju input slika pre procesiranja
- Koristi `--psr 0.5` ili veći

### Problem: "Ringing artifacts around bright stars"

**Rešenje**:
- Proveri da li je `--no-positivity` slučajno specificiran
- Ukloni `--no-positivity` flag
- Smanji broj iteracija

### Problem: "Rezultat je sličan običnom drizzle-u"

**Rešenje**:
- Broj iteracija je premali - povećaj na 50-100
- Slike možda nemaju dovoljno dithering shifts
- Proveri shift file

---

## Reference i dodatni resursi

### Naučni rad:
- **arXiv**: https://arxiv.org/abs/2511.09881
- **Naslov**: "fiDrizzle-MU: A Fast Iterative Drizzle with Multiplicative Updates"
- **Autori**: Shen Zhang, Lei Wang, Huanyuan Shan, et al.

### Povezane metode:
- Original Drizzle: Fruchter & Hook (2002)
- iDrizzle: Fruchter (2011)
- fiDrizzle-DC: Wang & Li (2017)

### Siril dokumentacija:
- Siril registration: https://siril.org/
- Drizzle integration: https://siril.org/tutorials/

---

## Napredne opcije

### Python API upotreba:

Možeš koristiti kao Python modul:

```python
from siril_fidrizzle_mu import FiDrizzleMU

# Kreiraj processor
processor = FiDrizzleMU(
    psr=0.5,
    gamma=1.0,
    max_iterations=100,
    positivity_constraint=True,
    verbose=True
)

# Učitaj slike
processor.load_images(['image1.fit', 'image2.fit', ...])

# Procesiranje
result = processor.process()

# Sačuvaj
processor.save_result(result, 'output.fits')
```

### Prilagođavanje algoritma:

Možeš modifikovati parametre u kodu:
- `upsampling()` metoda - promeni interpolaciju
- `downsampling()` metoda - promeni averaging scheme
- `iterate()` metoda - dodaj custom regularizaciju

---

## Zaključak

**fiDrizzle-MU** je trenutno **najnapredniji algoritam** za stackiranje dithered slika koji je javno dostupan. Koristi ga kada želiš **maksimalnu kvalitet** i rezoluciju iz svojih podataka!

Za pitanja i probleme, pogledaj:
- GitHub Issues: [siril-drizzle-scripts repository]
- Siril Forum: https://siril.org/forum/
- Original rad: arXiv:2511.09881

---

**Srećno stackiranje! 🔭✨**
