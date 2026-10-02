"""C99 Ring Buffer and Binary Protocol (WASM) benchmark.

Tests low-level C99 systems programming capabilities:
- Level 1: Static ring buffer (ringbuf_init, push, pop, available, free_space).
- Level 2: Binary packet decoder with noise scanning and XOR checksum verification.
- Level 3: Streaming network parser with fragmented data handling.

Code is compiled on the fly via Zig CC to WASM and safely executed in Wasmtime sandbox.
"""

import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from wasmtime import Store

from benchmarks.base import Benchmark, Level, TestResult
from sandboxes import compile_c_to_wasm, load_wasm

LEVEL1_PROMPT = """\
Implement a fixed-size ring buffer in C99.

Buffer requirements:
- Buffer size: 512 bytes (#define BUFFER_SIZE 512 or static array of 512 elements).
- No dynamic memory allocation (no malloc/free), use static memory only.
- Pure C99 (#include <stdint.h>).

Functions to implement:
- void ringbuf_init(void) — initializes or resets the buffer to an empty initial state.
- int ringbuf_push(uint8_t byte) — pushes one byte into the buffer. Returns 0 on success, or -1 if the buffer is full (already contains 512 bytes).
- int ringbuf_pop(void) — pops one byte from the buffer following FIFO ordering. Returns byte value (0..255) on success, or -1 if the buffer is empty.
- int ringbuf_available(void) — returns the current number of bytes stored in the buffer (0 to 512).
- int ringbuf_free_space(void) — returns remaining free space in the buffer (512 - available).

Return only the C code in a single ```c ... ``` code block, with no explanations outside the block.
"""

LEVEL2_PROMPT = """\
Extend your implementation with a binary packet decoder.

Packet format:
[0xAA (Magic, 1B)] [type (1B)] [len (1B)] [payload (len B)] [checksum (1B)]
- Magic byte: always 0xAA.
- type: uint8_t — message type identifier (0..255).
- len: uint8_t — payload length (0..255 bytes).
- payload: len bytes of payload data.
- checksum: uint8_t — checksum calculated as XOR of all payload bytes (if len == 0, checksum is 0).
Total valid packet length = 3 + len + 1 = len + 4 bytes.

Function to implement:
int decode_packet(const uint8_t *stream, int stream_len, uint8_t *out_payload, int *out_type);

Requirements:
- Scan stream and locate the first valid packet.
- If preceded by noise bytes or false 0xAA markers (corrupted length or checksum), skip the noise and find the valid packet.
- Upon valid packet discovery:
  - Copy payload bytes into out_payload.
  - Write message type to *out_type.
  - Return payload length (>= 0).
- If no valid packet found or insufficient data, return -1.
- Preserve all ring buffer functions from Level 1.

Return only the C code in a single ```c ... ``` code block, with no explanations outside the block.
"""

LEVEL3_PROMPT = """\
Extend your implementation with a streaming parser supporting network data fragmentation.

Data arrives in arbitrary chunks into the ring buffer and is extracted as packets complete.

Functions to implement:
- void feed_bytes(const uint8_t *data, int len) — feeds incoming bytes into the ring buffer. If buffer overflows, discard bytes that do not fit.
- int get_next_packet(uint8_t *out_payload, int *out_type) — checks the ring buffer for a completed packet (format from Level 2: 0xAA, type, len, payload, checksum):
  - If a full valid packet is found: pop it from the ring buffer (advancing the buffer), copy payload to out_payload, write type to *out_type, and return payload length.
  - If noise bytes or false 0xAA headers precede the packet, discard noise up to the next candidate.
  - If packet is incomplete (awaiting future chunks) or buffer is empty, return -1 without discarding incomplete packet data.

Preserve all functions from Level 1 and Level 2.

Return only the C code in a single ```c ... ``` code block, with no explanations outside the block.
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
        return 0, len(cases), [f"File {c_path} not found"]

    with tempfile.NamedTemporaryFile(suffix=".wasm", delete=False) as tmp:
        wasm_path = Path(tmp.name)

    try:
        ok, err = compile_c_to_wasm(c_path, wasm_path)
        if not ok:
            return 0, len(cases), [f"C99 -> WASM compilation error: {err}"]

        store, exports = load_wasm(wasm_path)

        passed = 0
        failures: list[str] = []
        for test_name, test_fn in cases:
            try:
                res = test_fn(store, exports)
                if res:
                    passed += 1
                else:
                    failures.append(f"{test_name}: assertion returned False")
            except Exception as e:
                failures.append(f"{test_name}: exception {e}")

        return passed, len(cases), failures
    finally:
        if wasm_path.exists():
            try:
                wasm_path.unlink()
            except Exception:
                pass


class CFramingBenchmark(Benchmark):
    id = "c_framing"
    name = "C99: Ring Buffer & Binary Protocol (WASM)"
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
