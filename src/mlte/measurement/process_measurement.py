"""
Base class for measurement of external processes asynchronously.
"""

from __future__ import annotations

import threading
import time
from typing import List, Optional

from .measurement import Measurement
from .result import Result
from mlte._private import job

# -----------------------------------------------------------------------------
# ProcessMeasurement
# -----------------------------------------------------------------------------


class ProcessMeasurement(Measurement):
    """Base class to be extended to measure external processes."""

    @staticmethod
    def start_script(script: str, arguments: List[str]) -> int:
        """
        Initialize an external Python process running training or similar script.

        :param script: The full path to a Python script with the training or equivalent process to run.
        :type script: str

        :param arguments: A list of string arguments for the process.
        :type arguments: List[str[]

        :return: the id of the process that was created.
        :rtype: int
        """
        return job.spawn_python_job(script, arguments)

    @staticmethod
    def start_process(process: str, arguments: List[str]) -> int:
        """
        Initialize an external process running training or similar.

        :param process: The full path to a process to run.
        :type script: str

        :param arguments: A list of string arguments for the process.
        :type arguments: List[str[]

        :return: the id of the process that was created.
        :rtype: int
        """
        return job.spawn_job(process, arguments)

    def __init__(self, instance: ProcessMeasurement, identifier: str):
        """
        Initialize a new ProcessMeasurement measurement.

        :param identifier: A unique identifier for the measurement
        :type identifier: str
        """
        super().__init__(instance, identifier)
        self.thread: Optional[threading.Thread] = None
        self.result: Optional[Result] = None
        self.error: str = ""

    def evaluate_async(self, pid: int, *args, **kwargs):
        """
        Monitor an external process at `pid` in a separate thread until it stops.
        Equivalent to evaluate(), but does not return the result immediately as it works in the background.

        :param pid: The process identifier
        :type pid: int
        """

        # Evaluate the measurement
        self.error = ""
        self.result = None
        self.thread = threading.Thread(
            target=lambda: self._run_call(pid, *args, **kwargs)
        )
        self.thread.start()

    def _run_call(self, pid, *args, **kwargs):
        """
        Runs the internall __call__ method that should implement the measurement, and stores its results when it finishes.
        """
        try:
            self.result = self.__call__(pid, *args, **kwargs)
        except Exception as e:
            self.error = f"Could not evaluate process: {e}"

    def wait_for_result(self, poll_interval: int = 1) -> Result:
        """
        Needed to get the results of a measurement executed in parallel using evaluate_async. Waits for the thread to finish.

        :param poll_interval: The poll interval in seconds
        :type poll_interval: int

        :return: The result of measurement execution, with semantics
        :rtype: Result
        """
        # Wait for thread to finish, and return results once it is done.
        if self.thread is None:
            raise Exception(
                "Can't wait for result, no process is currently running."
            )
        while self.thread.is_alive():
            time.sleep(poll_interval)

        # If an exception was raised, return it here as an exception as well.
        if self.error != "":
            raise RuntimeError(self.error)

        if self.result is None:
            raise Exception("No valid result was returned from measurement.")
        return self.result