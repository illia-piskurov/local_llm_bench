#include <stdint.h>
#include <stdbool.h>

#define BUFFER_SIZE 512

static uint8_t buffer[BUFFER_SIZE];
static size_t head = 0;    // Next write position (circular index)
static size_t tail = 0;   // Next read position (circular index)
static bool is_full = false;

void ringbuf_init(void) {
    head = 0;
    tail = 0;
    is_full = false;
}

int ringbuf_push(uint8_t byte) {
    if (is_full || ((head + 1) % BUFFER_SIZE) == tail) {
        return -1; // Buffer full
    }

    buffer[head] = byte;
    head = (head + 1) % BUFFER_SIZE;

    if (tail == head && is_full) {
        is_full = false;
    }
    return 0;
}

int ringbuf_pop(void) {
    if (tail == head && !is_full) {
        return -1; // Buffer empty
    }

    uint8_t byte = buffer[tail];
    tail = (tail + 1) % BUFFER_SIZE;

    if (head == tail) {
        is_full = false;
    }
    return byte;
}

int ringbuf_available(void) {
    size_t available = head - tail;
    if (available < 0) available += BUFFER_SIZE; // Handle circular wrap
    return available;
}

int ringbuf_free_space(void) {
    return BUFFER_SIZE - ringbuf_available();
}
