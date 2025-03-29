import os
import json
import pandas as pd
import re

current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
question_template_name = '问题模板20250304_beautifuler.xlsx'
output_json_name = 'dependency.json'
necessary_heads = ["domain","intent","可替换值"]

def read_excel():
    excel_file_path = os.path.join(current_dir, question_template_name)
    dfs = pd.read_excel(excel_file_path,sheet_name=None)
    return dfs

def parse_excecl(dfs):
    result = []
    for sheet_name,df in dfs.items():
        try:
            print("------------------------------------")
            print(f"开始解析sheet {sheet_name}")
            column_names = df.columns.tolist()
            if not all(column_name in column_names for column_name in necessary_heads):
                print(f"sheet {sheet_name} 缺少必要的列名")
                print("------------------------------------")
                continue
            
            # 记录跳过的行数
            skipped_rows = 0
            invalid_json_rows = 0
            
            for index, row in df.iterrows():
                domain = row["domain"]
                intent = row["intent"]
                slots_str = row["可替换值"]
                
                # 检查必要列是否为空
                if pd.isna(domain) or pd.isna(intent) or pd.isna(slots_str):
                    skipped_rows += 1
                    continue
                
                try:
                    # 如果slots_str已经是字典类型，则不需要解析
                    if isinstance(slots_str, dict):
                        slots = slots_str
                    else:
                        # 确保slots_str是字符串类型
                        slots_str = str(slots_str)
                        
                        # 尝试处理单引号的情况
                        try:
                            # 先尝试标准JSON解析
                            slots = json.loads(slots_str)
                        except json.JSONDecodeError:
                            # 如果失败，尝试将单引号替换为双引号并解析
                            try:
                                # 使用正则表达式替换单引号为双引号，但避免替换已经转义的单引号
                                # 先将字符串中的双引号转义
                                slots_str = slots_str.replace('\\"', '____DOUBLEQUOTE____')
                                # 将单引号替换为双引号
                                slots_str = slots_str.replace("'", '"')
                                # 恢复原来的转义双引号
                                slots_str = slots_str.replace('____DOUBLEQUOTE____', '\\"')
                                # 再次尝试解析
                                slots = json.loads(slots_str)
                            except json.JSONDecodeError:
                                # 如果仍然失败，抛出异常
                                raise
                    
                    result.append({
                        "domain": domain,
                        "intent": intent,
                        "slots": slots  # 这里存储的是JSON对象，而不是字符串
                    })
                except json.JSONDecodeError:
                    # 如果JSON解析失败，记录错误并跳过该行
                    print(f"  行 {index+2}: slots字段不是有效的JSON格式: {slots_str}")
                    invalid_json_rows += 1
                    continue
            
            print(f"解析sheet {sheet_name} 成功，跳过了 {skipped_rows} 行空数据，{invalid_json_rows} 行无效JSON数据")
        except Exception as e:
            print(f"解析sheet {sheet_name} 失败: {e}")
            print("------------------------------------")
            continue
        print("------------------------------------")
    return result


if __name__ == '__main__':
    dfs = read_excel()
    result = parse_excecl(dfs)
    output_file_path = os.path.join(current_dir, output_json_name)
    with open(output_file_path,'w',encoding='utf-8') as f:
        json.dump(result,f,ensure_ascii=False,indent=4)
        print(f"转换完成，结果已保存至 {output_file_path}")