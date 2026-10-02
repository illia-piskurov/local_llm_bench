"""C99 Кольцевой буфер и бинарный протокол (WASM) бенчмарк.

Тестирует написание низкоуровневого системного кода на C99:
- Level 1: Статический кольцевой буфер (ringbuf_init, push, pop, available, free_space).
- Level 2: Декодер пакетов со сканированием мусора и контрольной суммой XOR.
- Level 3: Потоковый сетевой парсер с фрагментацией данных.

Код компилируется на лету через Zig CC в WASM и безопасно исполняется в песочнице Wasmtime.
"""

import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from wasmtime import Store

from benchmarks.base import Benchmark, Level, TestResult
from sandboxes import compile_c_to_wasm, load_wasm

LEVEL1_PROMPT = """\
Реализуй кольцевой буфер (ring buffer) фиксированного размера на языке C99.

Требования к буферу:
- Размер буфера: 512 байт (#define BUFFER_SIZE 512 или статический массив на 512 элементов).
- Без динамического выделения памяти (никакого malloc/free), используй статическую память.
- Чистый C99 (#include <stdint.h>).

Функции для реализации:
- void ringbuf_init(void) — инициализирует или сбрасывает буфер в начальное пустое состояние.
- int ringbuf_push(uint8_t byte) — добавляет один байт в буфер. Возвращает 0 при успехе, или -1 если буфер полон (в буфере уже 512 байт).
- int ringbuf_pop(void) — извлекает один байт из буфера по принципу FIFO. Возвращает значение байта (0..255) при успехе, или -1 если буфер пуст.
- int ringbuf_available(void) — возвращает текущее количество байт, находящихся в буфере (от 0 до 512).
- int ringbuf_free_space(void) — возвращает оставшееся свободное место в буфере (512 - available).

В ответе верни только C код одним блоком ```c ... ```, без пояснений вне блока.
"""

LEVEL2_PROMPT = """\
Дополни свою реализацию декодером бинарных пакетов.

Формат пакета:
[0xAA (Magic, 1B)] [type (1B)] [len (1B)] [payload (len B)] [checksum (1B)]
- Magic byte: всегда 0xAA.
- type: uint8_t — тип сообщения (0..255).
- len: uint8_t — длина полезной нагрузки (0..255 байт).
- payload: len байт полезной нагрузки.
- checksum: uint8_t — контрольная сумма, вычисляемая как XOR всех байт payload (если len == 0, checksum равен 0).
Полный размер корректного пакета = 3 + len + 1 = len + 4 байт.

Функция для реализации:
int decode_packet(const uint8_t *stream, int stream_len, uint8_t *out_payload, int *out_type);

Требования:
- Функция сканирует stream и ищет первый валидный пакет.
- Если перед пакетом идёт мусор или ложные байты 0xAA (у которых повреждена длина или контрольная сумма), функция должна пропускать мусор и находить валидный пакет.
- При успешном обнаружении пакета:
  - Копирует байты payload в out_payload.
  - Записывает тип сообщения в *out_type.
  - Возвращает длину payload (>= 0).
- Если валидный пакет не найден или данных недостаточно — возвращает -1.
- Сохрани функции кольцевого буфера из Level 1.

В ответе верни только C код одним блоком ```c ... ```, без пояснений вне блока.
"""

LEVEL3_PROMPT = """\
Дополни свою реализацию потоковым парсером (streaming parser) с поддержкой фрагментации по сети.

Данные поступают произвольными кусками в кольцевой буфер и извлекаются по мере готовности пакетов.

Функции для реализации:
- void feed_bytes(const uint8_t *data, int len) — помещает входящие байты в кольцевой буфер. Если буфер переполнен, отбрасывает то, что не поместилось.
- int get_next_packet(uint8_t *out_payload, int *out_type) — проверяет кольцевой буфер на наличие завершённого пакета (формат из Level 2: 0xAA, type, len, payload, checksum):
  - Если полный валидный пакет найден: извлекает его из кольцевого буфера (продвигая буфер вперед), копирует payload в out_payload, записывает type в *out_type и возвращает длину payload.
  - Если в буфере встретились мусорные байты перед пакетом или ложный 0xAA с битой контрольной суммой — мусор удаляется из буфера до следующего кандидата.
  - Если пакет ещё не полон (ждёт следующих фрагментов) или буфер пуст — возвращает -1, не удаляя незавершённый пакет из буфера.

Сохрани функции из Level 1 и Level 2.

В ответе верни только C код одним блоком ```c ... ```, без пояснений вне блока.
"""


# ── LEVEL 1 TESTS ──
def test_ringbuf_empty_state(store: Store, exp: Any) -> bool:
    exp["ringbuf_init"](store)
    return (
        exp["ringbuf_available"](store) == 0
        and exp["ringbuf_free_space"](store) == 512
        and exp["ringbuf_pop"](store) == -1
    )


def test_ringbuf_push_pop(store: Store, exp: Any) -> bool:
    exp["ringbuf_init"](store)
    for b in [10, 20, 30]:
        if exp["ringbuf_push"](store, b) != 0:
            return False
    if exp["ringbuf_available"](store) != 3 or exp["ringbuf_free_space"](store) != 509:
        return False
    return (
        exp["ringbuf_pop"](store) == 10
        and exp["ringbuf_pop"](store) == 20
        and exp["ringbuf_pop"](store) == 30
        and exp["ringbuf_pop"](store) == -1
    )


def test_ringbuf_wrap_around(store: Store, exp: Any) -> bool:
    exp["ringbuf_init"](store)
    for i in range(300):
        if exp["ringbuf_push"](store, i % 256) != 0:
            return False
    for i in range(200):
        if exp["ringbuf_pop"](store) != (i % 256):
            return False
    for i in range(300):
        if exp["ringbuf_push"](store, (i + 50) % 256) != 0:
            return False
    return exp["ringbuf_available"](store) == 400


def test_ringbuf_full_overflow(store: Store, exp: Any) -> bool:
    exp["ringbuf_init"](store)
    for i in range(512):
        if exp["ringbuf_push"](store, 0x55) != 0:
            return False
    if exp["ringbuf_push"](store, 0xFF) != -1:
        return False
    return exp["ringbuf_free_space"](store) == 0


LEVEL1_CASES: list[tuple[str, Callable]] = [
    ("empty_state", test_ringbuf_empty_state),
    ("basic_push_pop", test_ringbuf_push_pop),
    ("pointer_wrap_around", test_ringbuf_wrap_around),
    ("full_overflow_check", test_ringbuf_full_overflow),
]


# ── LEVEL 2 TESTS: Packet Decoder ──
def _make_packet(pkt_type: int, payload: bytes) -> bytes:
    crc = 0
    for b in payload:
        crc ^= b
    return bytes([0xAA, pkt_type, len(payload)]) + payload + bytes([crc])


def test_decode_clean_packet(store: Store, exp: Any) -> bool:
    mem = exp["memory"]
    fn = exp["decode_packet"]
    pkt = _make_packet(1, b"hello")
    mem.write(store, pkt, 1024)
    res_len = fn(store, 1024, len(pkt), 2048, 3072)
    if res_len != 5:
        return False
    out_type = int.from_bytes(mem.read(store, 3072, 3076), "little")
    out_payload = bytes(mem.read(store, 2048, 2048 + 5))
    return out_type == 1 and out_payload == b"hello"


def test_decode_with_junk_prefix(store: Store, exp: Any) -> bool:
    mem = exp["memory"]
    fn = exp["decode_packet"]
    pkt = _make_packet(42, bytes([0x01, 0x02, 0x03, 0x04]))
    stream = b"NOISE_GARBAGE\x00\xff" + pkt
    mem.write(store, stream, 1024)
    res_len = fn(store, 1024, len(stream), 2048, 3072)
    if res_len != 4:
        return False
    out_type = int.from_bytes(mem.read(store, 3072, 3076), "little")
    out_payload = bytes(mem.read(store, 2048, 2048 + 4))
    return out_type == 42 and out_payload == bytes([0x01, 0x02, 0x03, 0x04])


def test_decode_bad_checksum(store: Store, exp: Any) -> bool:
    mem = exp["memory"]
    fn = exp["decode_packet"]
    bad_pkt = bytes([0xAA, 10, 2, 0x11, 0x22, 0xFF])
    mem.write(store, bad_pkt, 1024)
    res = fn(store, 1024, len(bad_pkt), 2048, 3072)
    return res == -1


def test_decode_false_magic_byte(store: Store, exp: Any) -> bool:
    mem = exp["memory"]
    fn = exp["decode_packet"]
    valid_pkt = _make_packet(5, b"valid")
    stream = bytes([0xAA, 0x99, 0x02, 0x10, 0x20, 0x00]) + valid_pkt
    mem.write(store, stream, 1024)
    res_len = fn(store, 1024, len(stream), 2048, 3072)
    if res_len != 5:
        return False
    out_type = int.from_bytes(mem.read(store, 3072, 3076), "little")
    out_payload = bytes(mem.read(store, 2048, 2048 + 5))
    return out_type == 5 and out_payload == b"valid"


LEVEL2_CASES: list[tuple[str, Callable]] = [
    ("clean_packet", test_decode_clean_packet),
    ("with_junk_prefix", test_decode_with_junk_prefix),
    ("reject_bad_checksum", test_decode_bad_checksum),
    ("recover_after_false_magic", test_decode_false_magic_byte),
]


# ── LEVEL 3 TESTS: Streaming with Fragmentation ──
def test_streaming_fragmented_packet(store: Store, exp: Any) -> bool:
    exp["ringbuf_init"](store)
    mem = exp["memory"]
    pkt = _make_packet(100, b"fragmented_data")

    c1, c2, c3 = pkt[:3], pkt[3:10], pkt[10:]
    mem.write(store, c1, 1024)
    exp["feed_bytes"](store, 1024, len(c1))
    if exp["get_next_packet"](store, 2048, 3072) != -1:
        return False

    mem.write(store, c2, 1024)
    exp["feed_bytes"](store, 1024, len(c2))
    if exp["get_next_packet"](store, 2048, 3072) != -1:
        return False

    mem.write(store, c3, 1024)
    exp["feed_bytes"](store, 1024, len(c3))

    res_len = exp["get_next_packet"](store, 2048, 3072)
    if res_len != len(b"fragmented_data"):
        return False
    out_type = int.from_bytes(mem.read(store, 3072, 3076), "little")
    out_payload = bytes(mem.read(store, 2048, 2048 + res_len))
    return out_type == 100 and out_payload == b"fragmented_data"


def test_streaming_multiple_sequential_packets(store: Store, exp: Any) -> bool:
    exp["ringbuf_init"](store)
    mem = exp["memory"]
    p1 = _make_packet(1, b"pkt1")
    p2 = _make_packet(2, b"pkt2_longer")
    both = p1 + p2
    mem.write(store, both, 1024)
    exp["feed_bytes"](store, 1024, len(both))

    l1 = exp["get_next_packet"](store, 2048, 3072)
    t1 = int.from_bytes(mem.read(store, 3072, 3076), "little")
    d1 = bytes(mem.read(store, 2048, 2048 + l1))

    l2 = exp["get_next_packet"](store, 2048, 3072)
    t2 = int.from_bytes(mem.read(store, 3072, 3076), "little")
    d2 = bytes(mem.read(store, 2048, 2048 + l2))

    l3 = exp["get_next_packet"](store, 2048, 3072)

    return (
        l1 == 4
        and t1 == 1
        and d1 == b"pkt1"
        and l2 == len(b"pkt2_longer")
        and t2 == 2
        and d2 == b"pkt2_longer"
        and l3 == -1
    )


LEVEL3_CASES: list[tuple[str, Callable]] = [
    ("fragmented_packet", test_streaming_fragmented_packet),
    ("sequential_packets", test_streaming_multiple_sequential_packets),
]


def run_c_suite(cases: list[tuple[str, Callable]], c_path: Path) -> tuple[int, int, list[str]]:
    if not c_path.exists():
        return 0, len(cases), [f"Файл {c_path} не найден"]

    with tempfile.NamedTemporaryFile(suffix=".wasm", delete=False) as tmp:
        wasm_path = Path(tmp.name)

    try:
        ok, err = compile_c_to_wasm(c_path, wasm_path)
        if not ok:
            return 0, len(cases), [f"Ошибка компиляции C99 -> WASM: {err}"]

        store, exports = load_wasm(wasm_path)

        passed = 0
        failures: list[str] = []
        for test_name, test_fn in cases:
            try:
                res = test_fn(store, exports)
                if res:
                    passed += 1
                else:
                    failures.append(f"{test_name}: проверка вернула False")
            except Exception as e:
                failures.append(f"{test_name}: исключение {e}")

        return passed, len(cases), failures
    finally:
        if wasm_path.exists():
            try:
                wasm_path.unlink()
            except Exception:
                pass


class CFramingBenchmark(Benchmark):
    id = "c_framing"
    name = "C99: Кольцевой буфер и бинарный протокол (WASM)"
    short = "C Framing"
    file_ext = "c"
    code_lang = "c"
    code_lang_aliases = ("c99",)
    levels = [
        Level(id="level1", name="Level 1 (RingBuffer 512B)", prompt=LEVEL1_PROMPT, requires=None),
        Level(id="level2", name="Level 2 (PacketDecoder & XOR CRC)", prompt=LEVEL2_PROMPT, requires="level1"),
        Level(id="level3", name="Level 3 (StreamingParser & Fragmentation)", prompt=LEVEL3_PROMPT, requires="level2"),
    ]

    def run_tests(self, level_id: str, answer_path: Path) -> TestResult:
        if level_id == "level1":
            cases = LEVEL1_CASES
        elif level_id == "level2":
            cases = LEVEL1_CASES + LEVEL2_CASES
        else:
            cases = LEVEL1_CASES + LEVEL2_CASES + LEVEL3_CASES

        passed, total, failures = run_c_suite(cases, answer_path)
        return TestResult(passed, total, failures)
