import typing
import logging
from abc import ABC, abstractmethod
from pathlib import Path
import torch.nn as nn

from tensorboardX import SummaryWriter

try:
    import wandb
    WANDB_FOUND = True
except ImportError:
    WANDB_FOUND = False

logger = logging.getLogger(__name__)


class TAPEVisualizer(ABC):
    """Base class for visualization in TAPE"""

    @abstractmethod
    def __init__(self, log_dir: typing.Union[str, Path], exp_name: str):
        raise NotImplementedError

    @abstractmethod
    def log_config(self, config: typing.Dict[str, typing.Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def watch(self, model: nn.Module) -> None:
        raise NotImplementedError

    @abstractmethod
    def log_metrics(self,
                    metrics_dict: typing.Dict[str, float],
                    split: str,
                    step: int):
        raise NotImplementedError


class DummyVisualizer(TAPEVisualizer):
    """Dummy class that doesn't do anything. Used for non-master branches."""

    def __init__(self, log_dir: typing.Union[str, Path] = '', exp_name: str = ''):
        pass

    def log_config(self, config: typing.Dict[str, typing.Any]) -> None:
        pass

    def watch(self, model: nn.Module) -> None:
        pass

    def log_metrics(self,
                    metrics_dict: typing.Dict[str, float],
                    split: str,
                    step: int):
        pass


class TBVisualizer(TAPEVisualizer):

    def __init__(self, log_dir: typing.Union[str, Path], exp_name: str):
        log_dir = Path(log_dir) / exp_name
        logger.info(f"tensorboard file at: {log_dir}")
        self.logger = SummaryWriter(log_dir=str(log_dir))

    def log_config(self, config: typing.Dict[str, typing.Any]) -> None:
        logger.warn("Cannot log config when using a TBVisualizer. "
                    "Configure wandb for this functionality")

    def watch(self, model: nn.Module) -> None:
        logger.warn("Cannot watch models when using a TBVisualizer. "
                    "Configure wandb for this functionality")

    def log_metrics(self,
                    metrics_dict: typing.Dict[str, float],
                    split: str,
                    step: int):
        for name, value in metrics_dict.items():
            self.logger.add_scalar(split + "/" + name, value, step)


class WandBVisualizer(TAPEVisualizer):

    def __init__(self, log_dir: typing.Union[str, Path], exp_name: str):
        if not WANDB_FOUND:
            raise ImportError("wandb module not available")
        wandb.init(project="tape", dir=log_dir, name=exp_name)

    def log_config(self, config: typing.Dict[str, typing.Any]) -> None:
        wandb.config.update(config)

    def watch(self, model: nn.Module):
        wandb.watch(model)

    def log_metrics(self,
                    metrics_dict: typing.Dict[str, float],
                    split: str,
                    step: int):
        wandb.log({f"{split.capitalize()} {name.capitalize()}": value
                   for name, value in metrics_dict.items()}, step=step)


def get(log_dir: typing.Union[str, Path], exp_name: str, local_rank: int) -> TAPEVisualizer:
    if local_rank not in (-1, 0):
        return DummyVisualizer(log_dir, exp_name)
    elif WANDB_FOUND:
        return WandBVisualizer(log_dir, exp_name)
    else:
        return TBVisualizer(log_dir, exp_name)
