class Element:
    def __init__(self, name, value, precision) -> None:
        self.name = name;
        self.value = value;
        self.precision = precision;
    
    def round(self):
        return round(self.value, self.precision);

    def __str__(self):
        return f"{self.round()}";