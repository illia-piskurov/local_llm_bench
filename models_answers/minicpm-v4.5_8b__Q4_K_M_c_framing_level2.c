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

int decode_packet(const uint8_t *stream, int stream_len, uint8_t *out_payload, int *out_type) {
    uint8_t magic = 0xAA;
    int offset = 0;
    while (offset < stream_len) {
        if (stream[offset] != magic) {
            offset++;
            continue;
        }
        offset++;
        if (offset + 3 >= stream_len) return -1;
        uint8_t type = stream[offset];
        offset++;
        if (type > 255) return -1;
        uint8_t len = stream[offset];
        offset++;
        if (len > 255) return -1;
        if (offset + len >= stream_len) return -1;
        uint8_t checksum = 0;
        for (int i = 0; i < len; i++) {
            checksum ^= stream[offset + i];
        }
        offset += len;
        if (stream[offset] != checksum) return -1;
        offset++;
        if (offset < stream_len) {
            if (stream[offset] != magic) return -1;
            offset++;
        }
        if (out_payload != NULL) {
            for (int i = 0; i < len; i++) {
                out_payload[i] = stream[offset + i];
            }
        }
        *out_type = type;
        return len;
    }
    return -1;
}
