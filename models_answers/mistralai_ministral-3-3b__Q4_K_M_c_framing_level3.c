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
static bool validate_packet(const uint8_t *stream, int pos, size_t len, uint8_t **out_payload, int *out_type) {
    if (len < 4 || stream[pos] != 0xAA) return false;

    uint8_t type = stream[pos + 1];
    uint8_t payload_len = stream[pos + 2];

    // Check for valid length
    if (payload_len > len - pos - 3) return false;

    // Calculate expected checksum
    uint8_t calculated_checksum = 0;
    for (int i = pos + 3; i < pos + 3 + payload_len; ++i) {
        calculated_checksum ^= stream[i];
    }

    // Verify checksum
    if ((payload_len == 0 && stream[pos + 3] != 0) ||
        (payload_len > 0 && stream[pos + 3 + payload_len] != calculated_checksum)) {
        return false;
    }

    *out_payload = &stream[pos + 3];
    *out_type = type;
    return true;
}

void feed_bytes(const uint8_t *data, int len) {
    for (int i = 0; i < len && ringbuf_free_space() > 0; ++i) {
        if (ringbuf_push(data[i])) {
            break; // Buffer full
        }
    }
}

static bool is_valid_candidate(const uint8_t *stream, size_t pos) {
    return stream[pos] == 0xAA;
}

int get_next_packet(uint8_t *out_payload, int *out_type) {
    if (!ringbuf_available()) return -1;

    // Skip noise until next candidate
    while (ringbuf_available() > 0 && !is_valid_candidate(buffer + tail, ringbuf_pop())) {}

    size_t pos = tail;
    uint8_t *stream_ptr = buffer + pos;
    int remaining_len = ringbuf_available();

    if (!is_valid_candidate(stream_ptr, pos)) {
        return -1; // No valid candidate found
    }

    while (ringbuf_available() > 0) {
        size_t current_pos = tail;
        uint8_t *current_stream = buffer + current_pos;

        if (validate_packet(current_stream, current_pos, remaining_len,
                           &out_payload, out_type)) {
            // Packet is valid; copy payload and advance read position
            int payload_len = *out_type;
            for (int i = 0; i < payload_len; ++i) {
                if (!out_payload || i >= sizeof(out_payload)/sizeof(*out_payload)) break;
                out_payload[i] = ringbuf_pop();
            }
            return payload_len;
        }

        // Move to next byte
        current_pos++;
        remaining_len--;
    }

    return -1; // No valid packet found in buffer
}
