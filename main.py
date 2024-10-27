import sys
import logging
import traceback
from application import Application


def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("ai_assistant.log"),
        ],
    )


def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        logger.info("=== Starting AI Assistant ===")
        app = Application()
        return app.run()
    except Exception as e:
        logger.error(f"!!! Fatal error: {str(e)}")
        logger.error(f"Stack trace:\n{traceback.format_exc()}")
        return 1
    finally:
        logger.info("=== AI Assistant Shutdown ===")


if __name__ == "__main__":
    sys.exit(main())
