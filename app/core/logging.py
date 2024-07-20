""" ロギングのセットアップを行うためのモジュール"""

import logging


def setup_logging():
    """ロギングのセットアップ"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)
    logger.info("Logging set up is done :)")
