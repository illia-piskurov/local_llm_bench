#include <stdint.h>

#define BUFFER_SIZE 512

static uint8_t buffer[BUFFER_SIZE];
static int head = BUFFER_SIZE;
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

void feed_bytes(const uint8_t *data, int len) {
    for (int i = 0; i < len; i++) {
        if (ringbuf_free_space() >= len - i) {
            for (int j = 0; j < len - i; j++) {
                ringbuf_push(data[i + j]);
            }
        } else {
            return;
        }
    }
}

int get_next_packet(uint8_t *out_payload, int *out_type) {
    while (ringbuf_available() >= 3) {
        if (ringbuf_pop() == 0xAA && ringbuf_pop() == *out_type && ringbuf_pop() + 3 == *out_payload) {
            int packet_len = ringbuf_pop() + 3;
            for (int i = 0; i < packet_len; i++) {
                if (ringbuf_pop() != *out_payload++) {
                    return -1;
                }
            }
            return packet_len;
        }
    }
    return -1;
}
