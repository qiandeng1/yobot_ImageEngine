import os
import string

from ..exception import GroupNotExist
from ...ybdata import Clan_challenge, Clan_group, Clan_member


FILE_PATH = os.path.dirname(__file__)

def is_Chinese(word):
	for ch in word:
		if '\u4e00' <= ch <= '\u9fff': return True

#业绩表
def score_table(self, group_id):
	'''
	通过当期数据给成员打分
	'''
	group:Clan_group = self.get_clan_group(group_id=group_id)
	if group is None:raise GroupNotExist

	members = Clan_member.select().where(
		Clan_member.group_id == group_id,
	)

	member_score_dict = {}
	for member in members:
		challenges = Clan_challenge.select().where(
			Clan_challenge.gid == group_id,
			Clan_challenge.bid == group.battle_id,
			Clan_challenge.qqid == member.qqid
		).order_by(Clan_challenge.challenge_pcrdate)
		challenges = list(challenges)
		if member.qqid not in member_score_dict:
			member_score_dict[member.qqid] = {
				'score' : 0,
				'full_blade' : 0,
				'end_blade' : 0,
				'small_end_blade' : 0,
			}

		full_blade = sum(bool(c.boss_health_remain and not c.is_continue) for c in challenges)
		for info in challenges:
			score, full_blade, end_blade, small_end_blade = 0, 0, 0, 0
			if info.boss_health_remain > 0 and not info.is_continue: 
				full_blade += 1
				score += 1
			elif info.boss_health_remain == 0 and not info.is_continue: 
				end_blade += 1
				if info.challenge_damage >= group.threshold: score += 1
				else: score += 0.5
			elif info.is_continue:
				small_end_blade += 1
				if info.challenge_damage >= group.threshold: score += 1
				else: score += 0.5
			score_member = info.behalf and info.behalf or member.qqid
			if score_member not in member_score_dict:
				member_score_dict[score_member] = {
					'score' : score, 
					'full_blade' : full_blade,
					'end_blade' : end_blade,
					'small_end_blade' : small_end_blade,
				}
			else:
				member_score_dict[score_member]['score'] += score
				member_score_dict[score_member]['full_blade'] += full_blade
				member_score_dict[score_member]['end_blade'] += end_blade
				member_score_dict[score_member]['small_end_blade'] += small_end_blade

	member_score_dict = dict(sorted(member_score_dict.items(), key=lambda item: item[1]['score'], reverse=True))
	back_msg = []
	for qqid, info in member_score_dict.items():
		name:string = list(self._get_nickname_by_qqid(qqid))
		while len(name) > 5:name.pop()
		a = ''
		if len(name) < 5:
			for i in range(5 - len(name)): a += ' '
			name.append(a)
		a = ''
		for i in name:
			if not is_Chinese(i): a += ' '
		back_msg.append(f"{''.join(name)}{a}     \
分数：{info['score']}     \
整刀：{info['full_blade']}     \
尾刀：{info['end_blade']}     \
小尾刀：{info['small_end_blade']}")

	return self.text_2_pic('\n'.join(back_msg), 450, len(back_msg)*20 + 10, (255, 255, 255), "#000000", 15, (10, 5))
