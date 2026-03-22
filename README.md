# Základy měření 2

Zde se budou ukládat všechna zpracování dat v Pythonu a dále (pokud bude eh). Repozitář je rozdělen do složek dle úloh měření, dole je rozpis co a jak proč kde.

## Statistické zpracování dat
Následující seznam má následující strukturu
- **název metody** - Napis
    - Popis
    - Vstup
        - ...
    - Výstup
        - ...

Lze spustit automatické výpočty jako:
- **aritmeticky_prumer** - Aritmetický průměr + Střední kvadratická chyba aritmetického průměru
    - Výpočet aritmetického průměru spolu se střední kvadratickou chybou
    - Vstup
        - `soubor [txt, -, ...] {r}`
            - *soubor* obsahuje veličiny a hodnoty ke zpracování metodou, jeho struktura je následující: `VELIČINA=DATA` s tím, že pro každou novou veličinu zadáme do nového řádku, příklad níže, nebo [zde](statisticke_vypracovani/aritmeticky_prumer/input/input_aritm_prumer) 
                - U_0=2343,234,23423\
                  I_0=323,234928,1243
    - Výstup `print ->`
        - VELIČINA\
        ├──Aritmetický průměr = ČÍSLO\
        └──Chyba aritmetického průměru = ČÍSLO

### Vyvolávání metod
Pro vyvolání metody použije hlavní funkci **main.py**, která tyto metody modulárně vyvolává. A to ve formátu nejčastěji (zatím rozhodně):
```
python3 main.py -m METODA [-i CESTA_K_SOUBORU]
```

Pro každou metodu volíme jeho název pro argument `METODA`, tedy první argument v listu, tedy to co je tučně vyznačené, např.: chci aritmetický průměr tak název metody je aritmeticky_prumer.

Následně je nutné se zaměřit na vstup, vstupy jsou obecně zadaný a to ve formátu  `OBJEKT [TYP_OBJEKTU] {rwx}`, kde
- `OBJEKT` je vstupní objekt, soubor, ...
- `[TYP OBJEKTU]` jakej typ je objektu (clueless) např.: .txt, ...
- `{rwx}` jsou oprávnění `r` - read (čtení), `w` - write (zápis), `x` - execute (provést), pokud `{rwx}` chybí, tak oprávnění nejsou žádáná

pro každý vstup platí i určitá struktura, která je popsána pod `OBJEKT`

> [!IMPORTANT]
> Každej vstupní soubor MUSÍ splňovat podmínky vstupu jako vyznačený v listu výše.

Pro výpis všech metod lze využít příkazu:
```
python3 main.py -h
```

#### Příklad
```
python3 main.py -m aritmeticky_prumer -i input/KARL.txt
```



## Rozpis měření
- [Měření 7.](#měření-7---ohmův-zákon) - 12.3.25
- [Měření 8.](#měření-8---velké-odpory-wheastonův-můstek-obilíkámen-můstek) - 19.3.25

## Zápis měření

### Měření 7 - Ohmův zákon
- Zapsány tabulky měření\
Všechny výpočty dělány ručně (kalkulátor incident)

### Měření 8 - Velké odpory, Wheastonův můstek (Obilíkámen můstek)
- 