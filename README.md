# Yobot_ImageEngine
[![License](https://img.shields.io/github/license/qiandeng1/yobot_ImageEngine)](LICENSE) 
[![Fork](https://img.shields.io/badge/yobot-remix-blue)](https://github.com/eggggi/yobot_remix)

Yobot_ImageEngine是针对[yobot_remix](https://github.com/eggggi/yobot_remix)开发的QQBot回复消息仿游戏界面的插件项目
> 示例效果
> 
> ![demo](https://github.com/qiandeng1/yobot_ImageEngine/blob/main/image/demo1.jpg)
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
 1. 前往[Releases](https://github.com/qiandeng1/yobot_ImageEngine/releases)下载文件
 2. 将文件夹`components`覆盖☞`yobot_remix/src/client/ybplugins/clan_battle`下的`components`文件夹

### 使用
重启yobot_remix即可使用

## 待更新内容

 - [x] 死亡boss变成盒子而不是现在没有变化
 - [x] 场景背景轮换（背景图片已完成，按照星座轮换）
以下内容部分更新完成，由于本项目不再更新，有该部分需求请移步[yobot_plus](https://github.com/qiandeng1/yobot_plus)
 - [x] 左上角公会战时间制作
 - [x] 公会排名显示
 - [ ] 个人排名显示（已预留接口）
 - [ ] 优化图片生成速度
 - [ ] 切换公会战档案时，清除上周期公会战排名

## 相关项目
[yobot_plus](https://github.com/qiandeng1/yobot_plus)：yobot魔改版的再魔改，公会战战斗状态游戏风格回复，显示内容更丰富。
[yobot_remix](https://github.com/eggggi/yobot_remix)：yobot魔改版，支持新版公会战。
[yobot](https://github.com/yuudi/yobot)：是为[公主连接](https://priconne-redive.jp/)公会战设计的辅助机器人，能够帮助公会战管理者提供自动化管理服务。
