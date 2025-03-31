from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uvicorn
import json

# 导入模板解析器
from template_parser import parser

# 创建FastAPI应用
app = FastAPI(
    title="模板解析API",
    description="提供模板解析服务的API接口",
    version="1.0.0"
)

# 添加CORS中间件，允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源的请求，生产环境中应该限制来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有HTTP头
)

# 定义请求模型
class UserData(BaseModel):
    org: Optional[str] = ""
    time: Optional[str] = ""
    origin_slot: Dict[str, Any]
    last_slot: Dict[str, Any]
    result: Optional[Dict[str, Any]] = {}
    order: Optional[str] = ""
    cur_domain: Optional[str] = ""
    lead_add: Optional[List[Any]] = []
    last_option: Optional[List[Any]] = []

# 定义标准响应模型
class StandardResponse(BaseModel):
    code: int = 200
    success: bool = True
    message: str = ""
    data: Optional[Dict[str, Any]] = None

# 定义模板响应数据模型
class TemplateData(BaseModel):
    template_name: Optional[str] = None
    content: str

# 定义模板响应模型
class TemplateResponse(StandardResponse):
    data: Dict

@app.post("/validate",summary="验证模板", description="根据用户数据验证模板")
async def api_validate(user_data: UserData):
    # 获取last_slot数据
    last_slot = user_data.last_slot
    print(last_slot)
    # 直接调用模板解析函数
    result = parser.validate_user_data(last_slot)
    print(result)

    # 正确构造TemplateResponse对象
    response = TemplateResponse(
        code=200 if result.get("code") == 0 else 400,
        success=result.get("code") == 0,
        message=result.get("message", ""),
        data=result.get("data", {})
    )

    return response

@app.post("/parse_template",summary="解析模板", description="根据用户数据解析匹配的模板内容")
async def api_parse_template(user_data: UserData):
    # 将Pydantic模型转换为字典
    # 获取last_slot数据
    last_slot = user_data.last_slot
    print(last_slot)
    # 直接调用模板解析函数
    result = parser.process_template(last_slot)
    print(result)

    # 正确构造TemplateResponse对象
    response = TemplateResponse(
        code=200 if result.get("code") == 0 else 400,
        success=result.get("code") == 0,
        message=result.get("message", ""),
        data=result.get("data", {})
    )

    return response

@app.get("/", summary="API状态检查", description="检查API服务是否正常运行")
async def root():
    return {
        "code": 200,
        "success": True,
        "message": "模板解析API服务正常运行",
        "data": {"status": "running"}
    }

# 启动服务器
if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)