# **Villager Bot**
[![CodeFactor](https://www.codefactor.io/repository/github/iapetus-11/villager-bot/badge)](https://www.codefactor.io/repository/github/iapetus-11/villager-bot)
[![Views](https://api.ghprofile.me/view?username=villager-dev.villager-bot&color=0FAE6E&label=views&style=flat)](https://github.com/Iapetus-11/Villager-Bot)
[![Bot Status](https://top.gg/api/widget/status/639498607632056321.svg?noavatar=true)](https://top.gg/bot/639498607632056321)
[![Server Count](https://top.gg/api/widget/servers/639498607632056321.svg?noavatar=true)](https://top.gg/bot/639498607632056321)
[![Support Server](https://img.shields.io/discord/641117791272960031?color=0FAE6E&label=discord%20server)](https://discord.gg/39DwwUV)

## Notable Features
* Ability to generate Minecraft pixel art from images sent in the chat
* Ability to ping / check the status of any Minecraft server
* Expansive economy system (based upon emeralds obviously!)
* Multi-language support! (English, Español, Français, Português)
* Tons of customization and configuration options
* Made by Iapetus11, so it must be good right?!

## Support / Contact Information
* [Discord Support Server](https://discord.gg/39DwwUV)
* Discord Username: `Iapetus11#6821`

## Privacy Policy
- [Click Here](https://github.com/Iapetus-11/Villager-Bot/blob/main/PRIVACY-POLICY.md)

## Contributing
### Issues / Bugs
If a bug or unintended behavior is discovered, please report it by creating an issue [here](https://github.com/Iapetus-11/Villager-Bot/issues) or by reporting it in the **#bug-smasher** channel on the [support server](https://discord.gg/39DwwUV).

### Development
If you'd like to contribute code to Villager Bot, then please fork the repository and make any necessary changes there. Then, [make a pull request](https://github.com/Iapetus-11/Villager-Bot/pulls) and it will be reviewed. Please read the [contribution guidelines](https://github.com/Iapetus-11/Villager-Bot/blob/master/CONTRIBUTING.md) before making changes.

### Setting up Villager Bot
1. `git clone` Villager Bot, and `cd` into the `Villager-Bot` directory.
2. create a [PostgreSQL](https://www.postgresql.org/) database, and use the execute the contents of `setup.sql` to create the necessary tables.
3. make a new file called `secrets.json` and fill in the fields based off the `secrets.example.json` file.
4. use [poetry](https://python-poetry.org) to install the required dependencies with `poetry install`.
5. run the bot with either `villager-bot.bat` or `villager-bot.sh`.
