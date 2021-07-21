#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MIT License

Copyright (c) 2021-present Daniel [Mathtin] Shiko <wdaniil@mail.ru>
Project: Minecraft Discord Bot

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

__author__ = "DeadBlasoul"

import logging
import os
import sys
from typing import Dict, List, Type, Any
from xml.etree import ElementTree

from license import license_py_file

log = logging.getLogger('srv-gen')

NoneType = type(None)


def indent(string: str, level: int = 1) -> str:
    return (' ' * 4) * level + string


def indent_all(lines: List[str], level: int = 1) -> List[str]:
    return [indent(line, level) for line in lines]


def gen_function(name: str, args: List[str], body: List[str], ret_type: Type[Any] = NoneType) -> List[str]:
    ret_type_name = ret_type.__name__ if ret_type is not NoneType else 'None'
    return [
               f'def {name}({", ".join(args)}) -> {ret_type_name}:'
           ] + indent_all(body)


def gen_class_name(source_name: str) -> str:
    return 'X' + source_name.title().replace('-', '')


def gen_property_name(source_name: str) -> str:
    return source_name.upper().replace('-', '_')


def gen_header() -> str:
    return '''\
__author__ = None
    
import os.path
from typing import Dict
import xml.etree.ElementTree as ET
from .exceptions import MissingResourceException


def res_path(local_path: str):
    path = os.getenv('RESOURCE_PATH')
    return os.path.join(path, local_path)
'''


class CodeGenerator(object):
    @property
    def code(self) -> str:
        """Returns generated source code"""
        raise NotImplementedError()


class TypeViewGenerator(CodeGenerator):
    _strings: List[str]
    _code: List[str]
    _class_name: str
    _property_name: str
    _type_name: str

    def __init__(self, type_name: str, declaration: List[str]):
        self._type_name = type_name
        self._strings = declaration
        self._code = []
        self._class_name = gen_class_name(self._type_name)
        self._property_name = gen_property_name(self._type_name)

    def _generate_code(self) -> None:
        self._code = []
        self._gen_class_header()
        self._gen_get()
        for string_name in self._strings:
            self._gen_property(string_name)

    def _gen_class_header(self) -> None:
        self._code += [
                          f'class {self._class_name}(object):',
                          indent(f'_type_name = "{self._type_name}"'),
                          ''
                      ] + indent_all(
            gen_function(
                '__init__', args=['self', 'section'], body=['self._section = section']
            )
        ) + ['']

    def _gen_get(self) -> None:
        self._code += indent_all(
            gen_function(
                'get', args=['self', 'string_name'], ret_type=str,
                body=['return self._section.get(self._type_name, string_name)']
            )
        ) + ['']

    def _gen_property(self, name: str) -> None:
        self._code += indent_all(
            ['@property'] +
            gen_function(
                gen_property_name(name), args=['self'], ret_type=str,
                body=[f'return self.get("{name}")']
            )
        ) + ['']

    @property
    def code(self) -> str:
        if not self._code:
            self._generate_code()
        return '\n'.join(self._code)

    @property
    def lines(self) -> List[str]:
        if not self._code:
            self._generate_code()
        return self._code

    @property
    def property_name(self):
        return self._property_name

    @property
    def class_name(self):
        return self._class_name


class SectionViewGenerator(CodeGenerator):
    _code: List[str]
    _types: List[TypeViewGenerator]
    _class_name: str
    _property_name: str
    _section_name: str
    _parent_class_name: str

    def __init__(self, parent_class_name: str, section_name: str, declaration: Dict[str, List[str]]):
        self._code = []
        self._section_name = section_name
        self._types = [TypeViewGenerator(k, v) for k, v in declaration.items()]
        self._class_name = SectionViewGenerator._gen_section_class_name(self._section_name)
        self._property_name = SectionViewGenerator._gen_section_property_name(self._section_name)
        self._parent_class_name = parent_class_name

    def _generate_code(self) -> None:
        self._code = []
        self._gen_class_name()
        for type_generator in self._types:
            self._code += indent_all(type_generator.lines)
            self._code.append('')
        self._gen_section_name()
        for type_generator in self._types:
            self._code.append(indent(f'{type_generator.property_name}: {type_generator.class_name}'))
        self._code.append('')
        self._gen_constructor()
        self._code.append('')
        self._gen_get()

    def _gen_class_name(self) -> None:
        self._code.append(f'class {self._class_name}(object):')

    def _gen_section_name(self) -> None:
        self._code.append(indent(f'_section_name = "{self._section_name}"'))

    @staticmethod
    def _gen_section_property_name(source_name) -> str:
        prop_name = gen_property_name(source_name)
        return prop_name[:-1] if prop_name.lower().endswith('s') else prop_name

    @staticmethod
    def _gen_section_class_name(source_name) -> str:
        prop_name = gen_class_name(source_name)
        return prop_name[:-1] if prop_name.lower().endswith('s') else prop_name

    def _gen_constructor(self) -> None:
        self._code += indent_all(
            gen_function(
                '__init__', args=['self', 'res'],
                body=['self._res = res'] + [
                    f'self.{t.property_name} = {self._parent_class_name}.{self._class_name}.{t.class_name}(self)' for t
                    in self._types]
            )
        )

    def _gen_get(self) -> None:
        self._code += indent_all(
            gen_function(
                'get', args=['self', 'type_name', 'string_name'], ret_type=str,
                body=['return self._res.get(self._section_name, type_name, string_name)']
            )
        )

    @property
    def code(self) -> str:
        if not self._code:
            self._generate_code()
        return '\n'.join(self._code)

    @property
    def lines(self) -> List[str]:
        if not self._code:
            self._generate_code()
        return self._code

    @property
    def property_name(self):
        return self._property_name

    @property
    def class_name(self):
        return self._class_name


class StringResourceViewGenerator(CodeGenerator):
    _code: List[str]
    _name: str
    _class_name: str
    _property_name: str
    _sections: List[SectionViewGenerator]

    def __init__(self, name: str, declaration: Dict[str, Dict[str, List[str]]]):
        self._code = []
        self._name = name
        self._class_name = gen_class_name(self._name)
        self._property_name = gen_property_name(self._name)
        self._sections = [SectionViewGenerator(self._class_name, k, v) for k, v in declaration.items()]

    def _generate_code(self) -> None:
        self._code = []

        self._gen_class_name()
        for section in self._sections:
            self._code += indent_all(section.lines)
            self._code.append('')
        self._gen_private_fields()
        for section in self._sections:
            self._code.append(indent(f'{section.property_name}: {section.class_name}'))
        self._code.append('')
        self._gen_constructor()
        self._code.append('')
        self._gen_switch_lang()
        self._code.append('')
        self._gen_get()
        self._code += ['', '']
        self._gen_instance()
        self._code.append('')

    def _gen_private_fields(self):
        self._code += indent_all([
            '_lang: str',
            '_root: ET.Element',
            '_path_cache: Dict[str, str]'
        ])

    def _gen_class_name(self) -> None:
        self._code.append(f'class {self._class_name}(object):')

    def _gen_constructor(self) -> None:
        self._code += indent_all(
            gen_function('__init__', args=['self', 'lang: str = \'en\''],
                         body=[
                             f'self._strings_path = res_path("{self._name}.xml")',
                             'if not os.path.isfile(self._strings_path):',
                             indent(f'raise MissingResourceException(self._strings_path, "{self._name}.xml")'),
                             'self._root = ET.parse(self._strings_path).getroot()'
                         ] + [
                             f'self.{s.property_name} = {self._class_name}.{s.class_name}(self)' for s in self._sections
                         ] + [
                             'self.switch_lang(lang)'
                         ])
        )

    def _gen_switch_lang(self):
        self._code += indent_all(
            gen_function('switch_lang', args=['self', 'lang: str'], body=['self._lang = lang', 'self._path_cache = {}'])
        )

    def _gen_get(self):
        self._code += indent_all(gen_function(
            'get', args=['self', 'section_name', 'type_name', 'string_name'], ret_type=str,
            body=[
                'path = \'.\'.join([section_name, type_name, string_name])',
                'if path in self._path_cache:',
                indent('return self._path_cache[path]'),
                'res = self._root.find(f\'.//{section_name}/string[@lang="{self._lang}"]'
                '[@type="{type_name}"][@name="{string_name}"]\')',
                'self._path_cache[path] = res.text if res is not None else path',
                'return self._path_cache[path]'
            ]
        )
        )

    def _gen_instance(self):
        self._code.append(f'{self._property_name} = {self._class_name}()')

    @property
    def code(self) -> str:
        if not self._code:
            self._generate_code()
        return '\n'.join(self._code)


def extract_distinct_declaration(xml_file_path) -> Dict[str, Dict[str, List[str]]]:
    if not os.path.isfile(xml_file_path):
        raise Exception(f'There is no resource file via path "{xml_file_path}"')

    log.info(f'Loading {xml_file_path}')
    root = ElementTree.parse(xml_file_path).getroot()

    declaration = {}
    for section in root:
        for resource in section:
            section_name = section.tag
            type_name = resource.attrib['type']
            resource_name = resource.attrib['name']

            if section_name not in declaration:
                declaration[section_name] = {}
            if type_name not in declaration[section_name]:
                declaration[section_name][type_name] = []
            if resource_name not in declaration[section_name][type_name]:
                declaration[section_name][type_name].append(resource_name)

    return declaration


def main(_):
    xml = 'res/strings.xml'
    output = 'src/util/resources.py'
    declaration = extract_distinct_declaration(xml)
    generator = StringResourceViewGenerator('strings', declaration)

    with open(output, 'w') as file:
        file.write(gen_header() + '\n\n' + generator.code)

    license_py_file(output)


if __name__ == '__main__':
    main(sys.argv)
