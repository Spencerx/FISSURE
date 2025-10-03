#! /usr/bin/env python3
"""GNU Radio Flowgraph Plugin Operations Base Class and Decorators
"""
import asyncio
import logging
from gnuradio import gr

from fissure.utils.plugins.operations import setup_decorator as setup_decorator_base
from fissure.utils.plugins.operations import run_decorator as run_decorator_base
from fissure.utils.plugins.operations import stop_decorator as stop_decorator_base
from fissure.utils.plugins.operations import teardown_decorator as teardown_decorator_base
from fissure.utils.plugins.operations import Operation

def setup_decorator(func):
    """Decorator for setup method in OperationGR class
    """
    @setup_decorator_base
    async def wrapper(self, *args, **kwargs) -> bool:
        # initialize the gr top block
        self.tb_obj = self.tb()

        # call the decorated setup function
        status = await func(self, *args, **kwargs)
        return status
    return wrapper

def run_decorator(func):
    """Decorator for run method in OperationGR class
    """
    @run_decorator_base
    async def wrapper(self, *args, **kwargs) -> None:
        # call the decorated run function
        await func(self, *args, **kwargs)

        self.logger.debug(f"{self.__class__.__name__} starting...")
        self.tb_obj.start()
        self.logger.debug(f"{self.__class__.__name__} started.")
        while not self._stop:
            await asyncio.sleep(0.1)
    return wrapper

def stop_decorator(func):
    """Decorator for stop method in OperationGR class
    """
    @stop_decorator_base
    async def wrapper(self, *args, **kwargs) -> None:
        self.logger.debug(f"{self.__class__.__name__} top block stopping...")
        self.tb_obj.stop()
        self.tb_obj.wait()
        self.logger.debug(f"{self.__class__.__name__} top block stopped.")

        # call the decorated stop function
        await func(self, *args, **kwargs)
    return wrapper

def teardown_decorator(func):
    """Decorator for teardown method in OperationGR class
    """
    @teardown_decorator_base
    async def wrapper(self, *args, **kwargs) -> None:
        # call the decorated teardown function
        await func(self, *args, **kwargs)

        self.tb_obj = None
        self.logger.debug(f"{self.__class__.__name__} torn down.")
    return wrapper

class OperationGR(Operation):
    """GNU Radio Flowgraph Plugin Operations Base Class
    """
    def __init__(self, tb: gr.top_block, sensor_node_id: int | str = 0, logger: logging.Logger = logging.getLogger(__name__), alert_callback: callable = None, tak_cot_callback: callable = None) -> None:
        super().__init__(sensor_node_id, logger, alert_callback, tak_cot_callback)
        if not callable(tb):
            logger.error(f"tb {tb} is not callable")
        elif not issubclass(tb, gr.top_block):
            logger.error(f"tb {tb} is not a subclass of gr.top_block")
        self.tb = tb

    @setup_decorator
    async def setup(self) -> bool:
        """Setup the operation

        Returns
        -------
        bool
            True if setup was successful, False otherwise
        """
        return True

    @run_decorator
    async def run(self) -> None:
        """Run the operation
        """
        return

    @stop_decorator
    async def stop(self) -> None:
        """Stop the operation
        """
        return

    @teardown_decorator
    async def teardown(self) -> None:
        """Teardown the operation
        """
        return