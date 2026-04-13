from main import CLIApp, check_for_updates;

if __name__ == "__main__":
    check_for_updates();
    app = CLIApp(only={"aritmeticky_prumer", "neprima_chyba", "convert_soubor", "vazeny_prumer", "join_tables", "derivace", "format_table", "extract_table", "regrese"});
    app.run();
