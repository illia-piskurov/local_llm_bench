#include <stdint.h>

#define BUFFER_SIZE 512

static uint8_t buffer[BUFFER_SIZE];
static volatile int head = 0;
static volatile int tail = 0;

void ringbuf_init(void) {
    head = 0;
    tail = 0;
}

int ringbuf_push(uint8_t byte) {
    if ((tail + 1) % BUFFER_SIZE == head) {
        return -1; // Buffer is full
    }
    buffer[tail] = byte;
    tail = (tail + 1) % BUFFER_SIZE;
    return 0;
}

int ringbuf_pop(void) {
    if (head == tail) {
        return -1; // Buffer is empty
    }
    uint8_t byte = buffer[head];
    head = (head + 1) % BUFFER_SIZE;
    return byte;
}

int ringbuf_available(void) {
    return (tail - head + BUFFER_SIZE) % BUFFER_SIZE;
}

int ringbuf_free_space(void) {
    return BUFFER_SIZE - ringbuf_available();
}

int decode_packet(const uint8_t *stream, int stream_len, uint8_t *out_payload, int *out_type) {
    if (!stream || !out_payload || !out_type || stream_len < 4)
        return -1;

    const uint8_t *ptr = stream;
    while (ptr <= stream + stream_len - 4) {
        if (*ptr != 0xAA) {
            ptr++;
            continue;
        }

        int type = *(ptr + 1);
        int len = *(ptr + 2);

        if (len > stream_len - (ptr - stream) - 3)
            return -1;

        uint8_t checksum = 0;
        for (int i = 0; i < len; ++i)
            checksum ^= *(ptr + 3 + i);
        
        if (*(ptr + 3 + len) != checksum)
            ptr++;
        else {
            *out_type = type;
            memcpy(out_payload, ptr + 3, len);
            return len;
        }
    }

    return -1;
}
