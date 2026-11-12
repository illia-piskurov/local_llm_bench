#include <stdint.h>

static uint8_t buffer[BUFFER_SIZE];

void ringbuf_init(void) {
    buffer[0] = 0;
}

int ringbuf_push(uint8_t byte) {
    if (buffer[0] == 0) {
        buffer[0] = byte;
        return 0;
    } else {
        return -1;
    }
}

int ringbuf_pop(void) {
    if (buffer[0] == 0) {
        return -1;
    } else {
        uint8_t byte = buffer[0];
        buffer[0] = 0;
        return byte;
    }
}

int ringbuf_available(void) {
    return buffer[0] != 0;
}

int ringbuf_free_space(void) {
    return BUFFER_SIZE - buffer[0];
}
