from typing import Dict, List
import json

from ...ybdata import Clan_group


class SubscribeHandler:
    def __init__(self, group: Clan_group) -> None:
        """
        预约系统处理核心

        :param group: Clan_group公会实例
        """
        """
        转换为方便处理内部的类型
        原始类型: Dict[str, Dict[str, str]] = {Boss编号: {预约QQ号: 留言}}
        目标类型: Dict[int, Dict[int, str]] = {Boss编号: {预约QQ号: 留言}}
        """
        if group.subscribe_list:
            data: Dict[str, Dict[str, str]] = json.loads(group.subscribe_list)
        else:
            data = {}
        new_data: Dict[int, Dict[int, str]] = {}
        for boss_no, boss_subscribe_data in data.items():
            new_boss_subscribe_data = {}
            for subscribe_qq, subscribe_note in boss_subscribe_data.items():
                new_boss_subscribe_data[int(subscribe_qq)] = subscribe_note
                new_data[int(boss_no)] = new_boss_subscribe_data
        self._data: Dict[int, Dict[int, str]] = new_data
        self._clan_group: Clan_group = group

    def subscribe(self, user_id: int, boss_id: int, note: str = "") -> None:
        """
        预约Boss

        :param user_id: QQ号
        :param boss_id: Boss编号
        :param note: 留言
        """
        if boss_id not in self._data:
            self._data[boss_id] = {}
        self._data[boss_id][user_id] = note

    def is_subscribed(self, user_id: int, boss_id: int) -> bool:
        """
        检查是否已预约过特定Boss

        :param user_id: QQ号
        :param boss_id: Boss编号
        :return: 是否预约了该Boss
        """
        if boss_id not in self._data:
            return False
        return user_id in self._data[boss_id]

    def unsubscribe(self, user_id: int, boss_id: int) -> None:
        self._data[boss_id].pop(user_id)
        if not self._data[boss_id]:  # 删除没有预约的Boss
            self._data.pop(boss_id)

    def unsubscribe_all(self, boss_id: int) -> None:
        """
        取消某个Boss的所有预约

        :param boss_id: Boss编号
        """
        if boss_id not in self._data:
            return
        self._data.pop(boss_id)

    def get_subscribe_list(self, boss_id: int) -> List[int]:
        """
        获取预约Boss的用户列表

        :param boss_id: Boss编号
        :return: 预约Boss的用户列表
        """
        if boss_id not in self._data:
            return []
        return list(self._data[boss_id].keys())

    def get_note(self, user_id: int, boss_id: int) -> str:
        if not self.is_subscribed(user_id, boss_id):
            return ""
        return self._data[boss_id][user_id]

    @property
    def have_subscribe(self) -> bool:
        """
        是否包含任何预约记录

        :return: 预约记录查询结果
        """
        return True if self._data else False

    @property
    def data(self) -> Dict[int, Dict[int, str]]:
        """
        获取预约数据

        :return: 预约数据
        """
        return dict(sorted(self._data.items(), key=lambda i: i[0]))

    def save(self) -> None:
        self._clan_group.subscribe_list = json.dumps(self._data)
        self._clan_group.save()
