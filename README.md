# Yobot ImageEngine
[![License](https://img.shields.io/github/license/qiandeng1/yobot_ImageEngine)](LICENSE) 
[![Fork](https://img.shields.io/badge/yobot-remix-blue)](https://github.com/eggggi/yobot_remix)

Yobot_ImageEngine是针对[yobot_remix](https://github.com/eggggi/yobot_remix)开发的QQBot回复消息仿游戏界面的插件项目
> 示例效果
> 
> ![demo](https://github.com/qiandeng1/yobot_ImageEngine/blob/main/image/demo.jpg)
## 目录
- [开始使用](https://github.com/qiandeng1/yobot_ImageEngine/#开始使用)
	- [环境](https://github.com/qiandeng1/yobot_ImageEngine/#环境)
	- [安装](https://github.com/qiandeng1/yobot_ImageEngine/#安装)
	- [使用](https://github.com/qiandeng1/yobot_ImageEngine/#使用)
- [待更新内容](https://github.com/qiandeng1/yobot_ImageEngine/#待更新内容)
- [相关项目](https://github.com/qiandeng1/yobot_ImageEngine/#相关项目)

## 开始使用
### 环境
本项目仅包含图片生成引擎及相关魔改文件，需要搭配[yobot_remix](https://github.com/eggggi/yobot_remix)本体使用
Python环境

P.S.
yobot_remix安装方式与yobot安装方式一致，可以参考
> [Yobot Linux 手动部署](http://yobot.win/install/Linux-gocqhttp/)

### 安装
 1. git clone本项目或前往[Releases](https://github.com/qiandeng1/yobot_ImageEngine/releases)下载文件
 2. 将文件夹`components`覆盖☞`yobot_remix/src/client/ybplugins/clan_battle`下的`components`文件夹

### 使用
重启yobot_remix即可使用

## 待更新内容

 - [ ] 场景背景轮换（实在是找不到背景图片了，现在是用的白羊座五王的战斗背景临时代替的，有没有大佬可以帮帮我找一下背景图片）
 - [ ] 左上角公会战时间制作（要找个日程表来订阅）
 - [x] 公会排名显示（由于现在并没有开源查询公会排名的接口，暂无开发计划，已预留接口）
 - [ ] 个人排名显示（已预留接口）
 - [ ] 开发yobot其他公会战相关回复图片生成

## 相关项目
[yobot_remix](https://github.com/eggggi/yobot_remix)：yobot魔改版，支持新版公会战。
[yobot](https://github.com/yuudi/yobot)：是为[公主连接](https://priconne-redive.jp/)公会战设计的辅助机器人，能够帮助公会战管理者提供自动化管理服务。
