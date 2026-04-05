# Shell completion

Nástroj podporuje tab-completion pro bash a zsh prostřednictvím knihovny `argcomplete`.

## Instalace

```bash
pip install argcomplete
```

## Aktivace (bash)

Pro aktuální session:
```bash
eval "$(register-python-argcomplete main.py)"
```

Pro trvalé povolení přidáme do `~/.bashrc`:
```bash
echo 'eval "$(register-python-argcomplete ~/cesta/k/ZM2_Mereni/main.py)"' >> ~/.bashrc
```

## Aktivace (zsh)

```bash
autoload -U bashcompinit && bashcompinit
eval "$(register-python-argcomplete main.py)"
```

## Použití

```bash
$ python3 main.py arit<TAB>
# → python3 main.py aritmeticky_prumer

$ python3 main.py aritmeticky_prumer --<TAB>
# → --input  --latextable  --typ-b  --outliers  --caption  ...
```
