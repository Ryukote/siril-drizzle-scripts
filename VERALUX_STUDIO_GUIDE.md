# VeraLux Drizzle Studio - Priručnik

## Pregled

VeraLux Drizzle Studio je moderna, profesionalna GUI aplikacija za drizzle stackiranje slika u Sirilu. Omogućava kompletni workflow od kalibracije do finalnog stackiranja u intuitivnom sučelju.

## Pokretanje

```bash
# Jednostavno pokretanje
python veralux_drizzle_studio.py

# Ili pomoću launcher skripte (provjerava dependencies)
python run_veralux_studio.py
```

## Workflow - Korak po Korak

### 1. Input Files (Ulazne Datoteke)

**Light Frames:**
- Kliknite "Browse..." pored "Light Frames"
- Odaberite direktorij sa vašim light frame-ovima (FITS, RAW, itd.)
- Siril će automatski konvertirati i učitati sve kompatibilne datoteke

**Output Directory:**
- Odaberite gdje želite spremiti rezultat
- Default: `../drizzled`

### 2. Calibration (Kalibracija)

**Dva moda:**

**Uncalibrated** (Default):
- Procesira slike bez kalibracije
- Brzo, ali ne daje najbolje rezultate
- Dobro za testiranje

**Calibrated** (Preporučeno):
- Omogućava odabir master kalibracionih datoteka:
  - **Bias Frames**: Offset frames za oduzimanje read noise-a
  - **Dark Frames**: Dark current za oduzimanje termalnog šuma
  - **Flat Frames**: Flat field za korekciju vignettinga i prašine
- Rezultira u značajno boljoj kvaliteti slike

**Debayer:**
- Označite ako koristite OSC/color kameru (Bayer pattern)
- Odznačite za mono kamere

### 3. Drizzle Method (Metoda)

Odaberite između 4 napredne metode:

#### Standard Drizzle ⭐
- Klasična metoda (Fruchter & Hook 2002)
- Brza i pouzdana
- Najbolja za opću upotrebu

#### fiDrizzle-MU (★ PREPORUČENO za točkaste izvore)
- Najnovija metoda sa multiplikativnim updates
- 5-7x brža konvergencija od drugih iterativnih metoda
- Izvrsna za zvijezde, kvazare, gravitacijske leće
- Pozitivnost constrainta smanjuje ringing artefakte

#### fiDrizzle-DC
- Brza iterativna metoda sa difference correction
- Dobra ravnoteža brzine i kvalitete
- Reducira noise korelaciju

#### iDrizzle
- Originalna iterativna metoda
- Sporija ali vrlo precizna
- Za maksimalnu kvalitetu rekonstrukcije

**Iteracije:**
- Povećajte za bolju kvalitetu (ali sporije)
- Preporučeno: 65 za point sources, 100 za generalno

**Gamma:**
- Step size za fiDrizzle-MU
- Default: 1.0
- Manji = stabilnije, veći = brže

**Positivity Constraint:**
- Forsira nenegativne flux vrijednosti
- Smanjuje ringing artefakte
- **Preporučeno: Uključeno**

### 4. Drizzle Parameters (Parametri)

#### Pixfrac (Drop Size) 🔧
Kontrolira "skupljanje" input piksela prije drizzlinga:

- **0.0** = Interlacing (oštro, ali praznine)
- **0.5** = Dobro za točkaste izvore (zvijezde)
- **0.7** = ⭐ **PREPORUČENO** za generalnu upotrebu
- **0.8** = Extended sources (galaksije, maglice)
- **1.0** = Shift-and-add (glatko, više korelacije)

**Pravilo:**
- Manje pixfrac = oštrije, ali više artefakata
- Veće pixfrac = glađe, ali više blur-a

#### Output Scale (PSR) 📐
Output pixel scale ratio - rezolucija izlazne slike:

- **1.0** = Ista rezolucija kao input
- **0.5** = ⭐ **PREPORUČENO** - 2x finiji sampling
- **0.25** = 4x finiji sampling (za ekstremnu rezoluciju)

**Napomena:** Manji scale = veća izlazna slika!

### 5. Quick Presets (Brzi Preset-i)

Kliknite na preset za optimalne postavke:

- **High Resolution**: Optimizirano za maksimalnu rezoluciju
- **Fast Iterative**: Brza iterativna metoda, opća upotreba
- **Point Sources**: ⭐ Savršeno za zvijezde i točkaste objekte
- **Extended Sources**: Za galaksije, maglice, planetarne maglice

### 6. Processing (Proces)

1. Kliknite **"⚡ STACK IMAGES"**
2. Potvrdite postavke u dijalogu
3. Pratite napredak u **Processing Log** panelu
4. Progress bar pokazuje trenutni status
5. Po završetku, rezultat se sprema u output direktorij

## Processing Log

Real-time log pokazuje:
- Konfiguraciju postavki
- Trenutni korak u procesu
- Siril komande koje se izvršavaju
- Greške ili upozorenja
- Završnu poruku

## Tipične Greške i Rješenja

### "Input directory not found"
- Provjerite da li je putanja do light frames pravilna
- Provjerite ima li direktorij validnih FITS/RAW datoteka

### "Calibration files required"
- Ako ste odabrali "Calibrated" mod, morate navesti bias, dark i flat
- Ili prebacite na "Uncalibrated" mod

### "Siril command failed"
- Provjerite je li Siril instaliran i dostupan
- Provjerite jesu li datoteke validne
- Pogledajte log za detaljnije informacije

### "Processing is slow"
- Iterativne metode (iDrizzle, fiDrizzle) su sporije
- Smanjite broj iteracija
- Koristite Standard drizzle za brže rezultate
- fiDrizzle-MU je najbržija iterativna metoda

## Tips & Tricks

### Najbolje Postavke za Različite Ciljeve

**Deep Sky Objects (DSO):**
```
Method: fiDrizzle-MU
Pixfrac: 0.7
Scale: 0.5
Iterations: 100
Positivity: ✓
```

**Planetary:**
```
Method: Standard
Pixfrac: 0.8
Scale: 0.5
Positivity: ✗
```

**Variable Stars / Photometry:**
```
Method: fiDrizzle-MU
Pixfrac: 0.5
Scale: 0.5
Iterations: 65
Positivity: ✓
```

**Quick Preview:**
```
Method: Standard
Pixfrac: 0.7
Scale: 1.0
```

### Calibration Best Practices

1. **Snimite dovoljno calibration frames:**
   - Bias: 20-30 frames
   - Dark: 10-20 frames (iste exposure time kao lights)
   - Flat: 10-20 frames

2. **Master frames:**
   - Siril će automatski napraviti master frames stackiranjem
   - Rezultat je bolja S/N ratio

3. **Temperatura:**
   - Dark frames trebaju biti snimljeni na istoj temperaturi kao lights
   - Ako imate hlađenu kameru, koristite istu temperaturu

## Keyboard Shortcuts

- **Double-click na slider** = Reset na default vrijednost
- **?** = Prikaži help dialog

## Persistence (Spremanje Postavki)

Aplikacija automatski sprema:
- Output directory
- Pixfrac i Scale vrijednosti
- Debayer postavku

Pri sljedećem pokretanju, postavke će biti učitane.

## Tehnička Dokumentacija

Za detaljnije informacije o drizzle metodama, pogledajte:
- `documentation/Drizzle.pdf` - Standard Drizzle
- `documentation/fiDrizzle-MU.pdf` - Fast Iterative MU method
- `README.md` - Opće informacije

## Kontakt i Podrška

Za pitanja ili probleme:
- Otvorite issue na GitHub-u
- Pogledajte dokumentaciju u `documentation/` direktoriju
- Provjerite Siril forum: https://free-astro.org/

---

**Sretan Drizzling! 🌟**

*Based on VeraLux Design System*
