import json
import os
from typing import List, Dict, Any, Optional

# 导入自定义类型定义
from types_custom import LastSlot, Dependency, ValidationResult, SlotDict, TemplateResponse, ErrorType

# 白名单槽位，这些槽位不需要验证
slot_white_list = ["time", "org", "option"]

# 文件缓存
_file_cache = {}

def load_file(file_path: str, default: Any = None) -> Any:
    # 检查缓存
    if file_path in _file_cache:
        return _file_cache[file_path]
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        # 更新缓存
        _file_cache[file_path] = content
        return content
    except Exception as e:
        print(f"加载文件失败 {file_path}: {e}")
        return default


class TemplateParser:
    def __init__(self, dependency_file_path: Optional[str] = None, templates_json_path: Optional[str] = None):
        # 获取当前脚本所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 设置默认依赖关系文件路径
        if dependency_file_path is None:
            dependency_file_path = os.path.join(current_dir, "dependency.json")
            print("dependency加载完毕")
        
        # 设置默认模板JSON文件路径
        if templates_json_path is None:
            templates_json_path = os.path.join(current_dir, "templates.json")
            print("templates.json路径设置完毕")
        
        # 加载依赖关系
        self.dependencies: List[Dependency] = load_file(dependency_file_path, [])
        
        # 加载模板JSON
        self.templates = load_file(templates_json_path, {})
        print("templates.json加载完毕")
    
    def validate_user_data(self, user_data: LastSlot) -> Dict[str, Any]:
        # 获取用户数据中的domain、intent和slots
        user_domain = user_data.get("domain", "")
        user_intent = user_data.get("intent", "")
        user_slots: Dict[str, Any] = user_data.get("slots", {})
        
        print(f"开始验证用户数据: domain={user_domain}, intent={user_intent}, slots={user_slots}")
        
        # 验证domain和intent是否存在
        if not user_domain:
            return {"code": 1, "message": "缺少domain信息", "data": {}}
        if not user_intent:
            return {"code": 1, "message": "缺少intent信息", "data": {}}
        
        # 查找匹配的依赖关系，domain和intent都匹配的
        matched_dependencies = []
        for dependency in self.dependencies:  # type: Dependency
            if dependency.get("domain") == user_domain and dependency.get("intent") == user_intent:
                matched_dependencies.append(dependency)
        
        print(f"找到匹配的依赖关系数量: {len(matched_dependencies)}")
        
        if not matched_dependencies:
            return {"code": 1, "message": f"未找到匹配的domain({user_domain})和intent({user_intent})组合", "data": {}}

        error_slot = []
        error_slot_value = []
        error_both = []

        print(f"开始验证slots匹配情况，共有{len(matched_dependencies)}个匹配的依赖关系")
        
        for dependency_index, dependency in enumerate(matched_dependencies):
            print(f"正在验证第{dependency_index+1}个依赖关系")
            lost_slots = {}
            value_errors = {}

            is_correct = True

            dependency_slots = dependency.get("slots", {})
            print(f"依赖关系中的slots: {dependency_slots}")

            score = 100

            for slot_key, slot_value_list in dependency_slots.items():
                if slot_key in slot_white_list:
                    continue
                if slot_key not in user_slots:
                    is_correct = False
                    score -= 10
                    lost_slots[slot_key] = slot_value_list
                elif user_slots[slot_key] not in slot_value_list:
                    is_correct = False
                    score -= 5
                    value_errors[slot_key] = slot_value_list

            current_errors = {
                "lost_slots": lost_slots,
                "value_errors": value_errors,
                "score": score,
            }
            
            if is_correct:
                print("验证成功，返回结果")
                return {"code": 0, "message": "验证成功", "data": current_errors}
            
            lost_slots_flag = len(current_errors["lost_slots"]) > 0
            value_errors_flag = len(current_errors["value_errors"]) > 0

            if lost_slots_flag:
                error_slot.append(current_errors)
            if value_errors_flag:
                error_slot_value.append(current_errors)
            if lost_slots_flag and value_errors_flag:
                error_both.append(current_errors)
        
        # 对三个错误列表按照score从大到小排序
        error_slot.sort(key=lambda x: x["score"], reverse=True)
        error_slot_value.sort(key=lambda x: x["score"], reverse=True)
        error_both.sort(key=lambda x: x["score"], reverse=True)
        
        # 选择三者中分数最高的那一个作为返回结果
        highest_score = -1
        highest_error = None
        error_type = ""
        
        if error_slot and (not highest_error or error_slot[0]["score"] > highest_score):
            highest_score = error_slot[0]["score"]
            highest_error = error_slot[0]
            error_type = ErrorType.LOST_SLOT
            
        if error_slot_value and (not highest_error or error_slot_value[0]["score"] > highest_score):
            highest_score = error_slot_value[0]["score"]
            highest_error = error_slot_value[0]
            error_type = ErrorType.VALUE_ERRORS
            
        if error_both and (not highest_error or error_both[0]["score"] > highest_score):
            highest_score = error_both[0]["score"]
            highest_error = error_both[0]
            error_type = ErrorType.BOTH_ERROR
        
        if highest_error:
            highest_error["error_type"] = error_type
            return {"code": 1, "message": f"验证失败: {error_type}", "data": highest_error}
        
        # 如果没有找到任何错误，返回默认错误
        return {"code": 1, "message": "验证失败", "data": {}}

    def process_template(self, user_data: LastSlot) -> Dict[str, Any]:
        """
        处理用户数据，先验证数据，再根据错误类型选择模板并填充错误信息
        
        Args:
            user_data: 用户数据
            
        Returns:
            处理结果，包含模板内容
        """
        # 先调用validate_user_data验证用户数据
        validation_result = self.validate_user_data(user_data)
        
        # 如果验证成功，直接返回结果
        if validation_result.get("code") == 0:
            return {
                "code": 0,
                "message": "验证成功",
                "data": {
                    "content": "验证成功"
                }
            }
        
        # 获取错误类型
        error_data = validation_result.get("data", {})
        error_type = error_data.get("error_type", "")
        conetent = ""
        # 根据错误类型选择模板
        print(error_data)
        if error_type == ErrorType.LOST_SLOT:
            temp = ""
            for key,value in error_data[error_type.value].items():
                temp += key + "：" + "、".join(value) + "\n"
            conetent = "由于缺少以下槽位信息而导致无法查出{}".format(temp)
        elif error_type == ErrorType.VALUE_ERRORS:
            temp = ""
            for key,value in error_data[error_type.value].items():
                temp += key + "：" + "、".join(value) + "\n"
            conetent = "不好意思，此次查询由于以下槽位数据暂时不支持查找而导致无法得出结果{}".format(temp)
        elif error_type == ErrorType.BOTH_ERROR:
            for key,value in error_data[error_type.value].items():
                conetent += key + "：" + "、".join(value) + "\n"
        # 构造返回结果
        return {
            "code": validation_result.get("code", 1),
            "message": validation_result.get("message", "验证失败"),
            "data": {
                "content": conetent,
            }
        }

parser = TemplateParser()