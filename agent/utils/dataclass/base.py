from typing import Dict
from pydantic.fields import Field
from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict
import typing as t
import pickle
from enum import Enum
from datetime import datetime
from threading import Lock

# pickle dumps nál kell. Kicseréli erre a threading Lock-okat és vissza rakja loads-nál
class DummyLock: pass

class DataclassBaseModel(PydanticBaseModel):

    model_config = ConfigDict(
        use_enum_values = True,
        arbitrary_types_allowed = True,
    )

    # class Config:
    #     use_enum_values = True
    #     arbitrary_types_allowed = True
    
    def __post_init__(self): pass

    def model_post_init(self, __context: t.Any):

        if hasattr(self, '__post_init__'):
            self.__post_init__()

    @classmethod
    def is_pydantic_dataclass(cls, obj) -> bool:

        cls = obj if isinstance(obj, type) else type(obj)

        return all(hasattr(cls, item) for item in PydanticBaseModel.__slots__)

    @classmethod
    def loads(cls, data: bytes) -> 'DataclassBaseModel':

        return pickle.loads(data)
    
    def __getstate__(self) -> dict[t.Any, t.Any]:
        # print('__getstate__')

        state = super().__getstate__()
    
        for state_name, state_items in state.items():
            # print(state_name)
            if isinstance(state_items, dict):

                for name, value in state_items.items():

                    if isinstance(value, type(Lock())):
                        state[state_name][name] = DummyLock()
        
        return state
    
    def __setstate__(self, state: dict[t.Any, t.Any]) -> None:

        # print('__setstate__')
    
        for state_name, state_items in state.items():

            if isinstance(state_items, dict):

                for name, value in state_items.items():

                    if isinstance(value, DummyLock):
                        state[state_name][name] = Lock()
        # print(state)
        return super().__setstate__(state)

    def dumps(self) -> bytes:

        # print(dir(self))

        # print()

        return pickle.dumps(self)
    
    def as_dict(self) -> dict[str, t.Any]:

        return {k: self._value_to_dict(v) for k, v in super().__dict__.items()}
    
    @classmethod
    def _value_to_dict(cls, value: t.Any) -> t.Any:

        if cls.is_pydantic_dataclass(value):
            return {k: cls._value_to_dict(v) for k, v in value.__dict__.items()}
        elif isinstance(value, list):
            return [cls._value_to_dict(item) for item in value]
        elif isinstance(value, tuple):
            return tuple([cls._value_to_dict(item) for item in list(value)])
        elif isinstance(value, dict):
            return {k: cls._value_to_dict(v) for k, v in value.items()}
        elif isinstance(value, Enum):
            return value.value
        else:
            return value
    
    def __str__(self) -> str:
        return self.__repr__()
    
    def __repr__(self):
        fields = []
        for field_name, field_value in self.__dict__.items():

            # print(field_name, field_value, type(field_value))

            if field_name.startswith("_") == True:
                continue

            if isinstance(field_value, bytes):
                value = f"Bytes({len(field_value)})"
            elif isinstance(field_value, str):
                value = f"'{field_value}'"
            elif isinstance(field_value, datetime):
                try:
                    value = f"datetime({field_value.strftime('%Y-%m-%d %H:%M:%S.%f')}, tz={field_value.tzinfo})"
                except:
                    value = f"datetime({field_value})"
            elif isinstance(field_value, list) and next((True for item in field_value if self.is_pydantic_dataclass(item.__class__)), False) == True:
                list_value = []
                for item in field_value:
                    if isinstance(item, str):
                        item = f"'{item}'"
                        # print(item)
                    elif self.is_pydantic_dataclass(item.__class__) == True:
                        item = str(item)
                    list_value.append(item)
                    # print(list_value)

                value = "[%s]" % (str(', '.join(list_value)))

            elif self.is_pydantic_dataclass(field_value.__class__) == True:
                value = str(field_value)
            
            else:
                value = field_value

            fields.append(f"{field_name}={value}")

        return f"{self.__class__.__name__}({', '.join(fields)})"