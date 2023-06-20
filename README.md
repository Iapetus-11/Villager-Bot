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

## Technologies
- [discord.py](https://github.com/Rapptz/discord.py)
- [Cython](https://cython.org/)
- [OpenCV](https://opencv.org/) + [Numpy](https://numpy.org/)
- websockets
### Architecture
Villager Bot is separated into two components; Karen and the clusters. A "cluster" is a group of shards (websockets connected to Discord in this case).
Due to the nature of Villager Bot, these clusters need to share state and communicate, which is what Karen facilitates via the use of websockets.
Villager Bot is dockerized and this architecture allows scaling while maintaining functionality and easy development.

## [Privacy Policy](PRIVACY-POLICY.md)

## [Contributing](CONTRIBUTING.md)
