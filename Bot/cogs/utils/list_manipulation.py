from typing import Any, List, Tuple


def insert_or_append(list_1: List[Any], value: Any, index: int = None) -> Tuple[List[Any], Any, int]:
    """
    Inserts or appends the given value to the given list according to the index value.

    Parameters
    __________
    list_1: List[Any]
        The list which the modifications has to be made.
    value: Any
        The value which has to be inserted or appended to the given list.
    index: int
        Index value where the value needs to be placed. Defaults to None

    Raises
    ______
    IndexError
         If the wrong index is passed.

    Returns
    _______
    Updated list, the value passed and the new index of the value.

    Return Type
    ___________
    Tuple[List[Any], Any, int]

    """
    if not index:
        list_1.append(value)
    elif -1 <= index < len(list_1):
        list_1.insert(index, value)
    else:
        raise IndexError("The index you sent is invalid!")
    new_index = list_1.index(value)
    return list_1, value, new_index


def pop_or_remove(list_1: List[Any], value: Any, index: int = None) -> Tuple[List[Any], Any, int]:
    """
    Pops or removes the given value from the given list according to the index value.

    Parameters
    __________
    list_1: List[Any]
        The list which the modifications has to be made.
    value: Any
        The value which has to be popped or removed to the given list.
    index: int
        Index value where the value needs to be removed. Defaults to None

    Raises
    ______
    IndexError
         If the wrong index is passed.

    Returns
    _______
    Updated list, the value passed and the old index of the value.

    Return Type
    ___________
    Tuple[List[Any], Any, int]

    """
    old_index = list_1.index(value)
    if not index:
        list_1.remove(value)
    elif -1 <= index < len(list_1):
        list_1.pop(index)
    else:
        raise IndexError("The index you sent is invalid!")
    return list_1, value, old_index


def replace_or_set(list_1: List[Any], value: Any, index: int) -> Tuple[List[Any], Any, int]:
    """
    Replaces or sets the given value in the given list according to the index value.

    Parameters
    __________
    list_1: List[Any]
        The list which the modifications has to be made.
    value: Any
        The value which has to be replaced or set to the given list.
    index: int
        Index value where the value needs to be replaced or set.

    Raises
    ______
    IndexError
         If the wrong index is passed.

    Returns
    _______
    Updated list, the value passed and the index of the value.

    Return Type
    ___________
    Tuple[List[Any], Any, int]

    """
    print(len(list_1))
    print(index)
    print(-1 < index < len(list_1))
    if not -1 < index < len(list_1):
        raise IndexError("The index you sent is invalid!")
    list_1[index] = value
    return list_1, value, index
