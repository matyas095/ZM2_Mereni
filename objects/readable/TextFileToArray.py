import numpy as np;
from ..elements import Element, List;

class TextFileToArray:
    def __init__(self, filePath) -> None:
        self.filePath = filePath;
    
    def try_convert(self, s):
        """
        Tries to convert a string to int, then float, then returns as-is.
        """
        if not isinstance(s, str): return s;
        try:
            return int(s);
        except ValueError:
            try:
                return float(s);
            except ValueError:
                return s;
    
    def openFile(self):
        return open(self.filePath, "r");
    
    def save(self):
        self.file.close();
    
    def mean(self, i = None):
        if(i): np.sum(self.array[i, 1]);
        else: return np.array([
                np.array([
                    group,
                    np.sum(val) * 1 / len(val)
                ])
                for group, val in zip(self.array[:, 0], self.array[:, 1])
            ], dtype=object);
    

    def build(self):
        self.file = self.openFile();

        result = [
            [
                np.array([self.try_convert(i) for i in sub][0]) if len(sub) == 1 
                else np.array([self.try_convert(i) for i in sub])
                for sub in group
            ]
            for group in [[m.split(",") for m in x.split("=")] for x in self.file.read().split("\n") if x]
        ];
    
        self.array = np.array(result, dtype=object);
    
        return List(self.array);

        
    def __str__(self) -> str:
        return str(self.array);

    def __iter__(self):
        return self.array;
