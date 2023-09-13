import asyncio
import logging
from urllib.parse import urljoin

import peewee
from quart import Quart, jsonify, make_response, redirect, request, session, url_for

from ...templating import render_template
from ...ybdata import Clan_group, Clan_member, User
from ..exception import ClanBattleError
from ..util import pcr_datetime, atqq
from .multi_cq_utils import who_am_i

_logger = logging.getLogger(__name__)

def register_routes(self, app: Quart):
	@app.route(
		urljoin(self.setting['public_basepath'], 'clan/<int:group_id>/'),
		methods=['GET'])
	async def yobot_clan(group_id):
		if 'yobot_user' not in session:
			return redirect(url_for('yobot_login', callback=request.path))
		user = User.get_by_id(session['yobot_user'])
		group = self.get_clan_group(group_id=group_id)
		if group is None:
			return await render_template('404.html', item='公会'), 404
		is_member = Clan_member.get_or_none(
			group_id=group_id, qqid=session['yobot_user'])
		if (not is_member and user.authority_group >= 10):
			return await render_template('clan/unauthorized.html')
		return await render_template(
			'clan/panel.html',
			is_member=is_member,
		)

	@app.route(
		urljoin(self.setting['public_basepath'],
				'clan/<int:group_id>/subscribers/'),
		methods=['GET'])
	async def yobot_clan_subscribers(group_id):
		if 'yobot_user' not in session:
			return redirect(url_for('yobot_login', callback=request.path))
		user = User.get_by_id(session['yobot_user'])
		group = self.get_clan_group(group_id=group_id)
		if group is None:
			return await render_template('404.html', item='公会'), 404
		is_member = Clan_member.get_or_none(
			group_id=group_id, qqid=session['yobot_user'])
		if (not is_member and user.authority_group >= 10):
			return await render_template('clan/unauthorized.html')
		return await render_template(
			'clan/subscribers.html',
		)

	@app.route(
		urljoin(self.setting['public_basepath'],
				'clan/<int:group_id>/api/'),
		methods=['POST'])
	async def yobot_clan_api(group_id):
		group = self.get_clan_group(group_id=group_id)
		if group is None:
			return jsonify(
				code=20,
				message='Group not exists',
			)
		if 'yobot_user' not in session:
			if not(group.privacy & 0x1):
				return jsonify(
					code=10,
					message='Not logged in',
				)
			user_id = 0
		else:
			user_id = session['yobot_user']
			user = User.get_by_id(user_id)
			is_member = Clan_member.get_or_none(
				group_id=group_id, qqid=user_id)
			if (not is_member and user.authority_group >= 10):
				return jsonify(
					code=11,
					message='Insufficient authority',
				)
		try:
			payload = await request.get_json()
			if payload is None:
				return jsonify(
					code=30,
					message='Invalid payload',
				)
			if (user_id != 0) and (payload.get('csrf_token') != session['csrf_token']):
				return jsonify(
					code=15,
					message='Invalid csrf_token',
				)
			action = payload['action']
			if user_id == 0:
				# 允许游客查看
				if action not in ['get_member_list', 'get_challenge']:
					return jsonify(
						code=10,
						message='Not logged in',
					)
			if action == 'get_member_list':
				return jsonify(
					code=0,
					members=self.get_member_list(group_id),
				)
			elif action == 'get_data':
				return jsonify(
					code=0,
					groupData={
						'group_id': group.group_id,
						'group_name': group.group_name,
						'game_server': group.game_server,
						'cycle': group.boss_cycle,
					},
					bossData=self._boss_data_dict(group),
					base_cycle = group.boss_cycle,
					selfData={
						'is_admin': (is_member and user.authority_group < 100),
						'user_id': user_id,
					}
				)
			elif action == 'update_boss_data':
				return jsonify(
					code = 0,
					bossData = self._boss_data_dict(group),
					base_cycle = group.boss_cycle,
				)
			elif action == 'get_challenge':
				d, _ = pcr_datetime(group.game_server)
				report = self.get_report(
					group_id,
					None,
					None,
					pcr_datetime(group.game_server, payload['ts'])[0],
				)
				return jsonify(
					code=0,
					challenges=report,
					today=d,
				)
			elif action == 'get_user_challenge':
				report = self.get_report(
					group_id,
					None,
					payload['qqid'],
					None,
				)
				try:
					visited_user = User.get_by_id(payload['qqid'])
				except peewee.DoesNotExist:
					return jsonify(code=20, message='user not found')
				return jsonify(
					code=0,
					challenges=report,
					game_server=group.game_server,
					user_info={
						'qqid': payload['qqid'],
						'nickname': visited_user.nickname,
					}
				)
			elif action == 'update_boss':
				try:
					bossData, base_cycle, notice = await asyncio.wait_for(
						asyncio.shield(
							self._boss_status[group_id]),
							timeout=30
						)
					return jsonify(
						code = 0,
						bossData = bossData,
						base_cycle = base_cycle,
						notice = notice,
					)
				except asyncio.TimeoutError:
					return jsonify(
						code=1,
						message='not changed',
					)
			elif action == 'addrecord':
				try:
					status = self.challenge(group_id, user_id,
					payload['defeat'],
					payload['damage'],
					payload['behalf'],
					payload['is_continue'],
					boss_num = payload['boss_num'])
				except ClanBattleError as e:
					_logger.info('网页 失败 {} {} {}'.format(
						user_id, group_id, action))
					return jsonify(
						code=10,
						message=str(e),
					)
				_logger.info('网页 成功 {} {} {}'.format(
					user_id, group_id, action))
				if group.notification & 0x01:
					asyncio.ensure_future(
						self.api.send_group_msg(
							self_id = who_am_i(group_id),
							group_id=group_id,
							message=str(status),
						)
					)
				return jsonify(
					code=0,
					bossData=self._boss_data_dict(group),
				)
			elif action == 'undo':
				try:
					status = self.undo(group_id, user_id)
				except ClanBattleError as e:
					_logger.info('网页 失败 {} {} {}'.format(
						user_id, group_id, action))
					return jsonify(
						code=10,
						message=str(e),
					)
				_logger.info('网页 成功 {} {} {}'.format(
					user_id, group_id, action))
				if group.notification & 0x02:
					asyncio.ensure_future(
						self.api.send_group_msg(
							self_id = who_am_i(group_id),
							group_id=group_id,
							message=str(status),
						)
					)
				return jsonify(
					code=0,
					bossData=self._boss_data_dict(group),
				)
			elif action == 'apply':
				try:
					is_continue = payload['is_continue']
					behalf = payload['behalf']
					boss_num = payload['boss_num']
					if behalf == user_id: behalf = None
					status = self.apply_for_challenge(is_continue, group_id, user_id, boss_num, behalf)
				except ClanBattleError as e:
					_logger.info('网页 失败 {} {} {}'.format(user_id, group_id, action))
					return jsonify(
						code=10,
						message=str(e),
					)
				_logger.info('网页 成功 {} {} {}'.format(user_id, group_id, action))
				if group.notification & 0x04:
					asyncio.ensure_future(
						self.api.send_group_msg(
							self_id = who_am_i(group_id),
							group_id = group_id,
							message = atqq(behalf)+status,
						)
					)
				return jsonify(
					code = 0,
					bossData = self._boss_data_dict(group),
				)
			elif action == 'cancelapply':
				try:
					behalf = payload['behalf'] and int(payload['behalf']) or user_id
					status = self.cancel_blade(group_id, behalf)
				except ClanBattleError as e:
					_logger.info('网页 失败 {} {} {}'.format(user_id, group_id, action))
					return jsonify(code=10, message=str(e))
				_logger.info('网页 成功 {} {} {}'.format(user_id, group_id, action))
				if group.notification & 0x08:
					asyncio.ensure_future(
						self.api.send_group_msg(
							self_id = who_am_i(group_id),
							group_id = group_id,
							message = atqq(behalf)+status,
						)
					)
				return jsonify(
					code=0,
					bossData=self._boss_data_dict(group),
				)
			elif action == 'put_on_the_tree':
				try:
					behalf = payload['behalf'] and int(payload['behalf']) or user_id
					status = self.put_on_the_tree(group_id, behalf)
				except ClanBattleError as e:
					_logger.info('网页 失败 {} {} {}'.format(user_id, group_id, action))
					return jsonify(code=10, message=str(e))
				_logger.info('网页 成功 {} {} {}'.format(user_id, group_id, action))
				if group.notification & 0x08:
					asyncio.ensure_future(
						self.api.send_group_msg(
							self_id = who_am_i(group_id),
							group_id = group_id,
							message = atqq(behalf)+status,
						)
					)
				return jsonify(
					code=0,
					bossData=self._boss_data_dict(group),
				)
			elif action == 'take_it_of_the_tree':
				try:
					behalf = payload['behalf'] and int(payload['behalf']) or user_id
					status = self.take_it_of_the_tree(group_id, behalf)
				except ClanBattleError as e:
					_logger.info('网页 失败 {} {} {}'.format(user_id, group_id, action))
					return jsonify(code=10, message=str(e))
				_logger.info('网页 成功 {} {} {}'.format(user_id, group_id, action))
				if group.notification & 0x08:
					asyncio.ensure_future(
						self.api.send_group_msg(
							self_id = who_am_i(group_id),
							group_id = group_id,
							message = atqq(behalf)+status,
						)
					)
				return jsonify(
					code=0,
					bossData=self._boss_data_dict(group),
				)
			elif action == 'save_slot':
				sl_member_qqid = payload['member']
				status = payload['status']
				try:
					self.save_slot(group_id, sl_member_qqid, clean_flag = not status)
				except ClanBattleError as e:
					_logger.info('网页 失败 {} {} {}'.format(user_id, group_id, action))
					return jsonify(
						code=10,
						message=str(e),
					)
				sw = '添加' if status else '取消'
				_logger.info('网页 成功 {} {} {}'.format(user_id, group_id, action))
				if group.notification & 0x200:
					asyncio.ensure_future(
						self.api.send_group_msg(
							self_id = who_am_i(group_id),
							group_id=group_id,
							message=(self._get_nickname_by_qqid(sl_member_qqid) + f'已{sw}SL记录'),
						)
					)
				return jsonify(code=0, notice=f'已{sw}SL记录')
			elif action == 'get_subscribers':
				subscribers = self.get_subscribe_list(group_id)
				return jsonify(
					code=0,
					group_name=group.group_name,
					subscribers=subscribers)
			elif action == 'add_subscribe':
				boss_num = payload['boss_num']
				message = payload.get('message')
				try:self.subscribe(group_id, user_id, str(boss_num), message)
				except ClanBattleError as e:
					_logger.info('网页 失败 {} {} {}'.format(user_id, group_id, action))
					return jsonify(code = 10, message = str(e))
				_logger.info('网页 成功 {} {} {}'.format(user_id, group_id, action))
				notice = '预约成功'
				if group.notification & 0x40:
					notice_message = '{}已预约{}号boss'.format(
						user.nickname,
						boss_num,
					)
					if message: notice_message += '\n留言：' + message
					asyncio.ensure_future(
						self.api.send_group_msg(
							self_id = who_am_i(group_id),
							group_id = group_id,
							message = notice_message,
						)
					)
				return jsonify(code=0, notice=notice)
			elif action == 'cancel_subscribe':
				boss_num = payload['boss_num']
				try:self.subscribe_cancel(group_id, str(boss_num), user_id)
				except ClanBattleError as e:
					_logger.info('网页 失败 {} {} {}'.format(user_id, group_id, action))
					return jsonify(code = 10, message = str(e))
				_logger.info('网页 成功 {} {} {}'.format(user_id, group_id, action))
				notice = '取消预约成功'
				if group.notification & 0x80:
					asyncio.ensure_future(
						self.api.send_group_msg(
							self_id = who_am_i(group_id),
							group_id = group_id,
							message = '{}已取消预约{}号boss'.format(user.nickname, boss_num),
						)
					)
				return jsonify(code = 0, notice = notice)
			elif action == 'modify':
				if user.authority_group >= 100:
					return jsonify(code=11, message='Insufficient authority')
				try:
					status = self.modify(
						group_id,
						cycle=payload['cycle'],
						bossData=payload['bossData'],
					)
				except ClanBattleError as e:
					_logger.info('网页 失败 {} {} {}'.format(
						user_id, group_id, action))
					return jsonify(code=10, message=str(e))
				_logger.info('网页 成功 {} {} {}'.format(
					user_id, group_id, action))
				if group.notification & 0x100:
					asyncio.ensure_future(
						self.api.send_group_msg(
							self_id = who_am_i(group_id),
							group_id=group_id,
							message=str(status),
						)
					)
				return jsonify(
					code=0,
					bossData=self._boss_data_dict(group),
				)
			elif action == 'send_remind':
				if user.authority_group >= 100:
					return jsonify(code=11, message='Insufficient authority')
				sender = user_id
				private = payload.get('send_private_msg', False)
				if private and not self.setting['allow_bulk_private']:
					return jsonify(
						code=12,
						message='私聊通知已禁用',
					)
				self.send_remind(group_id,
									payload['memberlist'],
									sender=sender,
									send_private_msg=private)
				return jsonify(
					code=0,
					notice='发送成功',
				)
			elif action == 'drop_member':
				if user.authority_group >= 100:
					return jsonify(code=11, message='Insufficient authority')
				count = self.drop_member(group_id, payload['memberlist'])
				return jsonify(
					code=0,
					notice=f'已删除{count}条记录',
				)
			else:
				return jsonify(code=32, message='unknown action')
		except KeyError as e:
			_logger.error(e)
			return jsonify(code=31, message=f'missing key: {str(e)}')
		except asyncio.CancelledError:
			pass
		except Exception as e:
			_logger.exception(e)
			return jsonify(code=40, message=f'server error, info:\n{str(e)}')

	@app.route(
		urljoin(self.setting['public_basepath'],
				'clan/<int:group_id>/my/'),
		methods=['GET'])
	async def yobot_clan_user_auto(group_id):
		if 'yobot_user' not in session:
			return redirect(url_for('yobot_login', callback=request.path))
		return redirect(url_for(
			'yobot_clan_user',
			group_id=group_id,
			qqid=session['yobot_user'],
		))

	@app.route(
		urljoin(self.setting['public_basepath'],
				'clan/<int:group_id>/<int:qqid>/'),
		methods=['GET'])
	async def yobot_clan_user(group_id, qqid):
		if 'yobot_user' not in session:
			return redirect(url_for('yobot_login', callback=request.path))
		user = User.get_by_id(session['yobot_user'])
		group = self.get_clan_group(group_id=group_id)
		if group is None:
			return await render_template('404.html', item='公会'), 404
		is_member = Clan_member.get_or_none(
			group_id=group_id, qqid=session['yobot_user'])
		if (not is_member and user.authority_group >= 10):
			return await render_template('clan/unauthorized.html')
		return await render_template(
			'clan/user.html',
			qqid=qqid,
		)

	@app.route(
		urljoin(self.setting['public_basepath'],
				'clan/<int:group_id>/setting/'),
		methods=['GET'])
	async def yobot_clan_setting(group_id):
		if 'yobot_user' not in session:
			return redirect(url_for('yobot_login', callback=request.path))
		user = User.get_by_id(session['yobot_user'])
		group = self.get_clan_group(group_id=group_id)
		if group is None:
			return await render_template('404.html', item='公会'), 404
		is_member = Clan_member.get_or_none(
			group_id=group_id, qqid=session['yobot_user'])
		if (not is_member):
			return await render_template(
				'unauthorized.html',
				limit='本公会成员',
				uath='无')
		if (user.authority_group >= 100):
			return await render_template(
				'unauthorized.html',
				limit='公会战管理员',
				uath='成员')
		return await render_template('clan/setting.html')

	@app.route(
		urljoin(self.setting['public_basepath'],
				'clan/<int:group_id>/setting/api/'),
		methods=['POST'])
	async def yobot_clan_setting_api(group_id):
		if 'yobot_user' not in session:
			return jsonify(
				code=10,
				message='Not logged in',
			)
		user_id = session['yobot_user']
		user = User.get_by_id(user_id)
		group = self.get_clan_group(group_id=group_id)
		if group is None:
			return jsonify(
				code=20,
				message='Group not exists',
			)
		is_member = Clan_member.get_or_none(
			group_id=group_id, qqid=session['yobot_user'])
		if (user.authority_group >= 100 or not is_member):
			return jsonify(
				code=11,
				message='Insufficient authority',
			)
		try:
			payload = await request.get_json()
			if payload is None:
				return jsonify(
					code=30,
					message='Invalid payload',
				)
			if payload.get('csrf_token') != session['csrf_token']:
				return jsonify(
					code=15,
					message='Invalid csrf_token',
				)
			action = payload['action']
			if action == 'get_setting':
				return jsonify(
					code=0,
					groupData={
						'group_name': group.group_name,
						'game_server': group.game_server,
						'battle_id': group.battle_id,
					},
					privacy=group.privacy,
					notification=group.notification,
				)
			elif action == 'put_setting':
				group.game_server = payload['game_server']
				group.notification = payload['notification']
				group.privacy = payload['privacy']
				group.save()
				_logger.info('网页 成功 {} {} {}'.format(
					user_id, group_id, action))
				return jsonify(code=0, message='success')
			elif action == 'get_data_slot_record_count':
				counts = self.get_data_slot_record_count(group_id)
				_logger.info('网页 成功 {} {} {}'.format(
					user_id, group_id, action))
				return jsonify(code=0, message='success', counts=counts)
			elif action == 'clear_data_slot':
				battle_id = payload.get('battle_id')
				self.clear_data_slot(group_id, battle_id)
				_logger.info('网页 成功 {} {} {}'.format(
					user_id, group_id, action))
				return jsonify(code=0, message='success')
			elif action == 'switch_data_slot':
				battle_id = payload['battle_id']
				self.switch_data_slot(group_id, battle_id)
				_logger.info('网页 成功 {} {} {}'.format(
					user_id, group_id, action))
				return jsonify(code=0, message='success')
			else:
				return jsonify(code=32, message='unknown action')
		except KeyError as e:
			_logger.error(e)
			return jsonify(code=31, message=f'missing key: {str(e)}')
		except Exception as e:
			_logger.exception(e)
			return jsonify(code=40, message=f'server error, info:\n{str(e)}')

	@app.route(
		urljoin(self.setting['public_basepath'],
				'clan/<int:group_id>/statistics/'),
		methods=['GET'])
	async def yobot_clan_statistics(group_id):
		if 'yobot_user' not in session:
			return redirect(url_for('yobot_login', callback=request.path))
		user = User.get_by_id(session['yobot_user'])
		group = self.get_clan_group(group_id=group_id)
		if group is None:
			return await render_template('404.html', item='公会'), 404
		is_member = Clan_member.get_or_none(
			group_id=group_id, qqid=session['yobot_user'])
		if (not is_member and user.authority_group >= 10):
			return await render_template('clan/unauthorized.html')
		return await render_template(
			'clan/statistics.html',
			allow_api=(group.privacy & 0x2),
			apikey=group.apikey,
		)

	@app.route(
		urljoin(self.setting['public_basepath'],
				'clan/<int:group_id>/statistics/<int:sid>/'),
		methods=['GET'])
	async def yobot_clan_boss(group_id, sid):
		if 'yobot_user' not in session:
			return redirect(url_for('yobot_login', callback=request.path))
		user = User.get_by_id(session['yobot_user'])
		group = self.get_clan_group(group_id=group_id)
		if group is None:
			return await render_template('404.html', item='公会'), 404
		is_member = Clan_member.get_or_none(
			group_id=group_id, qqid=session['yobot_user'])
		if (not is_member and user.authority_group >= 10):
			return await render_template('clan/unauthorized.html')
		return await render_template(
			f'clan/statistics/statistics{sid}.html',
		)

	@app.route(
		urljoin(self.setting['public_basepath'],
				'clan/<int:group_id>/statistics/api/'),
		methods=['GET'])
	async def yobot_clan_statistics_api(group_id):
		group = self.get_clan_group(group_id=group_id)
		if group is None:
			return jsonify(code=20, message='Group not exists')
		apikey = request.args.get('apikey')
		if apikey:
			# 通过 apikey 外部访问
			if not (group.privacy & 0x2):
				return jsonify(code=11, message='api not allowed')
			if apikey != group.apikey:
				return jsonify(code=12, message='Invalid apikey')
		else:
			# 内部直接访问
			if 'yobot_user' not in session:
				return jsonify(code=10, message='Not logged in')
			user = User.get_by_id(session['yobot_user'])
			is_member = Clan_member.get_or_none(
				group_id=group_id, qqid=session['yobot_user'])
			if (not is_member and user.authority_group >= 10):
				return jsonify(code=11, message='Insufficient authority')
		battle_id = request.args.get('battle_id')
		if battle_id is None:
			pass
		else:
			if battle_id.isdigit():
				battle_id = int(battle_id)
			elif battle_id == 'all':
				pass
			elif battle_id == 'current':
				battle_id = None
			else:
				return jsonify(code=20, message=f'unexceptd value "{battle_id}" for battle_id')
		report = self.get_report(group_id, battle_id, None, None)
		member_list = self.get_battle_member_list(group_id, battle_id)
		groupinfo = {
			'group_id': group.group_id,
			'group_name': group.group_name,
			'game_server': group.game_server,
			'battle_id': group.battle_id,
		},
		response = await make_response(jsonify(
			code=0,
			message='OK',
			api_version=1,
			challenges=report,
			groupinfo=groupinfo,
			members=member_list,
		))
		if (group.privacy & 0x2):
			response.headers['Access-Control-Allow-Origin'] = '*'
		return response

	@app.route(
		urljoin(self.setting['public_basepath'],
				'clan/<int:group_id>/progress/'),
		methods=['GET'])
	async def yobot_clan_progress(group_id):
		group = self.get_clan_group(group_id=group_id)
		if group is None:
			return await render_template('404.html', item='公会'), 404
		if not(group.privacy & 0x1):
			if 'yobot_user' not in session:
				return redirect(url_for('yobot_login', callback=request.path))
			user = User.get_by_id(session['yobot_user'])
			is_member = Clan_member.get_or_none(
				group_id=group_id, qqid=session['yobot_user'])
			if (not is_member and user.authority_group >= 10):
				return await render_template('clan/unauthorized.html')
		return await render_template(
			'clan/progress.html',
		)

	@app.route(
		urljoin(self.setting['public_basepath'],
				'clan/<int:group_id>/clan-rank/'),
		methods=['GET'])
	async def yobot_clan_rank(group_id):
		group = self.get_clan_group(group_id=group_id)
		if group is None:
			return await render_template('404.html', item='公会'), 404
		if not(group.privacy & 0x1):
			if 'yobot_user' not in session:
				return redirect(url_for('yobot_login', callback=request.path))
			user = User.get_by_id(session['yobot_user'])
			is_member = Clan_member.get_or_none(
				group_id=group_id, qqid=session['yobot_user'])
			if (not is_member and user.authority_group >= 10):
				return await render_template('clan/unauthorized.html')
		return await render_template(
			'clan/clan-rank.html',
		)