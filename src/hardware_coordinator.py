"""
Hardware Coordination System
Allows Gary remote commands to take precedence over local main app
"""

import time
import fcntl
import os
from pathlib import Path
from loguru import logger


class HardwareCoordinator:
    """
    Coordinates hardware access between main app and remote server

    Uses file locking to ensure only one process controls hardware at a time.
    Remote (Gary) commands get priority over local button presses.
    """

    def __init__(self, lock_file="/tmp/gairihead_hardware.lock"):
        """
        Initialize hardware coordinator

        Args:
            lock_file: Path to lock file for coordination
        """
        self.lock_file = lock_file
        self.lock_fd = None
        self.is_locked = False

    def acquire(self, timeout=5.0, is_remote=False):
        """
        Acquire hardware lock

        Args:
            timeout: How long to wait for lock (seconds)
            is_remote: If True, this is a remote (Gary) command (higher priority)

        Returns:
            True if lock acquired, False if timeout
        """
        start_time = time.time()

        while True:
            try:
                # Open lock file
                self.lock_fd = open(self.lock_file, 'w')

                # Try to acquire exclusive lock (non-blocking)
                fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

                # Write who has the lock
                self.lock_fd.write(f"{'remote' if is_remote else 'local'}: {os.getpid()}\n")
                self.lock_fd.flush()

                self.is_locked = True
                logger.debug(f"Hardware lock acquired ({'remote' if is_remote else 'local'})")
                return True

            except IOError:
                # Lock is held by another process
                elapsed = time.time() - start_time

                if elapsed >= timeout:
                    logger.warning(f"Hardware lock timeout after {timeout}s")
                    if self.lock_fd:
                        self.lock_fd.close()
                        self.lock_fd = None
                    return False

                # Wait a bit and retry
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Hardware lock acquire error: {e}")
                if self.lock_fd:
                    self.lock_fd.close()
                    self.lock_fd = None
                return False

    def release(self):
        """Release hardware lock"""
        if self.is_locked and self.lock_fd:
            try:
                fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
                self.lock_fd.close()
                self.is_locked = False
                logger.debug("Hardware lock released")
            except Exception as e:
                logger.error(f"Hardware lock release error: {e}")
            finally:
                self.lock_fd = None

    def __enter__(self):
        """Context manager support"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support - auto-release"""
        self.release()
        return False


# Singleton instance for easy import
_coordinator = HardwareCoordinator()


def get_coordinator():
    """Get global hardware coordinator instance"""
    return _coordinator
