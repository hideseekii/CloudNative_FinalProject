#!/bin/bash

echo "📱 生成 Port-Forward QR Code"
echo "================================"

# 確認 port-forward 地址
URL="http://140.113.193.244:8080"

echo "🌐 訪問地址: $URL"
echo ""

# 檢查是否安裝了 qrencode
if ! command -v qrencode &> /dev/null; then
    echo "安裝 qrencode..."
    if command -v brew &> /dev/null; then
        brew install qrencode
    elif command -v apt-get &> /dev/null; then
        sudo apt-get install -y qrencode
    else
        echo "請手動安裝 qrencode"
        exit 1
    fi
fi

# 在終端顯示 QR Code
echo "📱 掃描下方 QR Code 訪問應用："
echo ""
qrencode -t ansiutf8 "$URL"
echo ""

# 同時生成圖片文件
qrencode -o "port-forward-qr.png" -s 8 "$URL"
echo "🖼️  QR Code 圖片已保存為: port-forward-qr.png"

# 嘗試打開圖片（macOS）
if command -v open &> /dev/null; then
    echo "🖼️  正在打開 QR Code 圖片..."
    open "port-forward-qr.png"
fi

echo ""
echo "💡 使用說明："
echo "1. 確保 port-forward 正在運行："
echo "   kubectl port-forward svc/django 8080:80 -n cloudnative-final"
echo ""
echo "2. 用手機掃描 QR Code"
echo "3. 或直接訪問: $URL"
echo ""
echo "✅ 完成！"
