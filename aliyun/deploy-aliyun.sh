#!/usr/bin/env bash
# 知识点闯关 · 一键部署到阿里云轻量服务器（在本机 deploy/ 目录执行）
#   bash aliyun/deploy-aliyun.sh            默认 root@39.96.207.137
set -euo pipefail
HOST="${1:-root@39.96.207.137}"
REMOTE_DIR=/var/www/kpquiz
FILES=(index.html sw.js manifest.webmanifest icon-180.png icon-192.png icon-512.png)
echo "==> 上传到 $HOST:$REMOTE_DIR"
ssh "$HOST" "mkdir -p $REMOTE_DIR"
scp "${FILES[@]}" "$HOST:$REMOTE_DIR/"
echo "==> 站点配置（独立端口 9010 + 挂在 9000 的 /kp/ 路径）"
scp aliyun/kpquiz-9010.conf "$HOST:/etc/nginx/conf.d/kpquiz.conf"
ssh "$HOST" 'grep -q "location ^~ /kp/" /etc/nginx/conf.d/badtogo.conf || sed -i "/^    location \/ {/i\    # 知识点闯关（借用已放行的 9000 端口）\n    location ^~ /kp/ { alias /var/www/kpquiz/; index index.html; try_files \$uri \$uri/ /kp/index.html; add_header Cache-Control \"no-cache\"; }\n" /etc/nginx/conf.d/badtogo.conf; nginx -t && systemctl reload nginx'
echo "==> 完成：http://39.96.207.137:9000/kp/   （放行 9010 后：http://39.96.207.137:9010/）"
