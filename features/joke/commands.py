from discord import app_commands, Interaction
from discord.ext import commands
from features.joke.service import JokeService


class JokeCog(commands.Cog):
    def __init__(self, bot: commands.Bot, joke_service: JokeService):
        self.bot = bot
        self.joke_service = joke_service

    @app_commands.command(name="chiste", description="La IA hace un chiste con la palabra que le des")
    @app_commands.describe(palabra="Palabra que el chiste debe incluir")
    async def chiste(self, interaction: Interaction, palabra: str):
        await interaction.response.defer()
        chiste = await self.joke_service.generar_chiste(palabra)
        await interaction.followup.send(chiste)


async def setup(bot: commands.Bot):
    joke_service = JokeService(bot.ai_service)
    await bot.add_cog(JokeCog(bot, joke_service))
