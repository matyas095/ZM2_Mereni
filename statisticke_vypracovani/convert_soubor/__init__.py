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
            "flags": ["-o", "--output"],
            "help": "Název výstupu (BEZ PŘÍPONY)",
            "required": False,
            "default": "output_convertor",
            "type": str
        },
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