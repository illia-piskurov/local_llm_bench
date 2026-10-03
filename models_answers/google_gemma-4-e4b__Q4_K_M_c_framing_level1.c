#include <stdint.h>
#include <stddef.h> // For size_t if needed, but uint8_t array handles it fine

// Define the fixed buffer size
#define BUFFER_SIZE 512

// Static memory storage for the ring buffer
static uint8_t ringbuf_buffer[BUFFER_SIZE];

// Indices tracking the read (tail) and write (head) positions
static size_t head = 0; // Where the next byte will be written
static size_t tail = 0; // Where the next byte will be read from

// Current number of elements stored in the buffer
static int count = 0;

/**
 * @brief Initializes or resets the ring buffer.
 */
void ringbuf_init(void) {
    head = 0;
    tail = 0;
    count = 0;
}

/**
 * @brief Pushes one byte into the buffer.
 * 
 * @param byte The byte to push.
 * @return int 0 on success, -1 if the buffer is full.
 */
int ringbuf_push(uint8_t byte) {
    if (count >= BUFFER_SIZE) {
        // Buffer is full
        return -1;
    }

    // Write the byte at the current head position
    ringbuf_buffer[head] = byte;

    // Advance the head pointer, wrapping around if necessary
    head = (head + 1) % BUFFER_SIZE;

    // Increment count
    count++;
    return 0;
}

/**
 * @brief Pops one byte from the buffer following FIFO ordering.
 * 
 * @return int The popped byte value (0-255) on success, or -1 if the buffer is empty.
 */
int ringbuf_pop(void) {
    if (count == 0) {
        // Buffer is empty
        return -1;
    }

    // Read the byte from the current tail position
    uint8_t byte = ringbuf_buffer[tail];

    // Advance the tail pointer, wrapping around if necessary
    tail = (tail + 1) % BUFFER_SIZE;

    // Decrement count
    count--;
    
    return (int)byte;
}

/**
 * @brief Returns the current number of bytes stored in the buffer.
 * 
 * @return int The available count (0 to 512).
 */
int ringbuf_available(void) {
    return count;
}

/**
 * @brief Returns remaining free space in the buffer.
 * 
 * @return int Remaining free space (BUFFER_SIZE - available).
 */
int ringbuf_free_space(void) {
    return BUFFER_SIZE - count;
}
