#!/bin/bash

# PurpleAir Temperature Calibration Web App - 启动脚本
# ================================================

echo "🌡️ PurpleAir Temperature Calibration Web App"
echo "=============================================="
echo ""

# 检查是否在app目录
if [ ! -f "app.py" ]; then
    echo "❌ Error: Please run this script from the app/ directory"
    echo "   cd app/ && ./start_app.sh"
    exit 1
fi

# 检查依赖
echo "📦 Checking dependencies..."
if ! pip list | grep -q streamlit; then
    echo "⚠️  Streamlit not found. Installing dependencies..."
    pip install -r requirements.txt
else
    echo "✅ Dependencies installed"
fi

echo ""
echo "🚀 Starting web app..."
echo "📱 The app will open in your browser at: http://localhost:8501"
echo ""
echo "💡 Tips:"
echo "   - Press Ctrl+C to stop the server"
echo "   - To deploy online, see DEPLOYMENT_GUIDE.md"
echo ""
echo "=============================================="
echo ""

# 启动Streamlit
streamlit run app.py
