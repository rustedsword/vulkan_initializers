add_languages('c', native: false)
if not import('fs').is_file('../external/Vulkan-Headers/include/vulkan/vulkan.h')
  error('Initialize Vulkan-Headers with "git submodule update --init"')
endif
vulkan_headers = declare_dependency(
  include_directories: include_directories('../external/Vulkan-Headers/include', is_system: true),
)

foreach name : ['vk_init_test', 'vk_init_platform_test', 'vk_init_usage_test']
  test(name, executable(name, name + '.c',
    dependencies: [vulkan_initializers_dep, vulkan_headers],
    override_options: ['c_std=c23', 'warning_level=3', 'werror=true'],
  ))
endforeach
