from src import main
import dotenv
from os.path import join, dirname, abspath

# .env file is helpful on development machines
dotenv.load_dotenv(join(dirname(abspath(__file__)), "config", ".env"))

if __name__ == "__main__":
    main.run()
