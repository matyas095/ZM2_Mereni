import numpy as np;
import math;
from pathlib import Path;
from itertools import zip_longest;
from .Element import Element;
from utils import color_print;
import os;

class List:
    def __init__(self, list) -> None:
        self.array = np.array(list, dtype=object);
    
        TEMP = [];
        for i in range(len(list)):
            precision = self.get_Precision(i);
            name = list[i, 0];
            arguments = [name, [Element(name, val, precision) for val in list[i, 1]]];
            TEMP.append(arguments);
                # rounded_arr = np.round(val, decimals=precision);
        self.container = np.array(TEMP, dtype=object);

    def get_Precision(self, i):
        chyba = self.chyba(i)[1];
        if(not isinstance(chyba, (float, int))): raise ValueError("Chyba ve floatu pro hodnotu: " +  i);
        return -int(math.floor(math.log10(chyba)));

    def toArray(self):
        vals = [
            [
                group,
                [str(el) for el in sublist]
            ] 
            for group, sublist in zip(self.container[:, 0], self.container[:, 1])
        ];
        print(vals);
        return self.container;

    def append(self, value, i):
        return np.append(self.array[i, 1], value);

    def aritmetric_mean(self, i = None):
        """
        Vrátí chybu aritmetický průměr `self.array`.

        Parametry
        ---------
        i `int` (optional) - Pozice hodnoty k výpočtu aritmetického průměru
        
        Returns
        -------
        Vrátí `list | array` ve formátu [ ..[NÁZEV, ARITMETR_HODNOTA].. ].

        Example
        -------
        >>> List.aritmetric_mean(2);
            >>> ["Bengr", 234.23];
        """
        if(i): return np.sum(self.array[i, 1]);
        else: return np.array([
                [
                    group,
                    np.sum(val) * 1 / len(val)
                ]
                for group, val in zip(self.array[:, 0], self.array[:, 1])
            ], dtype=object);

    def chyba(self, i = None):
        """
        Vrátí chybu aritmetického průměru `self.array`.

        Parametry
        ---------
        i `int` (optional) - Pozice hodnoty k výpočtu chyby
        
        Returns
        -------
        Vrátí `tuple` ve formátu ( ..(NÁZEV, CHYBA).. ).

        Example
        -------
        >>> List.chyba(2)
            >>> ( ("Kárl", 2.32) )
        """
        if(i is not None): return [self.array[i, 0], np.std(self.array[i, 1]) * 1 / np.sqrt(len(self.array[i, 1]))];
        else: 
            return tuple(
                (
                    group,
                    np.std(val) * 1 / np.sqrt(len(val))
                )
                for group, val in zip(self.array[:, 0], self.array[:, 1])
            );

    def createLaTeXTable(self, i = None):
        dir_name = "latex_output";

        folder_path = Path(dir_name).resolve();
        folder_path.mkdir(parents=True, exist_ok=True);
        if(i is not None):
            header = self.array[i, 0].item();
            body = self.array[i, 1];

            thingy = [f"\t\t{str(x)}" for x in body];

            len_header = 1;

            latex_table_HEAD = (
                "\\begin{table}[H]\n"
                "\t\\centering\n"
                "\t\\small\n"
                "\t\\begin{tabular}{@{}" + "c" * len_header + "@{}}\n"
                "\t\t\\toprule\n"
            );
            latex_table_END = (
                "\n\t\\end{tabular}\n"
                "\t\\caption{" + input("Jakej caption (text) chceš míti: ") + "}\n"
                "\t\\label{tab:" + input("Jakej label chceš míti: ") + "}\n"
                "\\end{table}"
            );

            tex_File_Name = f"table_{str(header).split(" ")[0]}.tex";
            tex_File_Path = folder_path / tex_File_Name;

            with open(tex_File_Path, "w", encoding="utf-8") as f:
                f.write(latex_table_HEAD);
                f.write(f"\t\t{header} \\\\ \\midrule\n");
                result_str = " \\\\ \n".join(thingy) + r" \\ \bottomrule";
                f.write(result_str);
                f.write(latex_table_END);
                print(color_print.GREEN + f"Soubor {tex_File_Name} uložen na adrese{color_print.END}");
                print("└──" + str(tex_File_Path));
        else:
            headers = [f"${x}$" for x in self.container[:, 0]];
            body = self.container[:, 1];
            rows_list = list(zip_longest(*body, fillvalue="-"));

            pairs = ["\t\t" + " & ".join(str(el) for el in pair) + " \\\\" for pair in rows_list]

            tex_File_Name = f"table_{"_".join([x.split(" ")[0].replace("$", "") for x in headers])}.tex";
            tex_File_Path = folder_path / tex_File_Name;

            col_widths = []
            for i in range(len(headers)):
                column_cells = [str(r[i]) for r in rows_list];
                max_w = max(len(headers[i]), max([len(c) for c in column_cells] or [0]));
                col_widths.append(max_w);
            

            formatted_headers = [headers[i].ljust(col_widths[i]) for i in range(len(headers))];
            header_line = "\t\t" + " & ".join(formatted_headers) + " \\\\ \\midrule";

            pairs = [];
            for row in rows_list:
                formatted_cells = [str(row[i]).ljust(col_widths[i]) for i in range(len(row))];
                pairs.append("\t\t" + " & ".join(formatted_cells) + " \\\\");

            latex_table_HEAD = (
                "\\begin{table}[H]\n"
                "\t\\centering\n"
                "\t\\small\n"
                "\t\\begin{tabular}{@{}" + "c" * len(headers) + "@{}}\n"
                "\t\t\\toprule\n"
            );
            latex_table_END = (
                "\n\t\\end{tabular}\n"
                "\t\\caption{" + input("Jakej caption (text) chceš míti: ") + "}\n"
                "\t\\label{tab:" + input("Jakej label chceš míti: ") + "}\n"
                "\\end{table}"
            );
            size = os.get_terminal_size()
            print("-" * size.columns)


            with open(tex_File_Path, "w", encoding="utf-8") as f:
                f.write(latex_table_HEAD);
                f.write(header_line);
                
                result_str = "\n" + "\n".join(pairs) + "\n\t\t\\bottomrule";
                f.write(result_str);
                
                f.write(latex_table_END);
                
                print(color_print.GREEN + f"Soubor {tex_File_Name} uložen na adrese{color_print.END}");
                print("└──" + str(tex_File_Path));



