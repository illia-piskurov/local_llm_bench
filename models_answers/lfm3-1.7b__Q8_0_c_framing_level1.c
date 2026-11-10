#include <stdint.h>

#define BUFFER_SIZE 512

static uint8_t buffer[BUFFER_SIZE];
static unsigned int front = 0;
static unsigned int rear = 0;
static unsigned int count = 0;

void ringbuf_init(void) {
    // Initial state: empty
    front = 0;
    rear = 0;
    count = 0;
}

int ringbuf_push(uint8_t byte) {
    if (count == BUFFER_SIZE) {
        return -1; // buffer is full
    }
    buffer[rear] = byte;
    rear = (rear + 1) % BUFFER_SIZE;
    ++count;
    return 0;
}

int ringbuf_pop(void) {
    if (count == 0) {
        return -1; // buffer empty
    }
    int val = buffer[front];
    front = (front + 1) % BUFFER_SIZE;
    --count;
    return (int)val;
}

int ringbuf_available(void) {
    return count;
}

int ringbuf_free_space(void) {
    return BUFFER_SIZE - count;
}
