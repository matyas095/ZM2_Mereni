from main import CLIApp, check_for_updates;

if __name__ == "__main__":
    check_for_updates();
    app = CLIApp(only={"graf", "graf_interval", "histogram"});
    app.run();
