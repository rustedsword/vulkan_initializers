find_package(Vulkan REQUIRED)

set(CMAKE_C_EXTENSIONS OFF)

foreach(test IN ITEMS vk_init_test vk_init_platform_test vk_init_usage_test)
    add_executable(${test} ${test}.c)
    target_link_libraries(${test} vulkan_initializers Vulkan::Headers)
    target_compile_options(${test} PRIVATE -Wall -Wextra -Werror -pedantic-errors)
    add_test(NAME ${test} COMMAND ${test})
endforeach()
