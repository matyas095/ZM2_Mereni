import pandas as pd;
import io;
import re;
from pathlib import Path;
import numpy as np;
from utils import color_print;

def run(args, returnFile = False):
    dir_name = "outputs";

    folder_path = Path(dir_name).resolve();
    folder_path.mkdir(parents=True, exist_ok=True);

    outputs = np.array([]);

    with open(args.input) as f:
        f = io.StringIO(f.read());

        header_labels = re.split(r'\s{2,}', f.readline().strip());
        header_units = re.split(r'\s{2,}', f.readline().strip());
        labels = header_labels[0].strip().split('\t');
        units = header_units[0].strip().split('\t');

        combined_headers = [f"{label} ({unit})" for label, unit in zip(labels, units)];

        df = pd.read_csv(f, sep='\t', decimal=',', skiprows=2, names=combined_headers);
        toProcess = [];
        for _, row in df.iterrows():
            toProcess.append( { key: row[key] for key in combined_headers } );
        
        toWrite = {};
        for row in toProcess:
            for key in row:
                if key not in toWrite: toWrite[key] = [];
                toWrite[key].append(row[key]);
        
        all_lines = [];
        for rowKey in toWrite:
            str_list = [str(val) for val in toWrite[rowKey]];
            match = re.search(r'\(([^\)]+)\)', rowKey);
            if match: key = match.group(1) ;
            else: raise Exception("Chyba v klici");
        
            line = f'{key}={",".join(str_list)}';
            all_lines.append(line);
        
        np.append(outputs, all_lines);
        if(not returnFile):
            with open(folder_path / (getattr(args, "output", "ERRORER.txt") +  ".txt"), 'w', encoding='utf-8') as f:
                f.write("\n".join(all_lines));
    
    if(returnFile): return outputs;
    
    print(
        f"Soubor {color_print.GREEN}uložen{color_print.END} pod názvem "
        f"{color_print.BOLD}{getattr(args, "output", "ERRORER.txt") +  ".txt"}{color_print.END} cesta:\n"
        f"└──{folder_path / (getattr(args, "output", "ERRORER.txt") +  ".txt")}"
    );