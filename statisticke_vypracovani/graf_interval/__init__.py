from .logic import run;

def get_args_info():
    """Returns a list of dictionaries defining the arguments for this module.""";
    return [
        {
            "flags": ["-n", "--name"],
            "help": "Název grafu",
            "required": True,
            "type": str
        },
        {
            "flags": ["-r", "--rovnice"],
            "help": "Funkční závislost formát 'VELIČINA=VZTAH'\nNutná aby byla jedno proměnná.",
            "required": True,
            "type": str
        },
        {
            "flags": ["-i", "--interval"],
            "help": "Interval na kterým je vztah. Formát -i 10 100; Interval <10, 100>",
            "required": True,
            "nargs": 2,        # Očekává 2 hodnoty
            "type": float
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