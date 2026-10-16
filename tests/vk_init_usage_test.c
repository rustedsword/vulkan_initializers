#include "vk_init.h"

static const VkApplicationInfo *const file_scope_info = &xVkApplicationInfo(
    .pApplicationName = "vk-init-usage-test",
    .apiVersion = VK_API_VERSION_1_0,
);

static int check_file_scope(void)
{
    return file_scope_info->sType != VK_STRUCTURE_TYPE_APPLICATION_INFO
        || file_scope_info->apiVersion != VK_API_VERSION_1_0;
}

static int check_braced_arguments(void)
{
    const VkImageCreateInfo info = xVkImageCreateInfo(.extent = {16, 8, 1}, .mipLevels = 1);
    return info.sType != VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO
        || info.extent.width != 16 || info.extent.height != 8 || info.extent.depth != 1
        || info.mipLevels != 1;
}

static int check_zeroed_members(void)
{
    const VkBufferCreateInfo info = xVkBufferCreateInfo(.size = 64);
    return info.pNext != nullptr || info.flags != 0 || info.usage != 0 || info.size != 64;
}

static int check_pnext_chain(void)
{
    const VkPhysicalDeviceFeatures2 features = xVkPhysicalDeviceFeatures2(
        .pNext = &xVkPhysicalDeviceVulkan12Features(.timelineSemaphore = VK_TRUE),
    );
    const VkPhysicalDeviceVulkan12Features *next = features.pNext;
    return features.sType != VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_FEATURES_2
        || next->sType != VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_2_FEATURES
        || next->timelineSemaphore != VK_TRUE;
}

static int check_array(void)
{
    const VkWriteDescriptorSet writes[] = {
        xVkWriteDescriptorSet(.dstBinding = 0),
        xVkWriteDescriptorSet(.dstBinding = 1),
    };
    return writes[1].sType != VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET || writes[1].dstBinding != 1;
}

int main(void)
{
    return check_file_scope() || check_braced_arguments() || check_zeroed_members()
        || check_pnext_chain() || check_array();
}
