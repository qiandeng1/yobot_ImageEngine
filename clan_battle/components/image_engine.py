from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import sys
from typing import Tuple, List, Optional, Dict, Set, Union, Any
from pathlib import Path
import httpx
import asyncio

FILE_PATH = Path(sys._MEIPASS).resolve() if "_MEIPASS" in dir(sys) else Path(__file__).resolve().parent
FONTS_PATH = os.path.join(FILE_PATH, "fonts")
FONTS = os.path.join(FONTS_PATH, "msyh.ttf")
USER_HEADERS_PATH = Path.cwd().resolve().joinpath("./yobot_data/user_profile") if "_MEIPASS" in dir(sys) else Path(__file__).parent.parent.parent.parent.joinpath("./yobot_data/user_profile")
BOSS_ICON_PATH = Path(__file__).parent.parent.parent.parent.joinpath("./public/libs/yocool@final/princessadventure/boss_icon")

glovar_missing_user_id: Set[int] = set()


def image_engine_init():
    if not USER_HEADERS_PATH.is_dir():
        USER_HEADERS_PATH.mkdir()


class BackGroundGenerator:
    """
    被动背景生成器
    不会立即创建Image对象及执行粘贴操作  以便动态生成画布大小
    注意  一旦生成图像后(generate()方法)  缓存的图像都会被销毁  不可再次生成

    :param color: 画布背景颜色
    :param padding: 画布外部拓展边距 (左 上 右 下)
    :override_size: 强制生成该大小的画布 (长 宽) 不包括外部拓展边距 可设置None跳过
    """

    def __init__(
        self,
        color: Union[Tuple[int, int, int], Tuple[int, int, int, int]] = (255, 255, 255),
        padding: Tuple[int, int, int, int] = (0, 0, 0, 0),
        override_size: Optional[Tuple[Optional[int], Optional[int]]] = None,
    ) -> None:
        self.__alpha_composite_array: List[Tuple] = []
        self.__paste_array: List[Tuple] = []
        self.__used_height = override_size[1] if override_size and override_size[1] else 0
        self.__used_width = override_size[0] if override_size and override_size[0] else 0
        self.color = color
        self.padding = padding
        self.override_size = override_size
        self.__last_operate_image_address = None

    def alpha_composite(self, im: Image.Image, dest: Tuple[int, int], *args, **kw) -> None:
        self.__alpha_composite_array.append((im, dest, args, kw))
        self.__used_width = max(dest[0] + im.width, self.__used_width)
        self.__used_height = max(dest[1] + im.height, self.__used_height)
        self.__last_operate_image_address = 0, len(self.__alpha_composite_array) - 1

    def paste(self, im: Image.Image, box: Tuple[int, int], mask: Optional[Image.Image] = None, *args, **kw) -> None:
        self.__paste_array.append((im, box, mask, args, kw))
        self.__used_width = max(box[0] + im.width, self.__used_width)
        self.__used_height = max(box[1] + im.height, self.__used_height)
        self.__last_operate_image_address = 1, len(self.__paste_array) - 1

    def center(self, image: Image.Image) -> Tuple[int, int]:
        return round((self.use_width - image.width) / 2), round((self.__used_height - image.height) / 2)

    def generate(self) -> Image.Image:
        """
        生成最终图像
        注意  只能生成一次  否则会引发Operation on closed image错误

        :return: 最终生成的图像
        """
        result_image = Image.new("RGBA", self.size, self.color)
        for i in self.__alpha_composite_array:
            result_image.alpha_composite(i[0], (i[1][0] + self.padding[0], i[1][1] + self.padding[1]), *i[2], **i[3])
            i[0].close()
        for i in self.__paste_array:
            result_image.paste(i[0], (i[1][0] + self.padding[0], i[1][1] + self.padding[1]), i[2], *i[3], **i[4])
            i[0].close()
        return result_image

    def debug(self) -> None:
        result_image = Image.new("RGBA", (self.use_width, self.use_height), (128, 128, 128))
        for i in self.__alpha_composite_array:
            result_image.alpha_composite(i[0], i[1], *i[2], **i[3])
        for i in self.__paste_array:
            result_image.paste(i[0], i[1], i[2], *i[3], **i[4])
        result_image.show()

    @property
    def size(self) -> Tuple[int, int]:
        ret_size = self.__used_width + self.padding[0] + self.padding[2], self.__used_height + self.padding[1] + self.padding[3]
        if self.override_size:
            if self.override_size[0] is not None:
                ret_size = self.override_size[0] + self.padding[0] + self.padding[2], ret_size[1]
            if self.override_size[1] is not None:
                ret_size = ret_size[0], self.override_size[1] + self.padding[1] + self.padding[3]
        return ret_size

    @property
    def use_height(self) -> int:
        return self.__used_height

    @property
    def use_width(self) -> int:
        return self.__used_width

    @property
    def height(self) -> int:
        return self.size[1]

    @property
    def width(self) -> int:
        return self.size[0]

    @property
    def last_operate_object(self) -> Image.Image:
        if not self.__last_operate_image_address:
            raise AttributeError("Instance have no operation since created")
        if self.__last_operate_image_address[0] == 0:
            return self.__alpha_composite_array[self.__last_operate_image_address[1]][0]
        if self.__last_operate_image_address[0] == 1:
            return self.__paste_array[self.__last_operate_image_address[1]][0]
        raise IndexError("Unknown operation type flag")


def get_font_image(text: str, size: int, color: Tuple[int, int, int] = (0, 0, 0)) -> Image.Image:
    if "\n" in text:
        return get_font_image_vertical(text, size, color)
    image_font = ImageFont.truetype(FONTS, size)
    font_box = image_font.getbbox(text=text)
    background = Image.new("RGBA", (font_box[2] - font_box[0], font_box[3] - font_box[1]), (255, 255, 255, 0))
    background_draw = ImageDraw.Draw(background)
    background_draw.text((-font_box[0], -font_box[1]), text=text, font=image_font, fill=color)
    return background


def get_font_image_vertical(text: str, size: int, color: Tuple[int, int, int] = (0, 0, 0)) -> Image.Image:
    VERTICAL_PIXEL = round(size / 3)
    background = BackGroundGenerator(color=(255, 255, 255, 0))
    current_height = 0
    for i in text.split("\n"):
        background.alpha_composite(get_font_image(i, size, color), (0, current_height))
        current_height = background.height + VERTICAL_PIXEL
    return background.generate()


def center(source_image: Image.Image, target_image: Image.Image) -> Tuple[int, int]:
    result = [0, 0]
    target_image_box = target_image.getbbox()
    if target_image_box is None:
        return (0, 0)
    boxes = (source_image.size, target_image_box[2:])
    for i in range(2):
        result[i] = round((boxes[0][i] - boxes[1][i]) / 2)
    return tuple(result)


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
        circle_split = (circle_bg.crop((0, 0, circle_split_cursor_x, size)), circle_bg.crop((circle_split_cursor_x, 0, size, size)))

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


def user_chips(head_icon: Image.Image, user_name: str, background_color: Tuple[int, int, int] = (189, 189, 189)) -> Image.Image:
    OVERALL_CHIPS_LIST_WITH = 400 - 10  # 左右各5边距
    CHIPS_LIST_WIDTH = OVERALL_CHIPS_LIST_WITH - 29
    TEXT_MAXIMUM_WIDTH = CHIPS_LIST_WIDTH - 35  # 25为chip本身  10为chip自己外边距以及user_chips外边距
    USER_PROFILE_SIZE = 20
    USER_NICKNAME_FONTSIZE = 20
    CHIPS_HEIGHT = 20

    head_icon = head_icon.resize((USER_PROFILE_SIZE, USER_PROFILE_SIZE))
    head_icon = round_corner(head_icon)

    text_color = (255, 255, 255) if ((background_color[0] * 0.299 + background_color[1] * 0.587 + background_color[2] * 0.114) / 255) < 0.5 else (0, 0, 0)

    user_name_image = get_font_image(user_name, USER_NICKNAME_FONTSIZE, text_color)

    if user_name_image.width > TEXT_MAXIMUM_WIDTH:
        user_name_image = user_name_image.crop((0, 0, TEXT_MAXIMUM_WIDTH, CHIPS_HEIGHT))

    background = BackGroundGenerator(color=background_color, padding=(5, 5, 5, 5), override_size=(None, CHIPS_HEIGHT))
    background.alpha_composite(head_icon, (0, 0))
    if user_name_image.getbbox() is not None:
        background.alpha_composite(user_name_image, (25, background.center(user_name_image)[1]))

    return round_corner(background.generate())


def smaller_search(array: List[int], key, seek_map_array: Optional[List[int]] = None) -> Optional[int]:
    """
    使用二分查找法搜索目标对象的下标
    二分查找法变种  因为查找的不是全等于key的值

    :param array: 输入列表(必须有序且降序)
    :param key: 目标数值
    :param seek_map_array: 用于递归时传递下标map列表
    :result: array中小于key的最大值下标
    """
    if array[-1] > key:
        return None
    length = len(array)
    if not seek_map_array:
        seek_map_array = [i for i in range(length)]
    if length == 1:
        return seek_map_array[0]
    if length == 2:
        return seek_map_array[0] if array[0] < key else seek_map_array[1]

    half_seek = int(length / 2)

    if array[half_seek] < key:
        return smaller_search(array[: half_seek + 1], key, seek_map_array[: half_seek + 1])  # 中位数比key小  目标一定在左边  需要包含中位数本身
    else:
        return smaller_search(array[half_seek + 1 :], key, seek_map_array[half_seek + 1 :])  # 中位数比key大  目标一定在右边  不包含中位数本身


def chips_list_sort(source_list: List[int], target_num: int, interval: int) -> List[List[int]]:
    """
    用户 chips 排版算法
    以从长到短chip为基础不断与短到长的chip匹配并添加  直至行宽超过最大值后换行
    """

    result_seek_list: List[List[int]] = []  # 存储输出结果(下标) [行号][chips 列号]
    __address_map_list: List[int] = [i for i in range(len(source_list))]  # 存储结果对应下标

    while source_list:
        result_seek_list.append([])
        result_seek_list[-1].append(__address_map_list[0])  # 从长(前)到短(后)
        current_width = source_list[0] + interval

        source_list.pop(0)
        __address_map_list.pop(0)

        if not source_list:  # 没有待处理的chip了
            break
        if current_width + source_list[-1] > target_num:  # 这一行(当前待处理队列最长)的chip加上最短(索引最大)的chip已经超过行宽了  需要独占一行
            continue

        while (current_width < target_num) and source_list:  # 在待处理队列不为空且已使用的行宽不超过最大行宽前  不断从长到短添加chip
            target_seek = smaller_search(source_list, target_num - current_width)
            if target_seek is None:
                break
            result_seek_list[-1].append(__address_map_list[target_seek])
            current_width += source_list[target_seek] + interval  # 记录这个chip宽及间距

            source_list.pop(target_seek)
            __address_map_list.pop(target_seek)

            if not source_list:  # 没有待处理的chip了
                break
            if current_width + source_list[-1] > target_num:  # 这一行(当前待处理队列最长)的chip加上最短(索引最大)的chip已经超过行宽了  这一行已经完全没法放置新chip了
                break
    return result_seek_list


def chips_list(chips_array: Dict[str, Any] = {}, text: str = "内容", background_color: Tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
    global glovar_missing_user_id
    OVERALL_CHIPS_LIST_WITH = 400 - 10  # 左右各5边距
    CHIPS_LIST_WIDTH = OVERALL_CHIPS_LIST_WITH - 29
    CHIPS_INTERVAL = 5
    CHIPS_MINIMUM_HEIGHT = 65

    background_color = chips_array.pop("style-background-color", background_color)
    chips_color = chips_array.pop("style-chips-color", (189, 189, 189))
    text_color = (255, 255, 255) if ((background_color[0] * 0.299 + background_color[1] * 0.587 + background_color[2] * 0.114) / 255) < 0.5 else (0, 0, 0)
    # text_color = chips_array.get("style-text-color", text_color)

    text_image = get_font_image("\n".join([i for i in text]), 24, text_color)

    if not chips_array:
        background = BackGroundGenerator(color=background_color, override_size=(OVERALL_CHIPS_LIST_WITH, CHIPS_MINIMUM_HEIGHT), padding=(5, 5, 5, 5))
        background.alpha_composite(text_image, (0, background.center(text_image)[1]))
        text_image = get_font_image(f"暂无{text}", 24, text_color)
        background.alpha_composite(text_image, background.center(text_image))
        return round_corner(background.generate(), 5)

    chips_image_list = []
    for user_id, user_nickname in chips_array.items():
        if not user_id.isdigit():
            continue
        if not isinstance(user_nickname, str):
            continue
        user_profile_path = USER_HEADERS_PATH.joinpath(user_id + ".jpg")
        if not user_profile_path.is_file():
            user_profile_image = Image.new("RGBA", (20, 20), (255, 255, 255, 0))  # 已确保关闭
            glovar_missing_user_id.add(int(user_id))
        else:
            user_profile_image = Image.open(USER_HEADERS_PATH.joinpath(user_id + ".jpg"), "r")  # 已确保关闭
        chips_image_list.append(user_chips(user_profile_image, user_nickname, chips_color))

    chips_image_list.sort(key=lambda i: i.width, reverse=True)

    chips_sort_seek_list = chips_list_sort(
        source_list=list(map(lambda i: i.width, chips_image_list)),
        interval=5,
        target_num=CHIPS_LIST_WIDTH,
    )  # 排序chips

    chips_background = BackGroundGenerator(color=background_color)
    this_height = 0
    this_width = 0
    for this_chips_line_seeks in chips_sort_seek_list:
        if not this_chips_line_seeks:
            continue
        for this_chip_image_seek in this_chips_line_seeks:
            chips_background.alpha_composite(chips_image_list[this_chip_image_seek], (this_width, this_height))
            this_width += chips_image_list[this_chip_image_seek].width + CHIPS_INTERVAL
        this_height += 30 + CHIPS_INTERVAL
        this_width = 0

    background = BackGroundGenerator(color=background_color, padding=(5, 5, 5, 5), override_size=(OVERALL_CHIPS_LIST_WITH, None))
    background.alpha_composite(Image.new("RGBA", (1, CHIPS_MINIMUM_HEIGHT), (255, 255, 255, 0)), (0, 0))  # 限制最小chips list大小  已确保关闭
    background.alpha_composite(chips_background.generate(), (29, 0))
    background.alpha_composite(text_image, (0, background.center(text_image)[1]))
    # text_image.show()  ### 侧边文字调试 ###
    # background.debug()  ### chips list 调试(带侧边文字) ###
    return round_corner(background.generate(), 5)


class GroupStateBlock:
    def __init__(
        self,
        title_text: str,
        data_text: str,
        title_color: Tuple[int, int, int],
        data_color: Tuple[int, int, int],
        background_color: Tuple[int, int, int],
    ) -> None:
        self.title_text = title_text
        self.data_text = data_text
        self.title_color = title_color
        self.data_color = data_color
        self.background_color = background_color


def get_process_image(data: List[GroupStateBlock], chips_array: Dict[str, Dict[str, str]]):
    overall_image = BackGroundGenerator(color=(254, 251, 234), padding=(10, 10, 10, 10), override_size=(400, None))
    current_w, current_h = 0, 0
    for i in data:
        temp_background = BackGroundGenerator(padding=(10, 10, 10, 10), color=i.background_color)
        temp_background.alpha_composite(get_font_image(i.title_text, 28, i.title_color), (0, 0))
        data_image = get_font_image(i.data_text, 28, i.data_color)
        temp_background.alpha_composite(data_image, (temp_background.center(data_image)[0], temp_background.use_height + 10))

        if current_w + temp_background.width > 420:
            current_w = 0
            current_h = overall_image.use_height + 10

        overall_image.alpha_composite(round_corner(temp_background.generate(), 5), (current_w, current_h))
        current_w += temp_background.width + 10

    current_h = overall_image.use_height + 10
    for this_chips_list in chips_array:
        chips_list_image = chips_list(chips_array[this_chips_list], this_chips_list)
        overall_image.alpha_composite(chips_list_image, (0, current_h))
        current_h += chips_list_image.height + 10

    return overall_image.generate()


class BossStatusImageCore:
    def __init__(
        self,
        boss_round: int,
        current_hp: int,
        max_hp: int,
        name: str,
        boss_icon_id: str,
        extra_chips_array: Dict[str, Dict[str, Any]],
        is_next: bool,
    ) -> None:
        self.current_hp = current_hp
        self.max_hp = max_hp
        self.round = boss_round
        self.name = name
        self.boss_icon_id = boss_icon_id
        self.extra_chips_array = extra_chips_array
        self.is_next = is_next

    def hp_percent_image(self) -> Image.Image:
        HP_PERCENT_IMAGE_SIZE = (315, 24)
        background = Image.new("RGBA", HP_PERCENT_IMAGE_SIZE, (200, 200, 200))  # 已确保关闭
        background_draw = ImageDraw.Draw(background, "RGBA")
        percent_pixel_cursor_x = round(self.current_hp / self.max_hp * HP_PERCENT_IMAGE_SIZE[0])
        background_draw.rectangle((0, 0, percent_pixel_cursor_x, HP_PERCENT_IMAGE_SIZE[1]), (255, 0, 0))

        text_str = f"{self.current_hp} / {self.max_hp}"
        text_image_white = get_font_image(text_str, 20, (255, 255, 255))
        text_image_black = get_font_image(text_str, 20)
        text_paste_center_start_cursor = center(background, text_image_white)
        text_image = Image.new("RGBA", text_image_white.size)  # 已确保关闭
        seek_in_text_image = percent_pixel_cursor_x - text_paste_center_start_cursor[0] + 1
        if seek_in_text_image <= 0:
            text_image = text_image_black
        elif seek_in_text_image >= text_image_white.width:
            text_image = text_image_white
        else:
            text_image.alpha_composite(
                text_image_white.crop((0, 0, seek_in_text_image, text_image_white.size[1])),
                dest=(0, 0),
            )
            text_image.alpha_composite(
                text_image_black.crop((seek_in_text_image, 0, *text_image_black.size)),
                dest=(seek_in_text_image, 0),
            )
        background.alpha_composite(text_image, text_paste_center_start_cursor)

        text_image.close()

        return round_corner(background)

    def cycle_round_image(self) -> Image.Image:
        CYCLE_TEXT_SIZE = 23
        CYCLE_IMAGE_HEIGHT = 26

        text_str = f"{self.round} 周目"
        text_image = get_font_image(text_str, CYCLE_TEXT_SIZE, (255, 255, 255))
        color_code = (106, 152, 243, 255) if self.is_next else (228, 94, 104, 255)
        background = Image.new("RGBA", (text_image.width + CYCLE_IMAGE_HEIGHT, CYCLE_IMAGE_HEIGHT), color_code)  # 已确保关闭
        background.alpha_composite(text_image, center(background, text_image))
        return round_corner(background)

    def boss_panel_image(self) -> Image.Image:
        BOSS_HEADER_SIZE = 75
        background = BackGroundGenerator(color=(255, 255, 255, 0))
        boss_name_image = get_font_image(self.name, 24)
        background.alpha_composite(boss_name_image, (BOSS_HEADER_SIZE + 10, round((26 - boss_name_image.height) / 2)))
        background.alpha_composite(self.cycle_round_image(), (BOSS_HEADER_SIZE + 20 + boss_name_image.width, 0))
        background.alpha_composite(self.hp_percent_image(), (BOSS_HEADER_SIZE + 10, 75 - 24))

        if not BOSS_ICON_PATH.joinpath(self.boss_icon_id + ".webp").is_file():
            boss_icon = Image.new("RGBA", (128, 128), (255, 255, 255, 0))  # 已确保关闭
        else:
            boss_icon = Image.open(BOSS_ICON_PATH.joinpath(self.boss_icon_id + ".webp"), "r")  # 已确保关闭

        boss_icon = boss_icon.resize((BOSS_HEADER_SIZE, BOSS_HEADER_SIZE))
        boss_icon = round_corner(boss_icon, 10)
        background.alpha_composite(boss_icon, (0, 0))
        # background.debug()  ### boss面板调试 ###
        return background.generate()

    def generate(self, background_color: Tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
        background = BackGroundGenerator(color=background_color, padding=(10, 10, 10, 10))
        background.alpha_composite(self.boss_panel_image(), (0, 0))
        current_chips_height = background.use_height + 10
        for this_chips_list in self.extra_chips_array:
            #print(this_chips_list)
            #print(self.extra_chips_array[this_chips_list])
            chips_list_image = chips_list(self.extra_chips_array[this_chips_list], this_chips_list)
            background.alpha_composite(chips_list_image, (0, current_chips_height))
            current_chips_height += chips_list_image.height + 10
        # background.debug()
        return background.generate()


def makeShadow(image: Image.Image, iterations: int, border: int, offset: Tuple[int, int], backgroundColour, shadowColour):
    # https://en.wikibooks.org/wiki/Python_Imaging_Library/Drop_Shadows
    # image: base image to give a drop shadow
    # iterations: number of times to apply the blur filter to the shadow
    # border: border to give the image to leave space for the shadow
    # offset: offset of the shadow as [x,y]
    # backgroundCOlour: colour of the background
    # shadowColour: colour of the drop shadow

    # Calculate the size of the shadow's image
    fullWidth = image.size[0] + abs(offset[0]) + 2 * border
    fullHeight = image.size[1] + abs(offset[1]) + 2 * border

    # Create the shadow's image. Match the parent image's mode.
    shadow = Image.new(image.mode, (fullWidth, fullHeight), backgroundColour)

    # Place the shadow, with the required offset
    shadowLeft = border + max(offset[0], 0)  # if <0, push the rest of the image right
    shadowTop = border + max(offset[1], 0)  # if <0, push the rest of the image down
    # Paste in the constant colour
    shadow.paste(shadowColour, [shadowLeft, shadowTop, shadowLeft + image.size[0], shadowTop + image.size[1]])

    # Apply the BLUR filter repeatedly
    for i in range(iterations):
        shadow = shadow.filter(ImageFilter.BLUR)

    # shadow.show()

    # Paste the original image on top of the shadow
    imgLeft = border - min(offset[0], 0)  # if the shadow offset was <0, push right
    imgTop = border - min(offset[1], 0)  # if the shadow offset was <0, push down
    shadow.alpha_composite(image, (imgLeft, imgTop))

    image.close()

    return shadow


def generate_combind_boss_state_image(image_list: List[Union[Image.Image, BossStatusImageCore]]) -> Image.Image:
    INTERVAL = 20
    SHADOW_BORDER = 5

    background = BackGroundGenerator(color=(248, 239, 200), padding=(20, 20, 20 - SHADOW_BORDER, 20 - SHADOW_BORDER))
    current_y_cursor = 0
    current_x_cursor = 0
    module_count = 0
    format_color_flag = False

    for this_image in image_list:
        if isinstance(this_image, BossStatusImageCore):
            this_image = this_image.generate((254, 251, 234))
            # this_image.show()
        elif isinstance(this_image, Image.Image):
            pass
        else:
            raise ValueError(f"Unknown image type: {type(this_image)}")

        background.alpha_composite(
            makeShadow(round_corner(this_image, 10), 1, SHADOW_BORDER, (5, 5), (248, 239, 200), (248 - 20, 239 - 20, 200 - 20)),
            # round_corner(this_image, 10),
            (current_x_cursor, current_y_cursor),
        )
        current_y_cursor += this_image.height + INTERVAL
        format_color_flag = not format_color_flag
        module_count += 1
        if module_count == 3:
            current_x_cursor += this_image.width + INTERVAL
            current_y_cursor = 0
            format_color_flag = True if format_color_flag else False

    return background.generate()


async def download_pic(url: str, proxies: Optional[str] = None, file_name="") -> Optional[Path]:
    image_path = USER_HEADERS_PATH.joinpath(file_name)
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
    global glovar_missing_user_id
    if not glovar_missing_user_id:
        return
    await download_user_profile_image(list(glovar_missing_user_id))
    glovar_missing_user_id = set()
