#include <stdint.h>
#include <stdbool.h>

#define BUFFER_SIZE 512

static uint8_t buffer[BUFFER_SIZE];
static size_t head = 0;    // Next write position (circular index)
static size_t tail = 0;   // Next read position (circular index)
static bool is_full = false;

// Ring Buffer Functions
void ringbuf_init(void) {
    head = tail = 0;
    is_full = false;
}

int ringbuf_push(uint8_t byte) {
    if (is_full || ((head + 1) % BUFFER_SIZE) == tail) {
        return -1; // Buffer full
    }
    buffer[head] = byte;
    head = (head + 1) % BUFFER_SIZE;

    is_full = (tail == head && !is_full);
    return 0;
}

int ringbuf_pop(void) {
    if (head == tail && !is_full) {
        return -1; // Buffer empty
    }
    uint8_t byte = buffer[tail];
    tail = (tail + 1) % BUFFER_SIZE;

    is_full = (head != tail);
    return byte;
}

int ringbuf_available(void) {
    size_t available = (tail > head) ? (BUFFER_SIZE - tail + head) : (head - tail);
    return available;
}

int ringbuf_free_space(void) {
    return BUFFER_SIZE - ringbuf_available();
}

// Packet Decoder
static bool validate_packet(const uint8_t *stream, int len, uint8_t **out_payload, int *out_type) {
    if (len < 4 || stream[0] != 0xAA) return false;

    uint8_t type = stream[1];
    uint8_t payload_len = stream[2];

    // Check for valid length
    if (payload_len > len - 3) return false;

    // Calculate expected checksum
    uint8_t calculated_checksum = 0;
    for (int i = 3; i < 3 + payload_len; ++i) {
        calculated_checksum ^= stream[i];
    }

    // Verify checksum
    if ((payload_len == 0 && stream[3] != 0) ||
        (payload_len > 0 && stream[3 + payload_len] != calculated_checksum)) {
        return false;
    }

    *out_payload = &stream[3];
    *out_type = type;
    return true;
}

int decode_packet(const uint8_t *stream, int stream_len, uint8_t *out_payload, int *out_type) {
    if (stream_len < 4 || !ringbuf_available()) return -1;

    // Scan for first valid packet
    size_t pos = 0;
    while (pos < stream_len) {
        if (stream[pos] == 0xAA && ringbuf_push(stream[pos])) {
            pos++;
            int remaining = stream_len - pos;

            // Try to read complete packet
            uint8_t *payload = NULL;
            int type = -1;
            bool valid = false;

            while (ringbuf_available() > 0 && pos < stream_len) {
                if (validate_packet(stream + pos, remaining, &payload, &type)) {
                    // Copy payload to output buffer
                    for (int i = 0; i < type; ++i) {
                        if (!out_payload || i >= sizeof(out_payload)/sizeof(*out_payload)) break;
                        out_payload[i] = ringbuf_pop();
                    }
                    *out_type = type;
                    return type;
                }

                // Skip invalid bytes
                uint8_t byte = stream[pos];
                pos++;
                remaining--;
            }

            // If we didn't find a valid packet, try again with next byte
        } else {
            pos++;  // Skip invalid write attempts
        }
    }

    return -1;
}
