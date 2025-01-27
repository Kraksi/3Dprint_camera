from observer.observer import Observer

class ConsoleNotifier(Observer):
    def update(self, message: str):
        print(f"ConsoleNotifier: {message}")
