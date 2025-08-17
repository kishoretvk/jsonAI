from termcolor import colored


from typing import Any, Union

def highlight_values(value: Any, return_as_string: bool = False) -> Union[str, None]:
    """Highlight values in nested data structures with an option to return as a string."""
    output: list[str] = []

    def recursive_print(obj: Any, indent: int = 0, is_last_element: bool = True) -> None:
        if isinstance(obj, dict):
            output.append("{")
            last_key = list(obj.keys())[-1]
            for key, value in obj.items():
                output.append(f"{' ' * (indent + 2)}{key}: ")
                recursive_print(value, indent + 2, key == last_key)
            output.append(f"{' ' * indent}}}" + (",\n" if not is_last_element else "\n"))
        elif isinstance(obj, list):
            output.append("[")
            for index, value in enumerate(obj):
                output.append(f"{' ' * (indent + 2)}")
                recursive_print(value, indent + 2, index == len(obj) - 1)
            output.append(f"{' ' * indent}]" + (",\n" if not is_last_element else "\n"))
        else:
            if isinstance(obj, str):
                obj = f'"{obj}"'
            output.append(colored(obj, "green") + (",\n" if not is_last_element else "\n"))

    recursive_print(value)
    if return_as_string:
        return "".join(output)
    else:
        print("".join(output))
    return None
