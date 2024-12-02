import logging
import os
import time
from functools import wraps

import psutil

logger = logging.getLogger(__name__)


def resource_usage(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        process = psutil.Process(os.getpid())
        start_memory = process.memory_info().rss
        start_cpu_percent = process.cpu_percent(interval=None)
        start_cpu_times = process.cpu_times()

        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        end_memory = process.memory_info().rss
        end_cpu_percent = process.cpu_percent(interval=None)
        end_cpu_times = process.cpu_times()

        memory_usage = (end_memory - start_memory) / (1024 * 1024)  # Convert to MB
        cpu_percent_usage = end_cpu_percent - start_cpu_percent
        user_ticks = end_cpu_times.user - start_cpu_times.user
        system_ticks = end_cpu_times.system - start_cpu_times.system
        idle_ticks = (end_cpu_times.idle - start_cpu_times.idle) if hasattr(end_cpu_times, "idle") else 0

        logger.info("Function '%s' executed in %.4f seconds", func.__name__, end_time - start_time)
        logger.info("Memory usage: %.4f MB", memory_usage)
        logger.info("CPU percent usage: %.4f%%", cpu_percent_usage)
        logger.info("User ticks: %.4f", user_ticks)
        logger.info("System ticks: %.4f", system_ticks)
        logger.info("Idle ticks: %.4f", idle_ticks)

        return result

    return wrapper
