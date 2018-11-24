import abc

from aio import _loop


class BaseFuture(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def result(self) -> object:
        raise NotImplementedError

    @abc.abstractmethod
    def set_result(self, result) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def exception(self) -> Exception:
        raise NotImplementedError

    @abc.abstractmethod
    def set_exception(self, exception) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def done(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def add_done_callback(self, callback) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def remove_done_callback(self, callback) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def cancel(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def cancelled(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def get_loop(self) -> _loop.Loop:
        raise NotImplementedError
