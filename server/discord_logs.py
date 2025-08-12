import logging
import requests

DISCORD_WEBHOOK = "https://discordapp.com/api/webhooks/1401133863463555153/rkwIKwIeCPlSV8yPHpYE4oYLzPZt1SLekm75SNFomoCTvcqK5ZWwxgDe6pMGrpk_dGKY123" 

class DiscordHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        try:
            requests.post(DISCORD_WEBHOOK, json={"content": f"```{log_entry}```"})
        except Exception as e:
            print(f"Failed to send log: {e}", flush=True)


def get_logger(name="app"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    discord_handler = DiscordHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    discord_handler.setFormatter(formatter)
    logger.addHandler(discord_handler)
    return logger

