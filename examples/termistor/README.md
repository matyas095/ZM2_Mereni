# Příklad: Závislost odporu termistoru na teplotě

## Úloha

Měříme závislost odporu termistoru na teplotě v rozsahu 20–60 °C. Z naměřených dat extrapolujeme hodnotu odporu při 0 °C a počítáme konstanty B a R∞ ze vztahu:

```
R(T) = R∞ · exp(B/T)
```

## Vstupní data

Data ve složce `data/` jsou CASSY export obsahující:
- `t [s]` — čas měření
- `T [K]` — teplota termistoru
- `URT [V]` — napětí na termistoru
- `URN [V]` — napětí na kalibračním rezistoru

## Workflow

Viz `commands.sh` pro kompletní zpracování.

1. Načtení dat z CASSY exportu a výpočet statistik
2. Export do LaTeX tabulky pro protokol (s auto-statistikami v captionu)
3. Lineární fit pro extrapolaci k 0 °C
4. Výpočet R_0 z konstant B a R∞
