#!/bin/bash

# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。

set -e

echo "=== MediaCrawler API 服务启动脚本 ==="

# 检查并创建虚拟环境
if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "升级pip..."
pip install --upgrade pip

# 安装依赖
echo "安装项目依赖..."
pip install fastapi uvicorn sqlalchemy aiosqlite aiomysql pydantic typing-extensions python-multipart

# 确保脚本可执行
chmod +x api_server.py

echo ""
echo "=== 启动API服务 ==="
echo "API文档地址: http://localhost:8001/docs"
echo "健康检查地址: http://localhost:8001/health"
echo "按 Ctrl+C 停止服务"
echo ""

# 启动API服务
uvicorn api_server:app --host 0.0.0.0 --port 8001 --reload