#include "memory.h"
#include <cstdlib>

void* Memory::allocate(size_t size) {
    return std::malloc(size);
}

void Memory::deallocate(void* ptr) {
    std::free(ptr);
}