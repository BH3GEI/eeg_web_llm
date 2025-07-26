#!/bin/bash
echo "🚀 启动智能待办清单前端服务..."

cd frontend

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

# 启动开发服务器
echo "启动Vue开发服务器 (http://localhost:3000)..."
npm run dev