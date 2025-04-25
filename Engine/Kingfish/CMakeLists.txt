cmake_minimum_required(VERSION 3.26)
project(kingfish)

# #
# kingfish version numbers
# #
set(KINGFISH_VERSION_MAJOR "1")
set(KINGFISH_VERSION_MINOR "2")
set(KINGFISH_VERSION_PATCH "0")

message("Kingfish version is set to ${KINGFISH_VERSION_MAJOR}.${KINGFISH_VERSION_MINOR}.${KINGFISH_VERSION_PATCH}")

# #
# Executable name
# #
set(KINGFISH_OUT_NAME "kingfish_${KINGFISH_VERSION_MAJOR}.${KINGFISH_VERSION_MINOR}.${KINGFISH_VERSION_PATCH}")

# #
# Project settings
# #
set(CMAKE_CXX_STANDARD 23)

# #
# Source code
# #
add_executable(kingfish
    src/kingfish/main.cpp
    src/kingfish/uci.cpp
    src/kingfish/piece.cpp

    src/kingfish/ai/searcher.cpp
    src/kingfish/ai/timemanager.cpp

    src/kingfish/bitboard.cpp
    src/kingfish/position.cpp

    src/kingfish/zobrist.cpp
)

# #
# Compilation settings
# #
set_target_properties(kingfish PROPERTIES OUTPUT_NAME ${KINGFISH_OUT_NAME})

# #
# Add external dependencies
# #
if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    # Sửa: Loại bỏ -static-libstdc++ và -static-libgcc, thêm -shared-libgcc
    set(CMAKE_CXX_FLAGS "-pthread -O3 -Wall -Wextra -shared-libgcc")
    target_link_libraries(kingfish PUBLIC stdc++)
elseif(CMAKE_CXX_COMPILER_ID STREQUAL "Clang")
    set(CMAKE_CXX_FLAGS "-pthread -O3 -Wall -Wextra -shared-libgcc")
    target_link_libraries(kingfish PUBLIC stdc++)
endif()

# Đảm bảo liên kết động với libstdc++ và libgcc
set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -shared-libgcc")