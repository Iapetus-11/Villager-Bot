# **Villager Bot**
[![CodeFactor](https://www.codefactor.io/repository/github/iapetus-11/villager-bot/badge)](https://www.codefactor.io/repository/github/iapetus-11/villager-bot)
[![Bot Status](https://top.gg/api/widget/status/639498607632056321.svg?noavatar=true)](https://top.gg/bot/639498607632056321)
[![Server Count](https://top.gg/api/widget/servers/639498607632056321.svg?noavatar=true)](https://top.gg/bot/639498607632056321)
[![Support Server](https://img.shields.io/discord/641117791272960031?color=0FAE6E&label=discord%20server)](https://discord.gg/39DwwUV)
[![CI](https://github.com/Iapetus-11/Villager-Bot/actions/workflows/ci.yml/badge.svg)](https://github.com/Iapetus-11/Villager-Bot/actions/workflows/ci.yml)

## Notable Features
* Ability to generate Minecraft pixel art from images sent in the chat
* Ability to ping / check the status of any Minecraft server
* Expansive economy system (based upon emeralds obviously!)
* Multi-language support! (English, Español, Français, Português)
* Tons of customization and configuration options

## Support / Contact Information
* [Discord Support Server](https://discord.gg/39DwwUV)
* Discord Username: `Iapetus11#6821`

## Privacy Policy
- [Click Here](https://github.com/Iapetus-11/Villager-Bot/blob/main/PRIVACY-POLICY.md)

## Technologies
- [discord.py](https://github.com/Rapptz/discord.py)
- [Cython](https://cython.org/)
- [OpenCV](https://opencv.org/) + [Numpy](https://numpy.org/)
- websockets


## Contributing
### Issues / Bugs
If a bug or unintended behavior is discovered, please report it by creating an issue [here](https://github.com/Iapetus-11/Villager-Bot/issues) or by reporting it in the **#bug-smasher** channel on the [support server](https://discord.gg/39DwwUV).

### Development
If you'd like to contribute code to Villager Bot, then please fork the repository and make any necessary changes there. Then, [make a pull request](https://github.com/Iapetus-11/Villager-Bot/pulls) and it will be reviewed. Please read the [contribution guidelines](https://github.com/Iapetus-11/Villager-Bot/blob/master/CONTRIBUTING.md) before making changes.

### Setting up Villager Bot
1. `git clone` Villager Bot, and `cd` into the `Villager-Bot` directory.
2. create a [PostgreSQL](https://www.postgresql.org/) database, and execute the contents of `setup.sql` to create the necessary tables.
3. make a new file called `secrets.json` and fill in the fields based off the `secrets.example.json` file for both `bot/` and `karen/`
4. use [poetry](https://python-poetry.org) to install the required dependencies with `poetry install`.

### Running Villager Bot
1. Make sure the specified cluster count in `karen/secrets.json` is `1`
2. Run Karen with `poetry run py -m karen` (or `poetry run python3 ...` if not on windows)
3. Run a bot cluster with `poetry run py -m bot` (or `poetry run python3 ...` if not on windows)

- Running with Docker is also possible, but requires a .env file based off the .env.example to be created. Then to build run `docker compose build` and to run `docker compose up`
