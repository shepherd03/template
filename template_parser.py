import json
import re
import os

class TemplateParser:
    def __init__(self, template_file_path):
        """
        初始化模板解析器
        
        Args:
            template_file_path: 模板文件路径
        """
        self.template_file_path = template_file_path
        self.templates = self._load_templates()
    
    def _load_templates(self):
        """
        加载模板文件
        
        Returns:
            list: 模板列表
        """
        try:
            with open(self.template_file_path, 'r', encoding='utf-8') as f:
                templates = json.load(f)
            return templates
        except Exception as e:
            print(f"加载模板文件失败: {e}")
            return []
    
    def _match_domain(self, template_domains, user_domain):
        """
        匹配领域
        
        Args:
            template_domains: 模板中的领域列表
            user_domain: 用户对象中的领域
            
        Returns:
            bool: 是否匹配
        """
        if not user_domain:
            return False
        
        # 通配符匹配任意有效值
        if "*" in template_domains:
            return True
        
        return user_domain in template_domains
    
    def _match_intent(self, template_intents, user_intent):
        """
        匹配意图
        
        Args:
            template_intents: 模板中的意图列表
            user_intent: 用户对象中的意图
            
        Returns:
            bool: 是否匹配
        """
        if not user_intent:
            return False
        
        # 通配符匹配任意有效值
        if "*" in template_intents:
            return True
        
        return user_intent in template_intents
    
    def _match_slots(self, template_slots, user_slots):
        """
        匹配槽位
        
        Args:
            template_slots: 模板中的槽位列表
            user_slots: 用户对象中的槽位
            
        Returns:
            bool: 是否匹配
        """
        if not template_slots:  # 如果模板没有指定槽位要求，则匹配成功
            return True
        
        if not user_slots:  # 如果用户没有槽位但模板要求有槽位，则匹配失败
            return False
        
        # 检查每个模板槽位是否在用户槽位中
        for slot_dict in template_slots:
            slot_key = list(slot_dict.keys())[0]  # 获取槽位名称
            
            # 检查用户槽位中是否存在该槽位
            if slot_key not in user_slots:
                return False
            
            # 如果槽位值不是通配符，则需要精确匹配
            if slot_dict[slot_key] != "*" and user_slots[slot_key] != slot_dict[slot_key]:
                return False
        
        return True
    
    def _match_conditions(self, template_conditions, user_data):
        """
        匹配条件
        
        Args:
            template_conditions: 模板中的条件
            user_data: 用户数据
            
        Returns:
            bool: 是否匹配
        """
        # 检查origin_slot匹配
        if "origin_slot" in template_conditions and "origin_slot" in user_data:
            template_origin = template_conditions["origin_slot"]
            user_origin = user_data["origin_slot"]
            
            # 匹配domain
            if not self._match_domain(template_origin.get("domain", []), user_origin.get("domain", "")):
                return False
            
            # 匹配intent
            if not self._match_intent(template_origin.get("intent", []), user_origin.get("intent", "")):
                return False
            
            # 匹配slots
            if not self._match_slots(template_origin.get("slots", []), user_origin.get("slots", {})):
                return False
        
        # 检查last_slot匹配
        if "last_slot" in template_conditions and "last_slot" in user_data:
            template_last = template_conditions["last_slot"]
            user_last = user_data["last_slot"]
            
            # 匹配domain
            if not self._match_domain(template_last.get("domain", []), user_last.get("domain", "")):
                return False
            
            # 匹配intent
            if not self._match_intent(template_last.get("intent", []), user_last.get("intent", "")):
                return False
            
            # 匹配slots
            if not self._match_slots(template_last.get("slots", []), user_last.get("slots", {})):
                return False
        
        return True
    
    def _replace_variables(self, content, user_data):
        """
        替换模板中的变量
        
        Args:
            content: 模板内容
            user_data: 用户数据
            
        Returns:
            str: 替换后的内容
        """
        # 使用正则表达式查找所有{{}}格式的变量
        pattern = r'\{\{([^\}]+)\}\}'
        matches = re.findall(pattern, content)
        
        # 替换每个变量
        for match in matches:
            var_path = match.strip()  # 变量路径，如 origin_slot.slots.query_count
            parts = var_path.split('.')
            
            # 获取变量值
            value = user_data
            try:
                for part in parts:
                    value = value[part]
            except (KeyError, TypeError):
                value = "未知"  # 如果变量不存在，则替换为"未知"
            
            # 替换变量
            content = content.replace(f"{{{{{match}}}}}", str(value))
        
        return content
    
    def find_best_template(self, user_data):
        """
        查找最佳匹配的模板
        
        Args:
            user_data: 用户数据
            
        Returns:
            dict: 最佳匹配的模板和填充后的内容
        """
        matched_templates = []
        
        # 遍历所有模板，找出匹配的模板
        for template in self.templates:
            if self._match_conditions(template.get("conditions", {}), user_data):
                matched_templates.append(template)
        
        if not matched_templates:
            return {
                "template": None,
                "content": "未找到匹配的模板"
            }
        
        # 按优先级排序（数字越小优先级越高）
        matched_templates.sort(key=lambda x: int(x.get("priority", 99)))
        
        # 获取最佳匹配的模板
        best_template = matched_templates[0]
        
        # 替换模板中的变量
        content = self._replace_variables(best_template.get("content", ""), user_data)
        
        return {
            "template": best_template,
            "content": content
        }

# 使用示例
def parse_template(user_data, template_file_path=None):
    """
    解析模板
    
    Args:
        user_data: 用户数据
        template_file_path: 模板文件路径，默认为当前目录下的template.json
        
    Returns:
        dict: 最佳匹配的模板和填充后的内容
    """
    if template_file_path is None:
        # 获取当前脚本所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_file_path = os.path.join(current_dir, "template.json")
    
    parser = TemplateParser(template_file_path)
    return parser.find_best_template(user_data)