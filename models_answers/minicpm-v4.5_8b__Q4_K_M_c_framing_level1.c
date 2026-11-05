#include <stdint.h>

#define BUFFER_SIZE 512
static uint8_t buffer[BUFFER_SIZE];
static uint8_t head = 0;
static uint8_t tail = 0;
static uint8_t count = 0;

void ringbuf_init(void) {
    head = 0;
    tail = 0;
    count = 0;
}

int ringbuf_push(uint8_t byte) {
    if (count == BUFFER_SIZE) return -1;
    buffer[head] = byte;
    head = (head + 1) % BUFFER_SIZE;
    count++;
    return 0;
}

int ringbuf_pop(void) {
    if (count == 0) return -1;
    uint8_t byte = buffer[tail];
    tail = (tail + 1) % BUFFER_SIZE;
    count--;
    return byte;
}

int ringbuf_available(void) {
    return count;
}

int ringbuf_free_space(void) {
    return BUFFER_SIZE - count;
}
