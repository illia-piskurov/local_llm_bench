#include <stdint.h>

#define BUFFER_SIZE 512

static uint8_t buffer[BUFFER_SIZE];
static int head = 0;
static int tail = 0;

void ringbuf_init(void) {
    head = tail = 0;
}

int ringbuf_push(uint8_t byte) {
    if ((head + 1) % BUFFER_SIZE == tail) {
        return -1;
    }
    buffer[head] = byte;
    head = (head + 1) % BUFFER_SIZE;
    return 0;
}

int ringbuf_pop(void) {
    if (head == tail) {
        return -1;
    }
    uint8_t byte = buffer[tail];
    tail = (tail + 1) % BUFFER_SIZE;
    return byte;
}

int ringbuf_available(void) {
    if (head >= tail) {
        return head - tail;
    } else {
        return BUFFER_SIZE - tail + head;
    }
}

int ringbuf_free_space(void) {
    return BUFFER_SIZE - ringbuf_available();
}
