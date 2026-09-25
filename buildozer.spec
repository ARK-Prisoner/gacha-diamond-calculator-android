[app]

# (str) 应用显示名称（可含中文）
title = 攒钻抽卡计算器

# (str) 包名（仅小写字母、数字、点、下划线）
package.name = gachacalc

# (str) 包域名，最终包名为 package.domain.package.name
package.domain = org.gachacalc

# (str) 源码目录（默认当前目录）
source.dir = .

# (str) 需要打包进 APK 的文件扩展名（注意包含 otf 字体）
source.include_exts = py,png,jpg,kv,atlas,ttf,otf,ttc

# (str) 应用版本号
version = 1.0

# (list) 运行时依赖
# 通过 p4a.branch 锁定 python-for-android 到 v2024.01.21（其默认 Python 3.11.5，Kivy 2.3.x 兼容）
# filetype：Kivy 2.3.x 启动时强制依赖，p4a 无对应配方，需手动加入以便 pip 安装
requirements = python3,kivy==2.3.1,filetype==1.2.0

# (str) 锁定的 python-for-android 版本（新版默认 Python 3.14，Kivy 2.3.x 无法编译）
p4a.branch = v2024.01.21

# (str) 应用入口（默认 main.py）
#source.include_patterns = main.py

# (str) 屏幕方向
orientation = portrait

# (bool) 是否全屏
fullscreen = 0

# (str) 支持的 CPU 架构（只编 arm64，编译更快；现代手机都是 arm64）
android.archs = arm64-v8a

# (str) Android NDK 版本（锁定 r25b，与 python3.11 + kivy 兼容；默认 r28c 过新会导致编译失败）
android.ndk = 25b

# (int) 目标 Android API 版本
android.api = 33

# (int) 最低支持的 Android 版本
android.minapi = 21

# (bool) 自动接受 SDK 许可协议
android.accept_sdk_license = True

# (list) 需要的权限（本应用无需额外权限）
# android.permissions = INTERNET

# (bool) 允许系统备份应用数据
android.allow_backup = True

# (str) 应用标签图标与启动画面（可选，缺省即可）
# icon.filename = %(source.dir)s/icon.png
# presplash.filename = %(source.dir)s/presplash.png

[buildozer]

# (int) 日志级别：0 = 仅错误，1 = 信息，2 = 调试
log_level = 2

# (int) 编译时显示警告级别
warn_on_root = 1
