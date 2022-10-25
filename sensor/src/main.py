from src import interfaces

def run():
    """
    entry point of the mainloop running continuously
    on the sensor node
    """
    config = interfaces.ConfigInterface.read()
    print(f"Hello! config = {config}")
