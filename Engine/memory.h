#ifndef MEMORY_H
#define MEMORY_H

#include <cstdint>

class Memory {
public:
    static void* allocate(size_t size);
    static void deallocate(void* ptr);
};

#endif