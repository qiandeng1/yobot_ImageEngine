import json
import os
import math
import sys
import asyncio
import httpx

from PIL import Image, ImageDraw, ImageFont
from typing import Optional, List, Set
from pathlib import Path

dirPath = os.path.join(os.path.dirname(__file__), "monster_icon", "data.json")
texturePath = os.path.join(os.path.dirname(__file__), "Resource")
headPicturePath = Path.cwd().resolve().joinpath("./yobot_data/user_profile") if "_MEIPASS" in dir(sys) else Path(__file__).parent.parent.parent.parent.parent.joinpath("./yobot_data/user_profile")
bossPath = Path(__file__).parent.parent.parent.parent.parent.joinpath("./public/libs/yocool@final/princessadventure/boss_icon")
with open(dirPath, "r", encoding="utf-8") as file:
    data = json.load(file)

global_missing_user_id: Set[int] = set()
save_picture_num = 0

def font_bold_generate(notes: str,
                       size: Optional[int] = None,
                       bgPixelX: Optional[int] = None,
                       bgPixelY: Optional[int] = None,
                       fontPixelX: Optional[int] = None,
                       fontPixelY: Optional[int] = None
                       ) -> Image.Image:
    if size is None:
        size = 17
    if bgPixelX is None:
        bgPixelX = 4
    if bgPixelY is None:
        bgPixelY = 3
    if fontPixelX is None:
        fontPixelX = 2
    if fontPixelY is None:
        fontPixelY = 1

    offsetX = int((bgPixelX - fontPixelX) / 2)
    offsetY = int((bgPixelY - fontPixelY) / 2)
    iconFont = ImageFont.truetype(os.path.join(texturePath, "tqxyt.ttf"), size=size)
    fontBox = iconFont.getbbox(text=notes)
    image = Image.new("RGBA", (fontBox[2] - fontBox[0] + bgPixelX, fontBox[3] - fontBox[1] + bgPixelY), (0, 0, 0, 0))
    textImage = ImageDraw.Draw(image)
    # textImage.text((0, 0), notes, font=iconFont, anchor="lt")
    for i in range(bgPixelX):
        for j in range(bgPixelY):
            textImage.text((i, j), notes, font=iconFont, anchor="lt")
    for i in range(fontPixelX):
        for j in range(fontPixelY):
            textImage.text((i + offsetX, j + offsetY), notes, font=iconFont, fill=(82, 82, 82), anchor="lt")
    return image


def head_picture_draw(QQnum: str, Notes: str) -> Image.Image:
    global global_missing_user_id
    # 处理头像
    userProfilePath = headPicturePath.joinpath(QQnum + ".jpg")
    if not userProfilePath.is_file():
        qqPicture = Image.new("RGBA", (20, 20), (255, 255, 255, 0))
        global_missing_user_id.add(int(QQnum))
    else:
        qqPicture = Image.open(userProfilePath)
        qqPicture = qqPicture.resize((20, 20))
    qqPicture = round_corner(qqPicture, 10)

    # 文本制作
    iconFont = ImageFont.truetype(os.path.join(texturePath, "tqxyt.ttf"), size=17)
    fontBox = iconFont.getbbox(text=Notes)
    if Notes:
        iconNotes = Image.new("RGBA", (30 + fontBox[2] - fontBox[0], 24), (152, 155, 183, 255))
    else:
        iconNotes = Image.new("RGBA", (24 + fontBox[2] - fontBox[0], 24), (152, 155, 183, 255))
    iconNotes = round_corner(iconNotes, 12)
    iconNotes.paste(qqPicture, (2, 2), mask=qqPicture)
    textImage = ImageDraw.Draw(iconNotes)

    for i in range(4):
        for j in range(3):
            textImage.text((26 + i - 3, j - 1), Notes, font=iconFont)
    for i in range(2):
        textImage.text((26 + i - 2, 0), Notes, font=iconFont, fill=(82, 82, 82))

    qqPicture.close()
    return iconNotes


def char_num_iteration_generation(extra_info: dict, state: str, max_row: int):
    ICON_OFFSET = 30 + 2
    ICON_GAP = 10
    NONE_ID_ICON = 24
    INFORMATION_WIDTH = 359

    idWidth = 0

    # 迭代计算出最大显示字符数
    iconFont = ImageFont.truetype(os.path.join(texturePath, "tqxyt.ttf"), size=17)
    for sliceNum in range(8, -1, -1):
        rowNum = 1
        for qqNum in extra_info[state]:
            # 对id进行切片,不需要切片的进else,切到0了就不显示id
            # 每行计算长度,超过三行认为id过长，回滚减短id长度重新计算行数
            if not sliceNum:
                iconWidth = NONE_ID_ICON
            elif len(extra_info[state][qqNum]) > sliceNum:
                fontBox = iconFont.getbbox(extra_info[state][qqNum][:sliceNum] + "..")
                iconWidth = fontBox[2] - fontBox[0] + ICON_OFFSET
            else:
                fontBox = iconFont.getbbox(extra_info[state][qqNum])
                iconWidth = fontBox[2] - fontBox[0] + ICON_OFFSET
            idWidth += iconWidth + ICON_GAP
            if idWidth > INFORMATION_WIDTH:
                rowNum += 1
                if not sliceNum:
                    idWidth = NONE_ID_ICON + ICON_GAP
                else:
                    idWidth = iconWidth
                if rowNum > max_row:
                    idWidth = 0
                    break
        if rowNum <= max_row:
            return sliceNum
    return 0


def information_generation(bgPicture: Image.Image,
                           extra_info: dict,
                           state: str,
                           sliceNum: int,
                           iconTopStart: int,
                           max_row: int) -> Image.Image:
    ICON_LEFT_START = 145
    ICON_TOP_START = 8
    NONE_ID_ICON = 24
    ICON_GAP = 10
    ICON_IGNORE_OFFSET = 9
    INFORMATION_WIDTH = 359

    # 根据迭代生成的id最大字符数，创建信息栏
    rowNum = 0
    informationPosX = ICON_LEFT_START
    informationPosY = iconTopStart
    for qqNum in extra_info[state]:
        if not sliceNum:
            headPicture = head_picture_draw(qqNum, "")
        elif len(extra_info[state][qqNum]) > sliceNum:
            headPicture = head_picture_draw(qqNum, extra_info[state][qqNum][:sliceNum] + "..")
        else:
            headPicture = head_picture_draw(qqNum, extra_info[state][qqNum])
        if informationPosX + headPicture.width > ICON_LEFT_START + INFORMATION_WIDTH:
            rowNum += 1
            if rowNum >= max_row:
                bgPicture.alpha_composite(font_bold_generate("..."), (informationPosX, informationPosY + ICON_IGNORE_OFFSET))
                break
            informationPosX = ICON_LEFT_START
            informationPosY += NONE_ID_ICON + ICON_TOP_START
        bgPicture.alpha_composite(headPicture, (informationPosX, informationPosY))
        informationPosX += headPicture.width + ICON_GAP
        headPicture.close()
    return bgPicture


def boss_statue_draw(bossID, extra_info: dict):
    RESERVE_POSITION_X = 96
    RESERVE_POSITION_Y = 14
    LINE_POSITION_X = 134
    LINE_POSITION_Y = 17
    ROW_LINE_POSITION_X = 89
    ROW_LINE_TOP_GAP = 7
    ICON_TOP_START = 8
    STATE_TOP_START = 10
    STATE_TOP_GAP = 13
    NONE_ID_ICON = 24

    stateDict = {'挑战': {'rowNum': 0, 'sliceNum': 0},
                 '挂树': {'rowNum': 0, 'sliceNum': 0},
                 '预约': {'rowNum': 0, 'sliceNum': 0}}

    challengerNum = len(extra_info['挑战'])
    # boss图片生成
    bgPicture = Image.open(os.path.join(texturePath, "bgBorad.png"))
    bossPicture = Image.open(os.path.join(bossPath, bossID + ".webp"))  # 已关闭
    bossPicture = bossPicture.resize((65, 65))
    bossPicture = round_corner(bossPicture, 10)
    bgPicture.paste(bossPicture, (21, 10), mask=bossPicture)
    bossDescribe = font_bold_generate(str(challengerNum) + "人挑战")  # 已关闭
    bgPicture.alpha_composite(bossDescribe, (21 + int((bossPicture.width - bossDescribe.width) / 2), 77))

    # 数据生成
    textImage = ImageDraw.Draw(bgPicture)
    textImage.line([(LINE_POSITION_X, LINE_POSITION_Y), (LINE_POSITION_X, LINE_POSITION_Y + 70)],
                   width=3,
                   fill=(175, 178, 199))
    if not challengerNum:
        # 28号字体生成
        iconFont = ImageFont.truetype(os.path.join(texturePath, "tqxyt.ttf"), size=28)
        for i in range(4):
            for j in range(3):
                textImage.text((RESERVE_POSITION_X + i, RESERVE_POSITION_Y + j), "预\n约", font=iconFont)
        for i in range(2):
            textImage.text((RESERVE_POSITION_X + i + 1, RESERVE_POSITION_Y + 1), "预\n约",
                           font=iconFont,
                           fill=(82, 82, 82))
        stateDict['预约']['rowNum'] = 3
    else:
        # 枚举四种状态.懒得优化了.代码丑就丑罢.反正没人看
        if not extra_info.get('挂树'):
            if len(extra_info['预约']) >= len(extra_info['挑战']):
                stateDict['预约']['rowNum'] = 2
                stateDict['挑战']['rowNum'] = 1
            else:
                stateDict['预约']['rowNum'] = 1
                stateDict['挑战']['rowNum'] = 2
        else:
            stateDict['挑战']['rowNum'] = 1
            stateDict['挂树']['rowNum'] = 1
            stateDict['预约']['rowNum'] = 1

        # 信息栏描述
        rowNum = 0
        for state in stateDict:
            if stateDict[state]['rowNum']:
                stateDescribe = font_bold_generate(state)  # 已关闭
                textPositionX = ROW_LINE_POSITION_X + int((LINE_POSITION_X - ROW_LINE_POSITION_X - stateDescribe.width) / 2) - 1
                textPositionY = STATE_TOP_START + (stateDescribe.height + STATE_TOP_GAP) * rowNum
                bgPicture.alpha_composite(stateDescribe, (textPositionX, textPositionY))
                stateDescribe.close()
                rowNum += stateDict[state]['rowNum']
                if not state == '挑战':
                    textImage.line(
                        [(ROW_LINE_POSITION_X, textPositionY - ROW_LINE_TOP_GAP), (LINE_POSITION_X, textPositionY - ROW_LINE_TOP_GAP)],
                        width=3,
                        fill=(175, 178, 199))

    boxRowNum = 0
    for state in stateDict:
        if stateDict[state]['rowNum']:
            # 迭代计算出最大显示字符数
            sliceNum = char_num_iteration_generation(extra_info, state, stateDict[state]['rowNum'])
            # 根据迭代生成的id最大字符数，创建信息栏
            bgPicture = information_generation(bgPicture, extra_info, state, sliceNum,
                                               ICON_TOP_START + (ICON_TOP_START + NONE_ID_ICON) * boxRowNum,
                                               stateDict[state]['rowNum'])
            boxRowNum += stateDict[state]['rowNum']

    bossPicture.close()
    bossDescribe.close()
    return bgPicture


def boss_hp_bar_draw(health, full_health) -> Image.Image:
    healthBar = Image.open(os.path.join(texturePath, "healthBar.png"))  # 已关闭
    if health <= full_health:
        barScale = health / full_health
    else:
        barScale = 1
    if 218 * barScale < 25:
        healthBar = healthBar.resize((25, 20))
    else:
        healthBar = healthBar.resize((int(218 * barScale), 20))
    healthBar = round_corner(healthBar, 10)
    outputImage = Image.new("RGBA", (218, 20), (0, 0, 0, 0))
    if health:
        outputImage.paste(healthBar, (0, 0), mask=healthBar)
    # 文本生成
    textImage = ImageDraw.Draw(outputImage)
    font = ImageFont.truetype(os.path.join(texturePath, "tqxyt.ttf"), size=17)
    if health > full_health:
        text = "boss血量异常"
    else:
        text = str(health) + "/" + str(full_health)
    fontBox = font.getbbox(text=text)
    for i in range(2):
        for j in range(2):
            textImage.text(((218 - fontBox[2]) / 2 + i - 1, (20 - fontBox[3] - fontBox[1]) / 2 + j - 1), text, font=font)
            
    healthBar.close()
    return outputImage


def boss_cycle_bar_draw(cycle) -> Image.Image:
    # 周目数生成
    if cycle % 2 == 0:
        cycleBar = Image.open(os.path.join(texturePath, "cycleBlue.png"))
    else:
        cycleBar = Image.open(os.path.join(texturePath, "cycleRed.png"))
    textImage = ImageDraw.Draw(cycleBar)
    font = ImageFont.truetype(os.path.join(texturePath, "tqxyt.ttf"), size=34)
    text = "第" + str(cycle) + "轮"
    fontBox = font.getbbox(text=text)

    # 上下左右各平移一次输出，制作粗体及外发光字体
    for i in range(5):
        for j in range(5):
            if cycle % 2 == 0:
                textImage.text(((cycleBar.width - fontBox[2] + fontBox[0]) / 2 + i - 3, j - 1), text, font=font,
                               fill=(60, 106, 190))
            else:
                textImage.text(((cycleBar.width - fontBox[2] + fontBox[0]) / 2 + i - 3, j - 1), text, font=font,
                               fill=(192, 56, 56))
    for i in range(3):
        for j in range(3):
            textImage.text(((cycleBar.width - fontBox[2] + fontBox[0]) / 2 + i - 2, j), text, font=font)

    return cycleBar


def round_corner(image: Image.Image, radius: Optional[int] = None) -> Image.Image:
    if radius is None:
        size = image.height
    else:
        size = radius * 2

    circle_bg = Image.new("L", (size * 5, size * 5), 0)  # 已确保关闭
    circle_draw = ImageDraw.Draw(circle_bg)
    circle_draw.ellipse((0, 0, size * 5, size * 5), 255)
    circle_bg = circle_bg.resize((size, size))

    if radius is None:
        circle_split_cursor_x = round(circle_bg.size[0] / 2)
        circle_split = (
            circle_bg.crop((0, 0, circle_split_cursor_x, size)), circle_bg.crop((circle_split_cursor_x, 0, size, size)))

        mask = Image.new("L", image.size, 255)  # 已确保关闭
        mask.paste(circle_split[0], (0, 0))
        mask.paste(circle_split[1], (image.width - circle_split[1].width, 0))
    else:
        circle_split = (
            circle_bg.crop((0, 0, radius, radius)),
            circle_bg.crop((radius, 0, radius * 2, radius)),
            circle_bg.crop((0, radius, radius, radius * 2)),
            circle_bg.crop((radius, radius, radius * 2, radius * 2)),
        )
        mask = Image.new("L", image.size, 255)  # 已确保关闭
        mask.paste(circle_split[0], (0, 0))
        mask.paste(circle_split[1], (image.width - radius, 0))
        mask.paste(circle_split[2], (0, image.height - radius))
        mask.paste(circle_split[3], (image.width - radius, image.height - radius))

    mask_paste_bg = Image.new("RGBA", image.size, (255, 255, 255, 0))  # 已确保关闭

    result = Image.composite(image, mask_paste_bg, mask)

    circle_bg.close()
    mask_paste_bg.close()
    mask.close()
    image.close()

    return result


def monster_icon_generate(monsterIdInt, health, full_health, cycle) -> Image.Image:
    monsterId = str(monsterIdInt)
    icon = Image.open(os.path.join(os.path.dirname(__file__), os.path.join("monster_icon", monsterId + ".png")))  # 已关闭
    stage = Image.open(os.path.join(texturePath, "stage.png"))  # 已关闭

    # icon背景生成，宽度须分为4种情况
    # monster图片宽度小于stage宽度
    # monster图片中心左侧宽度小于stage中心左侧宽度
    # monster图片中心右侧宽度小于stage中心右侧宽度
    # monster图片宽度大于stage宽度
    leftCompare = data[monsterId]["width"] - data["stage"]["width"]
    rightCompare = (icon.width - data[monsterId]["width"]) - (stage.width - data["stage"]["width"])
    bgHeight = data[monsterId]["height"] + stage.height - data["stage"]["height"]

    # 图片粘贴时坐标补偿
    if leftCompare < 0:
        axisOffset = abs(leftCompare)
    else:
        axisOffset = 0

    if icon.width < stage.width:
        if rightCompare < 0:
            bossState = Image.new("RGBA", (stage.width, bgHeight), (0, 0, 0, 0))
        else:
            bossState = Image.new("RGBA", (stage.width + rightCompare, bgHeight), (0, 0, 0, 0))
    elif leftCompare < 0:
        bossState = Image.new("RGBA", (icon.width - leftCompare, bgHeight), (0, 0, 0, 0))
    elif rightCompare < 0:
        bossState = Image.new("RGBA", (icon.width - rightCompare, bgHeight), (0, 0, 0, 0))
    else:
        bossState = Image.new("RGBA", (icon.width, bgHeight), (0, 0, 0, 0))

    bossState.paste(stage, (leftCompare + axisOffset, bgHeight - stage.height), mask=stage)
    bossState.alpha_composite(icon, (axisOffset, 0))
    bossHpBar = boss_hp_bar_draw(health, full_health)  # 已关闭
    bossCycleBar = boss_cycle_bar_draw(cycle)  # 已关闭
    bossState.paste(bossHpBar, (leftCompare + axisOffset + 111, bgHeight - stage.height + 120), mask=bossHpBar)
    bossState.paste(bossCycleBar, (
        data[monsterId]["width"] + axisOffset - int(bossCycleBar.width / 2), data[monsterId]["height"] + 17),
                    mask=bossCycleBar)

    icon.close()
    stage.close()
    bossHpBar.close()
    bossCycleBar.close()
    return bossState


def cycle_state_generate(levelCycle, bossCycle) -> Image.Image:
    BG_FONT_START = 189
    BACKGROUND_HEIGHT = 60
    BACKGROUND_WIDTH = 315

    cycleRound = Image.open(os.path.join(texturePath, "cycleRound.png"))  # 已关闭
    cycleRound = cycleRound.crop((0, levelCycle * BACKGROUND_HEIGHT, BACKGROUND_WIDTH, (levelCycle + 1) * BACKGROUND_HEIGHT))
    cycleState = Image.new("RGBA", (BACKGROUND_WIDTH, BACKGROUND_HEIGHT), (0, 0, 0, 0))
    cycleState.paste(cycleRound, (0, 0), mask=cycleRound)
    text = "当前为" + str(bossCycle) + "周目"

    textImage = font_bold_generate(text, 27, 7, 6, 3, 2)  # 已关闭
    cycleState.alpha_composite(textImage, (BG_FONT_START - textImage.width, int((BACKGROUND_HEIGHT - textImage.height) / 2) + 3))

    cycleRound.close()
    textImage.close()
    return cycleState


def rank_num_generate(clanRank: Optional[int] = 0, selfRank: Optional[int] = 0) -> Image.Image:
    IMAGE_WIDTH = 490
    SELF_START_X = 380
    NUM_WIDTH = 36

    # 预留公会排名接口,目前暂无查询方法,输入为0的情况下,排名会变臭
    if clanRank == 0:
        clanRank = 114514

    cycleTime = 0
    numImage = Image.open(os.path.join(texturePath, "rankNum.png"))  # 已关闭
    rankNUm = Image.new("RGBA", (IMAGE_WIDTH, IMAGE_WIDTH), (0, 0, 0, 0))
    for i in map(int, str(clanRank)):
        rankNUm.alpha_composite(numImage.crop((i * NUM_WIDTH, 0, (i + 1) * NUM_WIDTH, 45)), (cycleTime * NUM_WIDTH, 0))
        cycleTime += 1
    rankNUm.alpha_composite(numImage.crop((360, 0, 396, 45)), (cycleTime * NUM_WIDTH, 0))
    cycleTime = 0
    for i in map(int, str(selfRank)):
        rankNUm.alpha_composite(numImage.crop((i * NUM_WIDTH, 45, (i + 1) * NUM_WIDTH, 90)), (SELF_START_X + cycleTime * NUM_WIDTH, 0))
        cycleTime += 1
    rankNUm.alpha_composite(numImage.crop((360, 45, 396, 90)), (SELF_START_X + cycleTime * NUM_WIDTH, 0))

    numImage.close()
    return rankNUm


def state_image_generate(groupBossData: dict, bossStateImageList: list, clanInfo: dict) -> Image.Image:
    global save_picture_num
    
    CYCLE_STATE_IMAGE_X = 484
    CYCLE_STATE_IMAGE_Y = 150
    monsterIcon = []
    totalPixelX = 0
    actualX = []
    actualY = [878, 801, 595, 862, 514]
    actualBossId = []

    # 生成背景图片,等找到真正的背景图片后要做修改
    resultImage = Image.new("RGBA", (2048, 1536), (0, 0, 0, 0))
    bgClanBattle = Image.open(os.path.join(texturePath, "background", "4.png"))  # 已关闭
    bgClanBattle = bgClanBattle.resize((2048, 1536))
    resultImage.paste(bgClanBattle, (0, 0))

    # 生成Monster及血量图片，储存在monsterIcon[]数组里面，同时计算出所有Icon的横坐标Pixl之和
    for bossNum in range(1, 6):
        thisBossData = groupBossData[bossNum]
        # try:
        for i in range(1, 14):
            bossId = str(bossNum * 1000 + i)
            if thisBossData["name"] == data[bossId]["cnName"]:
                actualBossId.append(bossId)
                monsterIcon.append(
                    monster_icon_generate(bossId, thisBossData["health"], thisBossData["full_health"],
                                          thisBossData["cycle"]))
                # 野性狮鹫这玩意出现太频繁了，画幅还宽就很烦，导致画面会看起来很难看，单独给他做点处理
                if bossId == "2004":
                    totalPixelX = totalPixelX + monsterIcon[bossNum - 1].width - 70
                else:
                    totalPixelX = totalPixelX + monsterIcon[bossNum - 1].width
                break
            else:
                pass
        # except:
        #     print("err: Monster数据异常")
    iconGap = int((resultImage.width - totalPixelX - 100) / 4)
    # 计算出实际X轴数值
    for xAxisNum in range(0, 5):
        if xAxisNum == 0:
            actualX.append(50)
        elif actualBossId[xAxisNum - 1] == "2004":
            actualX.append(actualX[xAxisNum - 1] + monsterIcon[xAxisNum - 1].width + iconGap - 70)
        else:
            actualX.append(actualX[xAxisNum - 1] + monsterIcon[xAxisNum - 1].width + iconGap)

    # 在上面的计算完成后，获得了actualX，actualY（其中actualX是图片左边缘，actualY是boss阴影中心）
    battleRecordOffSet = actualX[3] + monsterIcon[3].width - 1482
    if battleRecordOffSet > 0:
        actualX[3] = actualX[3] - battleRecordOffSet

    stageLine = Image.open(os.path.join(texturePath, "stageLine.png"))  # 已关闭
    for lineNum in range(0, 4):
        # 计算连结线长度，先算连结线X长度及Y长度，勾股定理算第三边长（这次真的是勾股定理x
        deltaX = actualX[lineNum + 1] + data[actualBossId[lineNum + 1]]["width"] - actualX[lineNum] - \
                 data[actualBossId[lineNum]]["width"]
        deltaY = actualY[lineNum] - actualY[lineNum + 1]
        lineLong = math.sqrt(pow(deltaX, 2) + pow(deltaY, 2))
        actualLine = stageLine.resize((int(lineLong), 20))  # 已关闭
        # 计算需要的旋转角度，用反正切倒推角度
        lineAngle = math.atan2(deltaY, deltaX)
        lineAngle = lineAngle / math.pi * 180
        # offsetAngleX = int(lineLong - lineLong/2 * math.cos(math.radians(lineAngle)))
        offsetAngleY = int(lineLong / 2 * math.sin(math.radians(lineAngle)))
        # 创建更大的画布，否则旋转后的连结线会因为画布不够大而被裁切
        lineImage = Image.new("RGBA", (actualLine.width, actualLine.width), (0, 0, 0, 0))  # 已关闭
        lineImage.paste(actualLine, (0, int(actualLine.width / 2) - 10), mask=actualLine)
        lineImage = lineImage.rotate(lineAngle)
        # 这里需要算出线段初始点对应图片的坐标，否则会产生位移
        resultImage.paste(lineImage, (actualX[lineNum] + data[actualBossId[lineNum]]["width"],
                                      actualY[lineNum] - int(actualLine.width / 2) + 10 - offsetAngleY), mask=lineImage)
        lineImage.close()
        actualLine.close()

    # 将boss放到指定位置
    for bossNum in [0, 1, 3, 2, 4]:
        resultImage.paste(
            monsterIcon[bossNum],
            (actualX[bossNum], actualY[bossNum] - data[actualBossId[bossNum]]["height"]),
            mask=monsterIcon[bossNum])
        monsterIcon[bossNum].close()

    clanBattle = Image.open(os.path.join(texturePath, "clanBattle.png"))
    # resultImage.paste(clanBattle, (0, 0), mask=clanBattle)
    resultImage.alpha_composite(clanBattle, (0, 0))
    for i in range(5):
        resultImage.alpha_composite(bossStateImageList[i], (1512, 732 + 105 * i))

    # 周目数状态栏绘制
    cycleStateImage = cycle_state_generate(clanInfo["levelCycle"], clanInfo["bossCycle"])
    resultImage.alpha_composite(cycleStateImage, (CYCLE_STATE_IMAGE_X, CYCLE_STATE_IMAGE_Y))

    # 出刀数绘制
    informationFont = font_bold_generate(str(clanInfo["finishChallengeCount"]), 28, 6, 6, 2, 2)
    resultImage.alpha_composite(informationFont, (912 - informationFont.width, 1153))
    informationFont = font_bold_generate(str(clanInfo["halfChallengeCount"]), 28, 6, 6, 2, 2)
    resultImage.alpha_composite(informationFont, (1228 - informationFont.width, 1153))

    # 排名绘制
    rankImage = rank_num_generate(clanInfo["clanRank"], clanInfo["selfRank"])
    resultImage.alpha_composite(rankImage, (1060, 103))
    
    resultImage.save(os.path.join(os.path.dirname(__file__), os.path.join("test", str(save_picture_num) + ".png")), "png")
    save_picture_num += 1

    bgClanBattle.close()
    stageLine.close()
    clanBattle.close()
    cycleStateImage.close()
    informationFont.close()
    rankImage.close()

    return resultImage



async def download_pic(url: str, proxies: Optional[str] = None, file_name="") -> Optional[Path]:
    image_path = headPicturePath.joinpath(file_name)
    client = httpx.AsyncClient(proxies=proxies, timeout=5)
    try:
        async with client.stream(method="GET", url=url, timeout=15) as response:  # type: ignore # params={"proxies": [proxies]}
            if response.status_code != 200:
                raise ValueError(f"Image respond status code error: {response.status_code}")
            with open(image_path, "wb") as f:
                async for chunk in response.aiter_bytes():
                    f.write(chunk)
    except Exception:
        return None
    finally:
        await client.aclose()
    return image_path


async def download_user_profile_image(user_id_list: List[int]) -> None:
    task_list = []
    for this_user_id in user_id_list:
        task_list.append(download_pic(f"http://q1.qlogo.cn/g?b=qq&nk={this_user_id}&s=1", file_name=f"{this_user_id}.jpg"))
    await asyncio.gather(*task_list)


async def download_missing_user_profile() -> None:
    global global_missing_user_id
    if not global_missing_user_id:
        return
    await download_user_profile_image(list(global_missing_user_id))
    global_missing_user_id = set()

