from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uvicorn
import json

# 导入模板解析器
from template_parser import parse_template

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
    data: Optional[TemplateData] = None

@app.post("/parse_template", response_model=TemplateResponse, summary="解析模板", description="根据用户数据解析匹配的模板内容")
async def api_parse_template(user_data: UserData):
    try:
        # 将Pydantic模型转换为字典
        user_dict = user_data.dict()
        
        # 调用模板解析函数
        result = parse_template(user_dict)
        
        # 构建响应
        template_data = TemplateData(
            template_name=result["template"]["name"] if result["template"] else None,
            content=result["content"]
        )
        
        response = TemplateResponse(
            code=200,
            success=True,
            message="模板解析成功",
            data=template_data
        )
        
        return response
    except Exception as e:
        # 异常处理
        raise HTTPException(
            status_code=500,
            detail={
                "code": 500,
                "success": False,
                "message": f"模板解析失败: {str(e)}",
                "data": None
            }
        )

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