add_languages('c', native: false)
vulkan_dep = dependency('vulkan').partial_dependency(compile_args: true, includes: true)

foreach name : ['vk_init_test', 'vk_init_platform_test', 'vk_init_usage_test']
  test(name, executable(name, name + '.c',
    dependencies: [vulkan_initializers_dep, vulkan_dep],
    override_options: ['c_std=c23', 'warning_level=3', 'werror=true'],
  ))
endforeach
