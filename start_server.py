import sys, os
# 直接把项目根加入路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8001,
        reload=True,
    )