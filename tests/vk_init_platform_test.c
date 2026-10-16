#define VK_ENABLE_BETA_EXTENSIONS
#define VK_USE_PLATFORM_ANDROID_KHR
#define VK_USE_PLATFORM_IOS_MVK
#define VK_USE_PLATFORM_MACOS_MVK
#define VK_USE_PLATFORM_METAL_EXT
#define VK_USE_PLATFORM_OHOS
#define VK_USE_PLATFORM_UBM_SEC
#define VK_USE_PLATFORM_VI_NN
#define VK_USE_PLATFORM_WAYLAND_KHR

#if __has_include(<windows.h>)
#define VK_USE_PLATFORM_WIN32_KHR
#endif
#if __has_include(<xcb/xcb.h>)
#define VK_USE_PLATFORM_XCB_KHR
#endif
#if __has_include(<X11/Xlib.h>)
#define VK_USE_PLATFORM_XLIB_KHR
#endif
#if __has_include(<X11/Xlib.h>) && __has_include(<X11/extensions/Xrandr.h>)
#define VK_USE_PLATFORM_XLIB_XRANDR_EXT
#endif
#if __has_include(<directfb.h>)
#define VK_USE_PLATFORM_DIRECTFB_EXT
#endif
#if __has_include(<zircon/types.h>)
#define VK_USE_PLATFORM_FUCHSIA
#endif
#if __has_include(<ggp_c/vulkan_types.h>)
#define VK_USE_PLATFORM_GGP
#endif
#if __has_include(<screen/screen.h>)
#define VK_USE_PLATFORM_SCREEN_QNX
#endif
#if __has_include(<nvscisync.h>) && __has_include(<nvscibuf.h>)
#define VK_USE_PLATFORM_SCI
#endif

#include "vk_init_test.c"
