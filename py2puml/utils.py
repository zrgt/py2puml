import re
from ast import parse
from inspect import getsource
from pathlib import Path
from typing import Type, Union, Optional


def investigate_domain_definition(type_to_inspect: Type):
    """
    Utilitary function which inspects the annotations of the given type
    """
    type_annotations = getattr(type_to_inspect, '__annotations__', None)
    if type_annotations is None:
        # print(f'class {type_to_inspect.__module__}.{type_to_inspect.__name__} of type {type(type_to_inspect)} has no annotation')
        for attr_class_key in dir(type_to_inspect):
            if attr_class_key != '__doc__':
                print(f'{type_to_inspect.__name__}.{attr_class_key}:', getattr(type_to_inspect, attr_class_key))
    else:
        # print(type_to_inspect.__annotations__)
        for attr_name, attr_class in type_annotations.items():
            for attr_class_key in dir(attr_class):
                if attr_class_key != '__doc__':
                    print(
                        f'{type_to_inspect.__name__}.{attr_name}:', attr_class_key, getattr(attr_class, attr_class_key)
                    )


def classname(cls):
    module = cls.__module__
    name = cls.__qualname__
    if module is not None and module != "__builtin__":
        name = module + "." + name
    return name


def read_file(file: Union[str, Path]) -> str:
    with open(file, 'r', encoding='utf8') as f:
        return f.read()


def write_file(file: Union[str, Path], content: str):
    with open(file, 'w', encoding='utf8') as f:
        f.write(content)


def has_decorator(class_type, decorator_name: Optional[str] = None):
    if class_type is None:
        return
    # Get the source code of the class
    source = getsource(class_type)
    # Parse the source code into an AST
    parsed_ast = parse(source)
    if hasattr(parsed_ast.body[0], 'decorator_list') and parsed_ast.body[0].decorator_list:
        if decorator_name is None:
            return True
        for decorator in parsed_ast.body[0].decorator_list:
            if hasattr(decorator, 'id') and decorator.id == decorator_name:
                return True
            elif hasattr(decorator, 'func') and decorator.func.id == decorator_name:
                return True
    return False


def snake_to_camel(snake_str):
    new_str = snake_str
    if re.search(r'_([a-zA-Z])([a-zA-Z]+)', new_str):
        new_str = re.sub(r'_([a-zA-Z])([a-zA-Z]+)', lambda match: match.group(1).upper() + match.group(2).lower(),
                         new_str)
        new_str = re.sub(r'([A-Z])([A-Z]+)([A-Z])',
                         lambda match: match.group(1) + match.group(2).lower() + match.group(3), new_str)
    return new_str
