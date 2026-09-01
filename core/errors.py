from discord import app_commands
from discord.ext import commands
from core.logger import logger


def setup_error_handler(bot: commands.Bot):
    @bot.tree.error
    async def on_app_command_error(
        interaction, error: app_commands.AppCommandError
    ):
        logger.error(f"App command error: {error}")

        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"Este comando está en cooldown. Intentá de nuevo en {error.retry_after:.1f} segundos.",
                ephemeral=True,
            )
        elif isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "No tenés permisos para usar este comando.", ephemeral=True
            )
        elif isinstance(error, app_commands.CheckFailure):
            await interaction.response.send_message(
                "No cumplís con los requisitos para usar este comando.", ephemeral=True
            )
        else:
            if interaction.response.is_done():
                await interaction.followup.send(
                    "Hubo un error al ejecutar el comando. Por favor intentá de nuevo.",
                    ephemeral=True,
                )
            else:
                await interaction.response.send_message(
                    "Hubo un error al ejecutar el comando. Por favor intentá de nuevo.",
                    ephemeral=True,
                )
