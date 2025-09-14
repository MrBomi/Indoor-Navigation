from configLoader import Config
from core.app import App


def main():
    config = Config()
    app = App(config)

    app.createFloor()
if __name__ == "__main__":
    main()



