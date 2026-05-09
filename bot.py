"""Paperclip Telegram Bot — entry point."""

import logging
import sys

from telegram.ext import Application

import config
from handlers import register_handlers
from middleware.errors import error_handler
from metrics_server import start_metrics_server
from paperclip_client import get_client

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def _setup_logging() -> None:
    """Configure logging based on LOG_FORMAT config."""
    level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)

    if config.LOG_FORMAT == "json":
        try:
            from pythonjsonlogger.json import JsonFormatter

            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(
                JsonFormatter(
                    fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
                    rename_fields={"asctime": "timestamp", "levelname": "level"},
                )
            )
            logging.root.handlers.clear()
            logging.root.addHandler(handler)
            logging.root.setLevel(level)
        except ImportError:
            logging.basicConfig(
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                level=level,
            )
            logging.getLogger(__name__).warning(
                "python-json-logger not installed — falling back to text logging"
            )
    else:
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=level,
        )


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shutdown hook
# ---------------------------------------------------------------------------

async def _post_shutdown(application: Application) -> None:
    """Close the HTTP client on bot shutdown."""
    client = get_client()
    await client.close()
    logger.info("Paperclip HTTP client closed")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Build and start the bot."""
    _setup_logging()
    config.validate()

    # Start metrics server (if enabled)
    start_metrics_server()

    # Build application
    builder = Application.builder().token(config.TELEGRAM_BOT_TOKEN)
    application = builder.build()

    # Register handlers and error handler
    register_handlers(application)
    application.add_error_handler(error_handler)

    # Graceful shutdown hook
    application.post_shutdown = _post_shutdown

    # Start in webhook or polling mode
    if config.WEBHOOK_URL:
        logger.info("Starting bot in WEBHOOK mode → %s", config.WEBHOOK_URL)
        application.run_webhook(
            listen="0.0.0.0",
            port=config.WEBHOOK_PORT,
            url_path=config.WEBHOOK_PATH,
            webhook_url=f"{config.WEBHOOK_URL}{config.WEBHOOK_PATH}",
        )
    else:
        logger.info("Starting bot in POLLING mode")
        application.run_polling()


if __name__ == "__main__":
    main()
