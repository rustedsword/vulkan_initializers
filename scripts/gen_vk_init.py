#!/usr/bin/env python3

"""Generate and compile-test C23 initializers for Vulkan tagged structs."""

from __future__ import annotations

import argparse
import os
import re
import shlex
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path


API = "vulkan"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = REPO_ROOT / "external/Vulkan-Headers/registry/vk.xml"
DEFAULT_HEADER = REPO_ROOT / "include/vk_init.h"
DEFAULT_TEST = REPO_ROOT / "tests/vk_init_test.c"
DEFAULT_VERSION = REPO_ROOT / "VERSION"


def supports(value: str | None, api: str = API) -> bool:
    return value is None or api in value.split(",")


def type_name(element: ET.Element) -> str | None:
    return element.get("name") or element.findtext("name")


def registry_header_version(root: ET.Element) -> str:
    defines = {
        type_name(element): "".join(element.itertext())
        for element in root.findall('./types/type[@category="define"]')
        if supports(element.get("api"))
    }
    patch = re.search(r"#define\s+VK_HEADER_VERSION\s+(\d+)", defines.get("VK_HEADER_VERSION", ""))
    complete = re.search(
        r"VK_MAKE_API_VERSION\(\s*\d+\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*VK_HEADER_VERSION\s*\)",
        defines.get("VK_HEADER_VERSION_COMPLETE", ""),
    )
    if patch is None or complete is None:
        return "unknown"
    return f"{complete.group(1)}.{complete.group(2)}.{patch.group(1)}"


def requirements(root: ET.Element) -> Iterator[tuple[str, ET.Element]]:
    for feature in root.findall("./feature"):
        if not supports(feature.get("api")):
            continue
        version = feature.get("number")
        if version is None:
            raise ValueError(f"feature {feature.get('name')} has no version number")
        provider = f"VK_VERSION_{version.replace('.', '_')}"
        for requirement in feature.findall("require"):
            if supports(requirement.get("api")):
                yield provider, requirement

    for extension in root.findall("./extensions/extension"):
        if not supports(extension.get("supported")):
            continue
        provider = extension.get("name")
        if provider is None:
            raise ValueError("extension has no name")
        for requirement in extension.findall("require"):
            if supports(requirement.get("api")):
                yield provider, requirement


def providers(root: ET.Element) -> dict[str, set[str]]:
    result: defaultdict[str, set[str]] = defaultdict(set)
    for provider, requirement in requirements(root):
        for element in requirement.findall("type"):
            if name := element.get("name"):
                result[name].add(provider)
    return result


def stype_aliases(root: ET.Element) -> tuple[dict[str, str], dict[str, set[str]]]:
    targets: dict[str, str] = {}
    nearby: defaultdict[str, set[str]] = defaultdict(set)
    for _, requirement in requirements(root):
        enums = {
            name: alias
            for element in requirement.findall("enum")
            if element.get("extends") == "VkStructureType"
            and (name := element.get("name"))
            and (alias := element.get("alias"))
        }
        targets.update(enums)
        for element in requirement.findall("type"):
            if name := element.get("name"):
                nearby[name].update(enums)
    return targets, nearby


def tagged_structs(root: ET.Element) -> dict[tuple[str, ...], list[tuple[str, str]]]:
    structs: dict[str, ET.Element] = {}
    for element in root.findall('./types/type[@category="struct"]'):
        if not supports(element.get("api")):
            continue
        name = type_name(element)
        if name is None:
            raise ValueError("struct has no name")
        structs[name] = element

    tags: dict[str, str | None] = {}

    def resolve_tag(name: str, resolving: set[str] | None = None) -> str | None:
        if name in tags:
            return tags[name]
        if name not in structs:
            return None
        if resolving is None:
            resolving = set()
        if name in resolving:
            raise ValueError(f"struct alias cycle involving {name}")
        resolving.add(name)

        element = structs[name]
        alias = element.get("alias")
        if alias is not None:
            tag = resolve_tag(alias, resolving)
        else:
            member = next(
                (member for member in element.findall("member") if member.findtext("name") == "sType"),
                None,
            )
            tag = member.get("values") if member is not None else None

        resolving.remove(name)
        tags[name] = tag
        return tag

    targets, nearby = stype_aliases(root)

    def canonical(tag: str) -> str:
        seen: set[str] = set()
        while tag in targets:
            if tag in seen:
                raise ValueError(f"sType alias cycle involving {tag}")
            seen.add(tag)
            tag = targets[tag]
        return tag

    provided_by = providers(root)
    groups: defaultdict[tuple[str, ...], list[tuple[str, str]]] = defaultdict(list)
    for name in structs:
        tag = resolve_tag(name)
        available = provided_by.get(name)
        if tag is None or not available:
            continue
        if structs[name].get("alias") is not None:
            # Headers that predate a promotion only know the sType alias required with the alias.
            own = [alias for alias in nearby.get(name, ()) if canonical(alias) == canonical(tag)]
            if len(own) == 1:
                tag = own[0]
        if "," in tag or not tag.startswith("VK_STRUCTURE_TYPE_"):
            raise ValueError(f"unexpected sType value for {name}: {tag}")
        groups[tuple(sorted(available))].append((name, tag))

    for entries in groups.values():
        entries.sort()
    return dict(groups)


def group_sort_key(providers: tuple[str, ...]) -> tuple[int, tuple[str, ...]]:
    return (0 if providers[0].startswith("VK_VERSION_") else 1, providers)


def condition(providers: tuple[str, ...]) -> str:
    return " || ".join(f"defined({provider})" for provider in providers)


def generated_preamble(source: Path, version: str, details: list[str]) -> list[str]:
    return [
        "/*",
        " * Generated by scripts/gen_vk_init.py; do not edit.",
        f" * Vulkan registry: {source.name}, header version {version}.",
        " *",
        *[f" * {line}" if line else " *" for line in details],
        " */",
        "",
    ]


def generate_header(
    groups: dict[tuple[str, ...], list[tuple[str, str]]], source: Path, version: str
) -> str:
    lines = generated_preamble(
        source,
        version,
        [
            "Each xVkType(...) macro produces a struct value with sType initialized.",
            "It can be stored directly or addressed for a Vulkan call:",
            "",
            "    vkUnmapMemory2(device, &xVkMemoryUnmapInfo(.memory = memory));",
        ],
    )
    lines += [
        "#ifndef VULKAN_INITIALIZERS_VK_INIT_H",
        "#define VULKAN_INITIALIZERS_VK_INIT_H",
        "",
        "#include <vulkan/vulkan.h>",
        "",
        "#if !defined(__STDC_VERSION__) || __STDC_VERSION__ < 202311L",
        '#error "vk_init.h requires C23"',
        "#endif",
        "",
    ]

    for available, entries in sorted(groups.items(), key=lambda item: group_sort_key(item[0])):
        lines.append(f"#if {condition(available)}")
        for name, tag in entries:
            lines += [
                f"#define x{name}(...) \\",
                f"    (({name}) {{ .sType = {tag} __VA_OPT__(,) __VA_ARGS__ }})",
                "",
            ]
        lines += ["#endif", ""]

    lines += ["#endif", ""]
    return "\n".join(lines)


def generate_test(
    groups: dict[tuple[str, ...], list[tuple[str, str]]], source: Path, version: str
) -> str:
    lines = generated_preamble(
        source,
        version,
        ["Every generated constructor is expanded here when its Vulkan provider is available."],
    )
    lines += [
        '#include "vk_init.h"',
        "",
        "#define CHECK_INITIALIZER(type_, tag_)                                         \\",
        "    do {                                                                        \\",
        "        const type_ *value_ = &x##type_();                                      \\",
        "        if (value_->sType != (tag_)) {                                          \\",
        "            return 1;                                                           \\",
        "        }                                                                       \\",
        "    } while (0)",
        "",
        "static int check_all_initializers(void)",
        "{",
    ]

    for available, entries in sorted(groups.items(), key=lambda item: group_sort_key(item[0])):
        lines.append(f"#if {condition(available)}")
        for name, tag in entries:
            lines.append(f"    CHECK_INITIALIZER({name}, {tag});")
        lines.append("#endif")
    lines += [
        "    return 0;",
        "}",
        "",
        "static int check_designated_arguments(void)",
        "{",
        "    const VkApplicationInfo *info = &xVkApplicationInfo(",
        "        .pApplicationName = \"vk-init-test\",",
        "        .apiVersion = VK_API_VERSION_1_0,",
        "    );",
        "    return info->sType != VK_STRUCTURE_TYPE_APPLICATION_INFO",
        "        || info->apiVersion != VK_API_VERSION_1_0;",
        "}",
        "",
        "int main(void)",
        "{",
        "    return check_all_initializers() || check_designated_arguments();",
        "}",
        "",
    ]
    return "\n".join(lines)


def compile_test(header: str, test: str, compiler: str, include: Path) -> int | None:
    base_command = (
        shlex.split(compiler)
        + shlex.split(os.environ.get("CPPFLAGS", ""))
        + shlex.split(os.environ.get("CFLAGS", ""))
        + ["-std=c23", "-Wall", "-Wextra", "-Werror", "-pedantic-errors"]
        + (["-isystem", str(include)] if include.is_dir() else [])
    )
    with tempfile.TemporaryDirectory(prefix="vk-init-") as directory:
        temporary = Path(directory)
        header_path = temporary / "vk_init.h"
        test_path = temporary / "vk_init_test.c"
        object_path = temporary / "vk_init_test.o"
        header_path.write_text(header)
        test_path.write_text(test)
        try:
            macros = subprocess.run(
                base_command + ["-I", directory, "-dM", "-E", str(test_path)],
                check=True,
                stdout=subprocess.PIPE,
                text=True,
            ).stdout
            subprocess.run(
                base_command + ["-I", directory, "-c", str(test_path), "-o", str(object_path)],
                check=True,
            )
        except FileNotFoundError:
            print(f"compiler not found: {base_command[0]}", file=sys.stderr)
            return None
        except subprocess.CalledProcessError:
            return None
    return len(re.findall(r"^#define xVk\w+\(", macros, re.MULTILINE))


def update(path: Path, contents: str, check: bool) -> bool:
    current = path.read_text() if path.exists() else None
    if current == contents:
        return True
    if check:
        print(f"out of date: {path}", file=sys.stderr)
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--header", type=Path, default=DEFAULT_HEADER)
    parser.add_argument("--test", type=Path, default=DEFAULT_TEST)
    parser.add_argument("--version-file", type=Path, default=DEFAULT_VERSION)
    parser.add_argument("--cc", default=os.environ.get("CC", "cc"), help="C compiler command")
    parser.add_argument("--check", action="store_true", help="fail instead of updating stale output")
    args = parser.parse_args()

    root = ET.parse(args.registry).getroot()
    version = registry_header_version(root)
    groups = tagged_structs(root)
    count = sum(len(entries) for entries in groups.values())
    header = generate_header(groups, args.registry, version)
    test = generate_test(groups, args.registry, version)
    outputs = [(args.header, header), (args.test, test), (args.version_file, f"{version}\n")]
    if args.check and not all([update(path, contents, True) for path, contents in outputs]):
        return 1
    # Vulkan-Headers keeps the matching headers next to the registry.
    include = args.registry.resolve().parents[1] / "include"
    compiled_count = compile_test(header, test, args.cc, include)
    if compiled_count is None:
        print("Vulkan struct initializer compile test failed", file=sys.stderr)
        return 1
    if not args.check:
        for path, contents in outputs:
            update(path, contents, False)
    action = "checked" if args.check else "generated"
    print(f"{action} {count} Vulkan struct initializers (registry header {version})")
    print(f"compile-tested {compiled_count} constructors exposed by the current Vulkan headers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
