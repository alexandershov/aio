class Loop:
    def call_soon(self, callback):
        pass

    def stop(self) -> None:
        pass

    def is_running(self) -> bool:
        pass

    def run_forever(self) -> None:
        pass


def get_event_loop() -> Loop:
    return Loop()
