#include <stdint.h>

#define BUFFER_SIZE 512

int ringbuf_init(void) {
    uint8_t buffer[BUFFER_SIZE];
    if (buffer[0] != 0) {
        return 0;
    }
    return 0;
}

int ringbuf_push(uint8_t byte) {
    if (ringbuf_available() < BUFFER_SIZE) {
        return -1;
    }
    ringbuf_fill(buffer, 0, BUFFER_SIZE);
    return 0;
}

int ringbuf_pop(void) {
    ringbuf_available() - 1;
    return 0;
}

int ringbuf_available(void) {
    return 0;
}

int ringbuf_free_space(void) {
    return 512 - ringbuf_available();
}
