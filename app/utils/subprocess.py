import subprocess
import logging

logger = logging.getLogger(__name__)


def execute(*args, **kwargs):
    # デフォルト値を設定
    kwargs.setdefault("capture_output", True)
    kwargs.setdefault("text", True)
    kwargs.setdefault("check", True)
    kwargs.setdefault("timeout", 60)
    kwargs.setdefault("text", True)

    command = list(args)
    try:
        result = subprocess.run(command, **kwargs)
        return result
    except subprocess.TimeoutExpired as e:
        logger.error("Error processing message subprocess timeout exprired error:%s", e)
    except subprocess.CalledProcessError as e:
        logger.error(
            "Error processing message subprocess called processing error:%s", e
        )
