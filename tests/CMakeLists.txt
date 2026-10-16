set(vulkan_headers "${PROJECT_SOURCE_DIR}/external/Vulkan-Headers/include")
if(NOT EXISTS "${vulkan_headers}/vulkan/vulkan.h")
    message(FATAL_ERROR "Initialize Vulkan-Headers with \"git submodule update --init\"")
endif()

set(CMAKE_C_EXTENSIONS OFF)

foreach(test IN ITEMS vk_init_test vk_init_platform_test vk_init_usage_test)
    add_executable(${test} ${test}.c)
    target_include_directories(${test} SYSTEM PRIVATE ${vulkan_headers})
    target_link_libraries(${test} vulkan_initializers)
    target_compile_options(${test} PRIVATE -Wall -Wextra -Werror -pedantic-errors)
    add_test(NAME ${test} COMMAND ${test})
endforeach()
