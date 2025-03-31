from typing import Dict, List, Any, Optional, Union
from typing_extensions import TypedDict
from enum import Enum, auto

# 定义槽位类型
class Slot(TypedDict):
    key: str
    value: Any

# 定义依赖关系中的槽位值类型
SlotValues = List[str]

# 定义依赖关系中的槽位字典类型
SlotDict = Dict[str, SlotValues]

# 定义依赖关系类型
class Dependency(TypedDict):
    domain: str
    intent: str
    slots: Dict[str, SlotDict]

# 定义用户数据类型
class LastSlot(TypedDict):
    domain: str
    intent: str
    slots: Dict[str, str]

# 定义验证结果类型
class ValidationResult(TypedDict):
    code: int
    message: str
    data: Dict[str, Any]

# 定义错误信息类型
class ErrorInfo(TypedDict):
    missing_slots: List[str]
    invalid_slots: List[Dict[str, Any]]
    undefined_slots: List[str]

# 定义模板内容类型
class TemplateContent(TypedDict):
    content: str

# 定义模板字典类型
TemplateDict = Dict[str, TemplateContent]

# 定义错误类型枚举
class ErrorType(str, Enum):
    LOST_SLOT = "lost_slots"        # 缺少槽位错误
    VALUE_ERRORS = "value_errors"  # 槽位值错误
    BOTH_ERROR = "both_error"       # 同时存在两种错误

# 定义模板响应类型
class TemplateResponse(TypedDict):
    template: Dict[str, str]
    content: str