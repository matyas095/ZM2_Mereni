from .logic import run;

def get_args_info():
    """Returns a list of dictionaries defining the arguments for this module.""";
    return [
        {
            "flags": ["-i", "--input"],
            "help": "Cesta k vstupnímu souboru s daty",
            "required": True,
            "is_file": True
        },
        {
            "flags": ["-n", "--name"],
            "help": "Název grafu",
            "required": True,
            "type": str
        },
        {
            "flags": ["-r", "--rovnice"],
            "help": "Závislost prvních linky dat do druhé",
            "required": False,
            "type": str
        },
        {
            "flags": ["-p", "--parametr"],
            "help": "Vypočítá data jako 2D graf dle parametru f(x), funguje jenom s -r [--rovnice]",
            "type": str
        }
    ];

"""
{
    "flags": ["-t", "--threshold"],
    "help": "Práh pro filtraci dat (výchozí: 0.5)",
    "default": 0.5,
    "type": float
},
{
    "flags": ["--verbose"],
    "help": "Vypisovat podrobnosti",
    "action": "store_true"
},
{
    "flags": ["-2d", "--2-dimenze"],
    "help": "Zg",
    "dest": "Zd",
    "action": "store_true"
}
"""