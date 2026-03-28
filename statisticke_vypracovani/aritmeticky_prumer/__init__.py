from .logic import run;

def get_args_info():
    """Returns a list of dictionaries defining the arguments for this module.""";
    return [
        {
            "flags": ["-i", "--input"],
            "help": "Cesta k vstupnímu souboru s daty",
            "required": True,
            "is_file": True
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
}
"""