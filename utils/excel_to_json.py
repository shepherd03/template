import os
import json
import pandas as pd
import re

def excel_to_json(excel_file_path, json_file_path=None):
    """
    将Excel文件转换为JSON文件
    
    Args:
        excel_file_path: Excel文件路径
        json_file_path: JSON文件路径，默认为Excel文件同目录下的同名JSON文件
    """
    # 如果未指定JSON文件路径，则使用默认路径
    if json_file_path is None:
        json_file_path = os.path.splitext(excel_file_path)[0] + '.json'
    
    # 加载Excel数据，读取所有sheet
    try:
        excel_data = pd.read_excel(excel_file_path, sheet_name=None)
    except Exception as e:
        print(f"加载Excel文件失败: {e}")
        return False
    
    # 存储所有转换后的JSON数据
    all_json_data = []
    
    # 处理每个sheet
    for sheet_name, df in excel_data.items():
        print(f"处理表格: {sheet_name}")
        
        # 跳过空表格
        if df.empty:
            print(f"表格 {sheet_name} 为空，跳过处理")
            continue
        
        # 确保必要的列存在
        required_columns = ['domain', 'intent', '问题模板']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"表格 {sheet_name} 缺少必要的列: {missing_columns}，跳过处理")
            continue
        
        # 处理每一行数据
        for _, row in df.iterrows():
            # 跳过空行或domain为空的行
            if pd.isna(row['domain']) or pd.isna(row['intent']):
                continue
            
            # 创建基本JSON结构
            json_item = {
                "domain": row['domain'],
                "intent": row['intent'],
                "slots_mapping": {}
            }
            
            # 添加扩充句（如果存在）
            if '扩充句' in df.columns and not pd.isna(row['扩充句']):
                json_item["expanded_sentence"] = row['扩充句']
            
            # 添加问题模板
            if not pd.isna(row['问题模板']):
                json_item["pattern"] = row['问题模板']
                
                # 提取问题模板中的槽位
                slots = re.findall(r'\[(.*?)\]', row['问题模板'])
                
                # 处理每个槽位的可替换值
                for slot in slots:
                    # 检查是否有对应的可替换值列
                    slot_column = f"{slot}:[可取值]"
                    if slot_column in df.columns and not pd.isna(row[slot_column]):
                        # 将可替换值字符串拆分为列表
                        replaceable_values = [val.strip() for val in str(row[slot_column]).split(',') if val.strip()]
                        if replaceable_values:
                            json_item["slots_mapping"][slot] = replaceable_values
            
            # 添加到结果列表
            all_json_data.append(json_item)
    
    # 保存JSON文件
    try:
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(all_json_data, f, ensure_ascii=False, indent=4)
        print(f"JSON文件已保存至: {json_file_path}")
        return True
    except Exception as e:
        print(f"保存JSON文件失败: {e}")
        return False

def main():
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    excel_file_path = os.path.join(current_dir, "问题模板20250304_beautifuler.xlsx")
    json_file_path = os.path.join(current_dir, "slot_dependency_new.json")
    
    # 转换Excel到JSON
    success = excel_to_json(excel_file_path, json_file_path)
    
    if success:
        # 读取生成的JSON文件并打印前几条记录作为示例
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print("\n转换完成！生成的JSON示例:")
            for i, item in enumerate(data[:3]):
                print(f"\n示例 {i+1}:")
                print(json.dumps(item, ensure_ascii=False, indent=2))
            
            print(f"\n共生成 {len(data)} 条记录")
        except Exception as e:
            print(f"读取生成的JSON文件失败: {e}")
    else:
        print("转换失败！")

if __name__ == "__main__":
    main()