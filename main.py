from configLoader import Config
from app import App


def main():
    config = Config()
    app = App(config)

    app.run()
    #app.test()
if __name__ == "__main__":
    main()



