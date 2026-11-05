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

int decode_packet(const uint8_t *stream, int stream_len, uint8_t *out_payload, int *out_type) {
    int i;
    for (i = 0; i < stream_len; i++) {
        if (stream[i] == 0xAA) {
            if (i + 3 < stream_len && stream[i + 1] == 0 && stream[i + 2] == 0 && stream[i + 3] == 0xAA) {
                int packet_len = stream[i + 3];
                if (i + 3 + packet_len < stream_len) {
                    if (stream[i + 3 + packet_len] == stream[i + 3] ^ 0xFF) {
                        if (ringbuf_push(stream[i + 3])) {
                            return -1;
                        }
                        for (int j = 0; j < packet_len; j++) {
                            if (ringbuf_push(stream[i + 3 + j])) {
                                return -1;
                            }
                        }
                        *out_payload = (uint8_t *)malloc(packet_len);
                        if (*out_payload == NULL) {
                            return -1;
                        }
                        for (int j = 0; j < packet_len; j++) {
                            *out_payload++ = ringbuf_pop();
                        }
                        *out_type = stream[i + 1];
                        return packet_len + 3;
                    }
                }
            }
        }
    }
    return -1;
}
