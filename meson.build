project(
  'vulkan_initializers',
  version: files('VERSION'),
  license: 'MIT',
  meson_version: '>= 0.57.0',
)

install_headers('include/vk_init.h')

vulkan_initializers_dep = declare_dependency(
  include_directories: include_directories('include'),
)
meson.override_dependency('vulkan_initializers', vulkan_initializers_dep)
if meson.is_cross_build()
  meson.override_dependency('vulkan_initializers', vulkan_initializers_dep, native: true)
endif

import('pkgconfig').generate(
  name: 'vulkan_initializers',
  description: 'C23 macros that initialize Vulkan structs with their sType',
  install_dir: get_option('datadir') / 'pkgconfig',
)

if get_option('tests')
  subdir('tests')
endif
