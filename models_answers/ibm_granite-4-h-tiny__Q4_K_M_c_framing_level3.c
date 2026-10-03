#include <stdint.h>

#define BUFFER_SIZE 512

static uint8_t buffer[BUFFER_SIZE];
static size_t head = 0;
static size_t tail = 0;

void ringbuf_init(void) {
    head = 0;
    tail = 0;
}

int ringbuf_push(const uint8_t *data, int len) {
    if ((head + len) % BUFFER_SIZE >= tail) {
        // Buffer can hold all data
        for (int i = 0; i < len; ++i) {
            buffer[head] = data[i];
            head = (head + 1) % BUFFER_SIZE;
        }
        return len;
    } else {
        // Buffer overflow, discard excess bytes
        int to_copy = BUFFER_SIZE - tail;
        for (int i = 0; i < to_copy && i < len; ++i) {
            buffer[head] = data[i];
            head = (head + 1) % BUFFER_SIZE;
        }
        return to_copy; // Return number of bytes actually copied
    }
}

int ringbuf_pop(uint8_t *data, int len) {
    if (tail == head) {
        return -1; // Buffer is empty
    }
    int to_copy = len < (head - tail ? len : (head - tail));
    for (int i = 0; i < to_copy; ++i) {
        data[i] = buffer[tail];
        tail = (tail + 1) % BUFFER_SIZE;
    }
    return to_copy;
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

void feed_bytes(const uint8_t *data, int len) {
    int copied = ringbuf_push(data, len);
    if (copied < len) {
        // Discard remaining bytes that didn't fit into the buffer
        for (int i = copied; i < len; ++i) {
            ringbuf_pop();
        }
    }
}

int get_next_packet(uint8_t *out_payload, int *out_type) {
    uint8_t payload[BUFFER_SIZE];
    int len = decode_packet(payload, BUFFER_SIZE, out_payload, out_type);
    if (len >= 0) {
        // Discard the packet from the buffer
        for (int i = 0; i < len + 4; ++i) {
            ringbuf_pop();
        }
    }
    return len;
}
