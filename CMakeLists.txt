cmake_minimum_required(VERSION 3.21...3.31)

if(TARGET vulkan_initializers)
    message("Project already exist")
    return()
endif()

project(vulkan_initializers
    VERSION 0.1.0
    DESCRIPTION "C23 macros that initialize Vulkan structs with their sType"
    LANGUAGES C)
include(GNUInstallDirs)
include(CMakePackageConfigHelpers)

add_library(vulkan_initializers INTERFACE)

target_compile_features(vulkan_initializers INTERFACE c_std_23)

target_include_directories(vulkan_initializers INTERFACE
    $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
)

if(VULKAN_INITIALIZERS_TEST)
    include(CTest)
    add_subdirectory(tests)
endif()

install(TARGETS vulkan_initializers EXPORT vulkan_initializers-config)

export(TARGETS vulkan_initializers
    FILE "${CMAKE_CURRENT_BINARY_DIR}/vulkan_initializers-config.cmake"
    )

install(EXPORT vulkan_initializers-config
    DESTINATION "${CMAKE_INSTALL_DATADIR}/cmake/${PROJECT_NAME}"
    )

write_basic_package_version_file("${CMAKE_CURRENT_BINARY_DIR}/vulkan_initializers-config-version.cmake"
    COMPATIBILITY SameMinorVersion
    ARCH_INDEPENDENT
    )

install(FILES "${CMAKE_CURRENT_BINARY_DIR}/vulkan_initializers-config-version.cmake"
    DESTINATION "${CMAKE_INSTALL_DATADIR}/cmake/${PROJECT_NAME}"
    )

set(pc_includedir "\${prefix}")
cmake_path(APPEND pc_includedir "${CMAKE_INSTALL_INCLUDEDIR}")
file(CONFIGURE OUTPUT vulkan_initializers.pc.in CONTENT [[
includedir=@pc_includedir@

Name: @PROJECT_NAME@
Description: @PROJECT_DESCRIPTION@
Version: @PROJECT_VERSION@
Cflags: -I"${includedir}"
]] @ONLY)

# The prefix is added at install time so that cmake --install --prefix is honored
install(CODE [[
    file(READ "${CMAKE_CURRENT_LIST_DIR}/vulkan_initializers.pc.in" pc)
    file(WRITE "${CMAKE_CURRENT_LIST_DIR}/vulkan_initializers.pc" "prefix=${CMAKE_INSTALL_PREFIX}\n${pc}")
]])

install(FILES "${CMAKE_CURRENT_BINARY_DIR}/vulkan_initializers.pc"
    DESTINATION "${CMAKE_INSTALL_DATADIR}/pkgconfig"
    )

install(FILES include/vk_init.h DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
