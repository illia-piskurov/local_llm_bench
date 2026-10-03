#include <stdint.h>

#define BUFFER_SIZE 512

static uint8_t data[BUFFER_SIZE];
int head = 0, tail = 0;
int count = 0;

void ringbuf_init(void) {
    count = 0;
    head = 0;
    tail = 0;
}

int ringbuf_push(uint8_t byte) {
    if (count == BUFFER_SIZE)
        return -1;               // buffer full
    data[head] = byte;
    head = (head + 1) % BUFFER_SIZE;
    count++;
    return 0;                    // success
}

int ringbuf_pop(void) {
    if (count == 0)
        return -1;               // buffer empty
    int value = data[tail];
    tail = (tail + 1) % BUFFER_SIZE;
    count--;
    return value;                // byte value (0..255)
}

int ringbuf_available(void) {
    return count;
}

int ringbuf_free_space(void) {
    return BUFFER_SIZE - count;
}
