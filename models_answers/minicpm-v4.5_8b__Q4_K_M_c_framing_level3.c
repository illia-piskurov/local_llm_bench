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

void feed_bytes(const uint8_t *data, int len) {
    int free = ringbuf_free_space();
    if (len > free) len = free;
    for (int i = 0; i < len; i++) {
        int res = ringbuf_push(data[i]);
        if (res == -1) break;
    }
}

int get_next_packet(uint8_t *out_payload, int *out_type) {
    uint8_t magic = 0xAA;
    while (ringbuf_available() > 0) {
        int offset = 0;
        while (offset < ringbuf_available()) {
            uint8_t byte = ringbuf_pop();
            if (byte != magic) {
                continue;
            }
            offset++;
            if (offset + 3 >= ringbuf_available()) return -1;
            uint8_t type = ringbuf_pop();
            offset++;
            if (type > 255) return -1;
            uint8_t len = ringbuf_pop();
            offset++;
            if (len > 255) return -1;
            if (offset + len >= ringbuf_available()) return -1;
            uint8_t checksum = 0;
            for (int i = 0; i < len; i++) {
                checksum ^= ringbuf_pop();
            }
            offset += len;
            if (ringbuf_pop() != checksum) return -1;
            offset++;
            if (offset < ringbuf_available()) {
                if (ringbuf_pop() != magic) return -1;
                offset++;
            }
            if (out_payload != NULL) {
                for (int i = 0; i < len; i++) {
                    out_payload[i] = ringbuf_pop();
                }
            }
            *out_type = type;
            return len;
        }
    }
    return -1;
}
