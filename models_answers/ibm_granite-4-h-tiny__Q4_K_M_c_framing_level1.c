#include <stdint.h>

#define BUFFER_SIZE 512

static uint8_t buffer[BUFFER_SIZE];
static size_t head = 0;
static size_t tail = 0;

void ringbuf_init(void) {
    head = 0;
    tail = 0;
}

int ringbuf_push(uint8_t byte) {
    if (ringbuf_available() == BUFFER_SIZE) {
        return -1; /* buffer full */
    }
    buffer[head] = byte;
    head = (head + 1) % BUFFER_SIZE;
    return 0;
}

int ringbuf_pop(void) {
    if (tail == head) {
        return -1; /* buffer empty */
    }
    int value = buffer[tail];
    tail = (tail + 1) % BUFFER_SIZE;
    return value;
}

int ringbuf_available(void) {
    size_t diff = (head >= tail) ? (head - tail) : (BUFFER_SIZE - (tail - head));
    return diff;
}

int ringbuf_free_space(void) {
    return BUFFER_SIZE - ringbuf_available();
}
