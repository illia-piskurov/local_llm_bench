#include <stdint.h>

#define BUFFER_SIZE 512

static uint8_t buffer[BUFFER_SIZE];
static volatile int head = 0;
static volatile int tail = 0;

void ringbuf_init(void) {
    head = 0;
    tail = 0;
}

int ringbuf_push(uint8_t byte) {
    if ((tail + 1) % BUFFER_SIZE == head) {
        return -1; // Buffer is full
    }
    buffer[tail] = byte;
    tail = (tail + 1) % BUFFER_SIZE;
    return 0;
}

int ringbuf_pop(void) {
    if (head == tail) {
        return -1; // Buffer is empty
    }
    uint8_t byte = buffer[head];
    head = (head + 1) % BUFFER_SIZE;
    return byte;
}

int ringbuf_available(void) {
    return (tail - head + BUFFER_SIZE) % BUFFER_SIZE;
}

int ringbuf_free_space(void) {
    return BUFFER_SIZE - ringbuf_available();
}
