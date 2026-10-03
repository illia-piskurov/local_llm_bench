#include <stdint.h>

#define BUFFER_SIZE 512

static uint8_t buffer[BUFFER_SIZE];
static size_t head = 0;
static size_t tail = 0;

void ringbuf_init(void) {
    head = 0;
    tail = 0;
}

int ringbuf_push(uint8_t byte) {
    if ((head + 1) % BUFFER_SIZE == tail) {
        return -1; // Buffer is full
    }
    buffer[head] = byte;
    head = (head + 1) % BUFFER_SIZE;
    return 0;
}

int ringbuf_pop(void) {
    if (tail == head) {
        return -1; // Buffer is empty
    }
    uint8_t byte = buffer[tail];
    tail = (tail + 1) % BUFFER_SIZE;
    return byte;
}

int ringbuf_available(void) {
    return (head - tail + BUFFER_SIZE) % BUFFER_SIZE;
}

int ringbuf_free_space(void) {
    return BUFFER_SIZE - ringbuf_available();
}

#include <stdint.h>

#define MAGIC_BYTE 0xAA

int decode_packet(const uint8_t *stream, int stream_len, uint8_t *out_payload, int *out_type) {
    size_t i = 0;
    while (i + 4 <= stream_len) {
        if (stream[i] == MAGIC_BYTE && ringbuf_available() >= (size_t)(3 + stream[i+1] + 1)) {
            uint8_t payload_length = stream[i+1];
            uint8_t checksum = stream[i+2 + payload_length];

            // Verify checksum
            uint8_t calculated_checksum = 0;
            for (int j = i + 2; j < i + 2 + payload_length; ++j) {
                calculated_checksum ^= stream[j];
            }
            if (calculated_checksum != checksum) {
                i += payload_length + 4;
                continue;
            }

            // Valid packet found, copy payload
            for (int j = 0; j < payload_length; ++j) {
                out_payload[j] = stream[i+2+j];
            }
            *out_type = stream[i+1];
            return payload_length;
        } else {
            i++;
        }
    }
    return -1; // No valid packet found
}
