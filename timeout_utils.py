"""
Общая защита от зависаний при вызове кода, сгенерированного моделью
(например бесконечный цикл из-за незакрытого JMP). Функция вызывается
в отдельном процессе с таймаутом; если процесс не успел — он принудительно
убивается через terminate(), а тест засчитывается как проваленный с понятной
причиной, вместо зависания всей программы.
"""

import importlib.util
import multiprocessing as mp

TEST_TIMEOUT_SECONDS = 5


def load_function(path: str, func_name: str):
    spec = importlib.util.spec_from_file_location("solution", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, func_name):
        raise AttributeError(f"В решении не найдена функция {func_name}(...)")
    return getattr(module, func_name)


def _worker_call(path: str, func_name: str, args: tuple, queue: mp.Queue) -> None:
    try:
        fn = load_function(path, func_name)
        queue.put((True, fn(*args)))
    except Exception as e:
        queue.put((False, e))


def call_with_timeout(
    path: str,
    func_name: str,
    args: tuple,
    timeout_seconds: int = TEST_TIMEOUT_SECONDS,
) -> tuple[bool, object]:
    """Вызывает func_name(*args) из решения по пути path в отдельном процессе.
    Возвращает (True, результат) при успехе или (False, исключение) при ошибке
    либо зависании (TimeoutError после terminate())."""
    queue: mp.Queue = mp.Queue()
    process = mp.Process(target=_worker_call, args=(path, func_name, args, queue))
    process.start()
    process.join(timeout_seconds)

    if process.is_alive():
        process.terminate()
        process.join()
        return False, TimeoutError(f"превышен таймаут {timeout_seconds}с (вероятно бесконечный цикл)")

    if queue.empty():
        return False, RuntimeError("подпроцесс не вернул результат (возможно, аварийно завершился)")

    return queue.get()
