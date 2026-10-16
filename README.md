# vulkan_initializers
Header-only C23 macros that create Vulkan structs with `sType` already set.

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

`xVkFoo(...)` expands to a compound literal: `((VkFoo){ .sType = VK_STRUCTURE_TYPE_FOO, ... })`

Each macro is defined only when the Vulkan version or extension that provides its struct is available.
As with `vulkan.h`, define `VK_USE_PLATFORM_*` or `VK_ENABLE_BETA_EXTENSIONS` before including `vk_init.h` to get the platform and beta structs.

## Requirements
C23 and Vulkan headers.

## Usage
Copy `include/vk_init.h` or use one of the packages below.

CMake:
```cmake
find_package(Vulkan REQUIRED)
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
```
git -C external/Vulkan-Headers fetch --depth 1 origin tag v1.4.366
git -C external/Vulkan-Headers checkout v1.4.366
scripts/gen_vk_init.py
```
