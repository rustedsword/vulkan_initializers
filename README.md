# vulkan_initializers
Header-only C23 macros that create Vulkan structs with `sType` already set, one for every struct in the Vulkan registry that has an `sType`.

```c
#include <vk_init.h>

VkPhysicalDeviceVulkan12Features vk12 = xVkPhysicalDeviceVulkan12Features(.timelineSemaphore = VK_TRUE);

vkCreateDevice(gpu, &xVkDeviceCreateInfo(
    .pNext = &xVkPhysicalDeviceFeatures2(.pNext = &vk12),
    .queueCreateInfoCount = 1,
    .pQueueCreateInfos = &xVkDeviceQueueCreateInfo(
        .queueFamilyIndex = family, .queueCount = 1, .pQueuePriorities = &(float){1.0f}),
), nullptr, &device);
```

`xVkFoo(...)` expands to `((VkFoo){ .sType = VK_STRUCTURE_TYPE_FOO, ... })`: a compound literal that can be stored, passed by address or chained through `pNext`. Members that are not mentioned are zeroed.

Each macro is defined only when the Vulkan version or extension that provides its struct is available. As with `vulkan.h`, define `VK_USE_PLATFORM_*` or `VK_ENABLE_BETA_EXTENSIONS` before including `vk_init.h` to get the platform and beta structs.

## Requirements
C23 and Vulkan headers.

## Usage
Copy `include/vk_init.h` or use one of the packages below. They only provide the include path, so add your usual Vulkan dependency too.

CMake:
```cmake
find_package(vulkan_initializers REQUIRED)  # or add_subdirectory(vulkan_initializers)
target_link_libraries(app PRIVATE vulkan_initializers Vulkan::Vulkan)
```

Meson, installed or as a subproject:
```meson
vulkan_initializers = dependency('vulkan_initializers',
  fallback: ['vulkan_initializers', 'vulkan_initializers_dep'])
```

pkg-config: `vulkan_initializers`.

## Regenerating
`include/vk_init.h`, `tests/vk_init_test.c` and `VERSION` are generated from the registry of the `external/Vulkan-Headers` submodule, and the package version is that Vulkan-Headers version. To update:
```
git -C external/Vulkan-Headers fetch --depth 1 origin tag v1.4.366
git -C external/Vulkan-Headers checkout v1.4.366
scripts/gen_vk_init.py
```
The generated test is compiled with `$CC` against the submodule headers before anything is written. `--check` fails if the files are out of date, and `--registry` selects another `vk.xml`.

## Tests
The tests are built against the submodule headers, so run `git submodule update --init` first.
```
cmake -B build -DVULKAN_INITIALIZERS_TEST=ON && cmake --build build && ctest --test-dir build
meson setup build -Dtests=true && meson test -C build
```
`vk_init_test` instantiates every macro that the Vulkan headers allow, `vk_init_platform_test` also enables beta extensions and every platform whose headers are installed.
