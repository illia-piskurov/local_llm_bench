#include <stdint.h>
#include <stdbool.h>
#include <string.h>

#define BUFFER_SIZE 512

// Fixed-size ring buffer implementation
typedef struct {
    uint8_t buffer[BUFFER_SIZE];
    int head;
    int tail;
    int count;
} ringbuf_t;

static ringbuf_t ringbuf;

void ringbuf_init(void) {
    ringbuf.head = 0;
    ringbuf.tail = 0;
    ringbuf.count = 0;
}

int ringbuf_push(uint8_t byte) {
    if (ringbuf.count == BUFFER_SIZE) {
        return -1; // Buffer full
    }

    ringbuf.buffer[ringbuf.tail] = byte;
    ringbuf.tail = (ringbuf.tail + 1) % BUFFER_SIZE;
    ringbuf.count++;
    return 0;
}

int ringbuf_pop(void) {
    if (ringbuf.count == 0) {
        return -1; // Buffer empty
    }

    uint8_t byte = ringbuf.buffer[ringbuf.head];
    ringbuf.head = (ringbuf.head + 1) % BUFFER_SIZE;
    ringbuf.count--;
    return byte;
}

int ringbuf_available(void) {
    return ringbuf.count;
}

int ringbuf_free_space(void) {
    return BUFFER_SIZE - ringbuf.count;
}

// Binary packet decoder
int decode_packet(const uint8_t *stream, int stream_len, uint8_t *out_payload, int *out_type) {
    if (stream == NULL || stream_len <= 0 || out_payload == NULL || out_type == NULL) {
        return -1;
    }

    int i = 0;
    while (i < stream_len) {
        if (stream[i] == 0xAA) {
            int len = stream[i + 1];
            if (len > 0 && len <= stream_len - i - 2) {
                uint8_t checksum = 0;
                if (len > 0) {
                    for (int j = 0; j < len; j++) {
                        checksum ^= stream[i + j + 1];
                    }
                }

                if (checksum == stream[i + len + 1]) {
                    int payload_len = len;
                    if (payload_len > 0) {
                        memcpy(out_payload, stream + i + 2, payload_len);
                    }
                    *out_type = stream[i + 1];
                    return payload_len;
                }
            }
        }
        i++;
    }

    return -1;
}
