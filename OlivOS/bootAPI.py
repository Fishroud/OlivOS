# -*- encoding: utf-8 -*-
'''
_______________________    ________________
__  __ \__  /____  _/_ |  / /_  __ \_  ___/
_  / / /_  /  __  / __ | / /_  / / /____ \
/ /_/ /_  /____/ /  __ |/ / / /_/ /____/ /
\____/ /_____/___/  _____/  \____/ /____/

@File      :   OlivOS/bootAPI.py
@Author    :   lunzhiPenxil仑质
@Contact   :   lunzhipenxil@gmail.com
@License   :   AGPL
@Copyright :   (C) 2020-2021, OlivOS-Team
@Desc      :   None
'''

# here put the import lib

import sys
import os
import time
import json
import multiprocessing
import platform

import OlivOS

def releaseDir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

class Entity(object):
    def __init__(self, basic_conf = None):
        self.Config = {}
        self.Config['basic_conf_path'] = './conf/basic.json'
        if basic_conf != None:
            self.Config['basic_conf_path'] = basic_conf

    def start(self):
        #兼容Win平台多进程，避免形成fork-bomb
        multiprocessing.freeze_support()
        basic_conf_path = self.Config['basic_conf_path']
        basic_conf = None
        basic_conf_models = None
        Proc_dict = {}
        Proc_Proc_dict = {}
        Proc_logger_name = []
        plugin_bot_info_dict = {}

        start_up_show_str = ('''
_______________________    ________________
__  __ \__  /____  _/_ |  / /_  __ \_  ___/
_  / / /_  /  __  / __ | / /_  / / /____ \ 
/ /_/ /_  /____/ /  __ |/ / / /_/ /____/ / 
\____/ /_____/___/  _____/  \____/ /____/  
'''     )
        print(start_up_show_str)
        print('･ﾟ( ﾉヮ´ )(`ヮ´ )σ`∀´) ﾟ∀ﾟ)σ' + ' [OlivOS - Witness Union]\n')

        print('init config from [' + basic_conf_path + '] ... ', end = '')
        try:
            with open(basic_conf_path, 'r', encoding = 'utf-8') as basic_conf_f:
                basic_conf = json.loads(basic_conf_f.read())
        except:
            print('failed')
            releaseDir('./conf')
            basic_conf = OlivOS.bootDataAPI.default_Conf
            print('init config from default ... done')
        else:
            print('done')
        print('init models from config ... ', end = '')
        if basic_conf != None:
            basic_conf_models = basic_conf['models']
            print('done')
        else:
            print('failed')
            sys.exit()

        print('generate queue from config ... ')
        multiprocessing_dict = {}
        for queue_name_this in basic_conf['queue']:
            print('generate queue [' + queue_name_this + '] from config ... ', end = '')
            multiprocessing_dict[queue_name_this] = multiprocessing.Queue()
            print('done')
        print('generate queue from config ... all done')

        main_control = OlivOS.API.Control(
            name = basic_conf['system']['name'],
            init_list = basic_conf['system']['init'],
            control_queue = multiprocessing_dict[basic_conf['system']['control_queue']],
            scan_interval = basic_conf['system']['interval']
        )

        for basic_conf_models_this_name in main_control.init_list:
            main_control.control_queue.put(main_control.packet('init', basic_conf_models_this_name), block = False)

        while True:
            if main_control.control_queue.empty():
                time.sleep(main_control.scan_interval)
                continue
            else:
                try:
                    rx_packet_data = main_control.control_queue.get(block = False)
                except:
                    continue
            if rx_packet_data.action == 'init':
                #兼容Win平台多进程，避免形成fork-bomb
                multiprocessing.freeze_support()
                basic_conf_models_this = basic_conf_models[rx_packet_data.key]
                if basic_conf_models_this['enable'] == True:
                    if basic_conf_models_this['type'] == 'logger':
                        Proc_dict[basic_conf_models_this['name']] = OlivOS.diagnoseAPI.logger(
                            Proc_name = basic_conf_models_this['name'],
                            scan_interval = basic_conf_models_this['interval'],
                            dead_interval = basic_conf_models_this['dead_interval'],
                            logger_queue = multiprocessing_dict[basic_conf_models_this['rx_queue']],
                            logger_mode = basic_conf_models_this['mode'],
                            logger_vis_level = basic_conf_models_this['fliter']
                        )
                        tmp_proc_mode = 'processing'
                        if 'proc_mode' in basic_conf_models_this:
                            tmp_proc_mode = basic_conf_models_this['proc_mode']
                        #不完全轻量模式原本就是是为了解决Linux下日志挂载问题设计的
                        #不完全轻量模式在Win下存在问题，强制全量模式
                        if platform.system() == 'Windows':
                            tmp_proc_mode = 'processing'
                        if tmp_proc_mode == 'processing':
                            Proc_Proc_dict[basic_conf_models_this['name']] = OlivOS.API.Proc_start(Proc_dict[basic_conf_models_this['name']])
                        elif tmp_proc_mode == 'threading':
                            Proc_Proc_dict[basic_conf_models_this['name']] = Proc_dict[basic_conf_models_this['name']].start_lite()
                        else:
                            Proc_Proc_dict[basic_conf_models_this['name']] = OlivOS.API.Proc_start(Proc_dict[basic_conf_models_this['name']])
                        for this_bot_info in  plugin_bot_info_dict:
                            plugin_bot_info_dict[this_bot_info].debug_logger = Proc_dict[basic_conf_models_this['name']]
                        Proc_logger_name = basic_conf_models_this['name']
                    elif basic_conf_models_this['type'] == 'plugin':
                        proc_plugin_func_dict = {}
                        tmp_tx_queue_list = []
                        for tmp_tx_queue_list_this in basic_conf_models_this['tx_queue']:
                            tmp_tx_queue_list.append(multiprocessing_dict[tmp_tx_queue_list_this])
                        Proc_dict[basic_conf_models_this['name']] = OlivOS.pluginAPI.shallow(
                            Proc_name = basic_conf_models_this['name'],
                            scan_interval = basic_conf_models_this['interval'],
                            dead_interval = basic_conf_models_this['dead_interval'],
                            rx_queue = multiprocessing_dict[basic_conf_models_this['rx_queue']],
                            tx_queue = tmp_tx_queue_list,
                            control_queue = multiprocessing_dict[basic_conf_models_this['control_queue']],
                            logger_proc = Proc_dict[basic_conf_models_this['logger_proc']],
                            debug_mode = basic_conf_models_this['debug'],
                            plugin_func_dict = proc_plugin_func_dict,
                            bot_info_dict = plugin_bot_info_dict,
                            treading_mode = basic_conf_models_this['treading_mode'],
                            restart_gate = basic_conf_models_this['restart_gate'],
                            enable_auto_restart = basic_conf_models_this['enable_auto_restart']
                        )
                        Proc_Proc_dict[basic_conf_models_this['name']] = OlivOS.API.Proc_start(Proc_dict[basic_conf_models_this['name']])
                    elif basic_conf_models_this['type'] == 'post':
                        flag_need_enable = False
                        for bot_info_key in plugin_bot_info_dict:
                            if plugin_bot_info_dict[bot_info_key].platform['sdk'] == 'onebot':
                                flag_need_enable = True
                        if not flag_need_enable:
                            continue
                        Proc_dict[basic_conf_models_this['name']] = OlivOS.flaskServerAPI.server(
                            Proc_name = basic_conf_models_this['name'],
                            scan_interval = basic_conf_models_this['interval'],
                            dead_interval = basic_conf_models_this['dead_interval'],
                            Flask_namespace = __name__,
                            Flask_server_methods = ['POST'],
                            Flask_host = basic_conf_models_this['server']['host'],
                            Flask_port = basic_conf_models_this['server']['port'],
                            tx_queue = multiprocessing_dict[basic_conf_models_this['tx_queue']],
                            debug_mode = basic_conf_models_this['debug'],
                            logger_proc = Proc_dict[basic_conf_models_this['logger_proc']],
                        )
                        Proc_Proc_dict[basic_conf_models_this['name']] = OlivOS.API.Proc_start(Proc_dict[basic_conf_models_this['name']])
                    elif basic_conf_models_this['type'] == 'account_config':
                        plugin_bot_info_dict = OlivOS.accountAPI.Account.load(
                            path = basic_conf_models_this['data']['path'],
                            logger_proc = Proc_dict[basic_conf_models_this['logger_proc']]
                        )
                    elif basic_conf_models_this['type'] == 'account_config_safe':
                        plugin_bot_info_dict = OlivOS.accountAPI.Account.load(
                            path = basic_conf_models_this['data']['path'],
                            logger_proc = Proc_dict[basic_conf_models_this['logger_proc']],
                            safe_mode = True
                        )
                    elif basic_conf_models_this['type'] == 'account_fix':
                        plugin_bot_info_dict = OlivOS.fanbookPollServerAPI.accountFix(
                            bot_info_dict = plugin_bot_info_dict,
                            logger_proc = Proc_dict[basic_conf_models_this['logger_proc']],
                        )
                        plugin_bot_info_dict = OlivOS.kaiheilaLinkServerAPI.accountFix(
                            bot_info_dict = plugin_bot_info_dict,
                            logger_proc = Proc_dict[basic_conf_models_this['logger_proc']],
                        )
                        plugin_bot_info_dict = OlivOS.accountAPI.accountFix(
                            basic_conf_models = basic_conf_models,
                            bot_info_dict = plugin_bot_info_dict,
                            logger_proc = Proc_dict[basic_conf_models_this['logger_proc']],
                        )
                    elif basic_conf_models_this['type'] == 'qqGuild_link':
                        flag_need_enable = False
                        for bot_info_key in plugin_bot_info_dict:
                            if plugin_bot_info_dict[bot_info_key].platform['sdk'] == 'qqGuild_link':
                                flag_need_enable = True
                        if not flag_need_enable:
                            continue
                        for bot_info_key in plugin_bot_info_dict:
                            if plugin_bot_info_dict[bot_info_key].platform['sdk'] == 'qqGuild_link':
                                tmp_Proc_name = basic_conf_models_this['name'] + '=' + bot_info_key
                                Proc_dict[tmp_Proc_name] = OlivOS.qqGuildLinkServerAPI.server(
                                    Proc_name = tmp_Proc_name,
                                    scan_interval = basic_conf_models_this['interval'],
                                    dead_interval = basic_conf_models_this['dead_interval'],
                                    rx_queue = None,
                                    tx_queue = multiprocessing_dict[basic_conf_models_this['tx_queue']],
                                    logger_proc = Proc_dict[basic_conf_models_this['logger_proc']],
                                    bot_info_dict = plugin_bot_info_dict[bot_info_key],
                                    debug_mode = False
                                )
                                Proc_Proc_dict[basic_conf_models_this['name']] = OlivOS.API.Proc_start(Proc_dict[tmp_Proc_name])
                    elif basic_conf_models_this['type'] == 'kaiheila_link':
                        flag_need_enable = False
                        for bot_info_key in plugin_bot_info_dict:
                            if plugin_bot_info_dict[bot_info_key].platform['sdk'] == 'kaiheila_link':
                                flag_need_enable = True
                        if not flag_need_enable:
                            continue
                        for bot_info_key in plugin_bot_info_dict:
                            if plugin_bot_info_dict[bot_info_key].platform['sdk'] == 'kaiheila_link':
                                tmp_Proc_name = basic_conf_models_this['name'] + '=' + bot_info_key
                                Proc_dict[tmp_Proc_name] = OlivOS.kaiheilaLinkServerAPI.server(
                                    Proc_name = tmp_Proc_name,
                                    scan_interval = basic_conf_models_this['interval'],
                                    dead_interval = basic_conf_models_this['dead_interval'],
                                    rx_queue = None,
                                    tx_queue = multiprocessing_dict[basic_conf_models_this['tx_queue']],
                                    logger_proc = Proc_dict[basic_conf_models_this['logger_proc']],
                                    bot_info_dict = plugin_bot_info_dict[bot_info_key],
                                    debug_mode = False
                                )
                                Proc_Proc_dict[basic_conf_models_this['name']] = OlivOS.API.Proc_start(Proc_dict[tmp_Proc_name])
                    elif basic_conf_models_this['type'] == 'telegram_poll':
                        flag_need_enable = False
                        for bot_info_key in plugin_bot_info_dict:
                            if plugin_bot_info_dict[bot_info_key].platform['sdk'] == 'telegram_poll':
                                flag_need_enable = True
                        if not flag_need_enable:
                            continue
                        Proc_dict[basic_conf_models_this['name']] = OlivOS.telegramPollServerAPI.server(
                            Proc_name = basic_conf_models_this['name'],
                            scan_interval = basic_conf_models_this['interval'],
                            dead_interval = basic_conf_models_this['dead_interval'],
                            rx_queue = None,
                            tx_queue = multiprocessing_dict[basic_conf_models_this['tx_queue']],
                            logger_proc = Proc_dict[basic_conf_models_this['logger_proc']],
                            bot_info_dict = plugin_bot_info_dict,
                            debug_mode = False
                        )
                        Proc_Proc_dict[basic_conf_models_this['name']] = OlivOS.API.Proc_start(Proc_dict[basic_conf_models_this['name']])
                    elif basic_conf_models_this['type'] == 'fanbook_poll':
                        flag_need_enable = False
                        for bot_info_key in plugin_bot_info_dict:
                            if plugin_bot_info_dict[bot_info_key].platform['sdk'] == 'fanbook_poll':
                                flag_need_enable = True
                        if not flag_need_enable:
                            continue
                        Proc_dict[basic_conf_models_this['name']] = OlivOS.fanbookPollServerAPI.server(
                            Proc_name = basic_conf_models_this['name'],
                            scan_interval = basic_conf_models_this['interval'],
                            dead_interval = basic_conf_models_this['dead_interval'],
                            rx_queue = None,
                            tx_queue = multiprocessing_dict[basic_conf_models_this['tx_queue']],
                            logger_proc = Proc_dict[basic_conf_models_this['logger_proc']],
                            bot_info_dict = plugin_bot_info_dict,
                            debug_mode = False
                        )
                        Proc_Proc_dict[basic_conf_models_this['name']] = OlivOS.API.Proc_start(Proc_dict[basic_conf_models_this['name']])
                    elif basic_conf_models_this['type'] == 'dodo_link':
                        flag_need_enable = False
                        for bot_info_key in plugin_bot_info_dict:
                            if plugin_bot_info_dict[bot_info_key].platform['sdk'] == 'dodo_link':
                                flag_need_enable = True
                        if not flag_need_enable:
                            continue
                        for bot_info_key in plugin_bot_info_dict:
                            if plugin_bot_info_dict[bot_info_key].platform['sdk'] == 'dodo_link':
                                tmp_Proc_name = basic_conf_models_this['name'] + '=' + bot_info_key
                                Proc_dict[tmp_Proc_name] = OlivOS.dodoLinkServerAPI.server(
                                    Proc_name = tmp_Proc_name,
                                    scan_interval = basic_conf_models_this['interval'],
                                    dead_interval = basic_conf_models_this['dead_interval'],
                                    rx_queue = None,
                                    tx_queue = multiprocessing_dict[basic_conf_models_this['tx_queue']],
                                    logger_proc = Proc_dict[basic_conf_models_this['logger_proc']],
                                    bot_info_dict = plugin_bot_info_dict[bot_info_key],
                                    debug_mode = False
                                )
                                Proc_Proc_dict[basic_conf_models_this['name']] = OlivOS.API.Proc_start(Proc_dict[tmp_Proc_name])
                    elif basic_conf_models_this['type'] == 'dodo_poll':
                        flag_need_enable = False
                        for bot_info_key in plugin_bot_info_dict:
                            if plugin_bot_info_dict[bot_info_key].platform['sdk'] == 'dodo_poll':
                                flag_need_enable = True
                        if not flag_need_enable:
                            continue
                        Proc_dict[basic_conf_models_this['name']] = OlivOS.dodoPollServerAPI.server(
                            Proc_name = basic_conf_models_this['name'],
                            scan_interval = basic_conf_models_this['interval'],
                            dead_interval = basic_conf_models_this['dead_interval'],
                            rx_queue = None,
                            tx_queue = multiprocessing_dict[basic_conf_models_this['tx_queue']],
                            logger_proc = Proc_dict[basic_conf_models_this['logger_proc']],
                            bot_info_dict = plugin_bot_info_dict,
                            debug_mode = False
                        )
                        Proc_Proc_dict[basic_conf_models_this['name']] = OlivOS.API.Proc_start(Proc_dict[basic_conf_models_this['name']])
                    elif basic_conf_models_this['type'] == 'dodobot_ea':
                        Proc_dict[basic_conf_models_this['name']] = OlivOS.dodobotEAServerAPI.server(
                            Proc_name = basic_conf_models_this['name'],
                            scan_interval = basic_conf_models_this['interval'],
                            dead_interval = basic_conf_models_this['dead_interval'],
                            rx_queue = None,
                            tx_queue = multiprocessing_dict[basic_conf_models_this['tx_queue']],
                            logger_proc = Proc_dict[basic_conf_models_this['logger_proc']],
                            bot_info_dict = plugin_bot_info_dict,
                            debug_mode = False
                        )
                        Proc_Proc_dict[basic_conf_models_this['name']] = OlivOS.API.Proc_start(Proc_dict[basic_conf_models_this['name']])
                    elif basic_conf_models_this['type'] == 'dodobot_ea_tx':
                        Proc_dict[basic_conf_models_this['name']] = OlivOS.dodobotEATXAPI.server(
                            Proc_name = basic_conf_models_this['name'],
                            scan_interval = basic_conf_models_this['interval'],
                            dead_interval = basic_conf_models_this['dead_interval'],
                            rx_queue = multiprocessing_dict[basic_conf_models_this['rx_queue']],
                            tx_queue = multiprocessing_dict[basic_conf_models_this['tx_queue']],
                            logger_proc = Proc_dict[basic_conf_models_this['logger_proc']],
                            bot_info_dict = plugin_bot_info_dict,
                            debug_mode = False
                        )
                        Proc_Proc_dict[basic_conf_models_this['name']] = OlivOS.API.Proc_start(Proc_dict[basic_conf_models_this['name']])
                    elif basic_conf_models_this['type'] == 'multiLoginUI':
                        if(platform.system() == 'Windows'):
                            Proc_dict[basic_conf_models_this['name']] = OlivOS.multiLoginUIAPI.HostUI(
                                Model_name = basic_conf_models_this['name'],
                                Account_data = plugin_bot_info_dict,
                                logger_proc = Proc_dict[basic_conf_models_this['logger_proc']]
                            )
                            Proc_dict[basic_conf_models_this['name']].start()
                            if Proc_dict[basic_conf_models_this['name']].UIData['flag_commit']:
                                plugin_bot_info_dict = Proc_dict[basic_conf_models_this['name']].UIData['Account_data']
                    elif basic_conf_models_this['type'] == 'account_config_save':
                        OlivOS.accountAPI.Account.save(
                            path = basic_conf_models_this['data']['path'],
                            Account_data = plugin_bot_info_dict,
                            logger_proc = Proc_dict[basic_conf_models_this['logger_proc']]
                        )
                    elif basic_conf_models_this['type'] == 'gocqhttp_lib_exe_model':
                        if(platform.system() == 'Windows'):
                            for bot_info_key in plugin_bot_info_dict:
                                if plugin_bot_info_dict[bot_info_key].platform['model'] == 'gocqhttp' or plugin_bot_info_dict[bot_info_key].platform['model'] == 'gocqhttp_hide' or plugin_bot_info_dict[bot_info_key].platform['model'] == 'gocqhttp_show':
                                    tmp_Proc_name = basic_conf_models_this['name'] + '=' + bot_info_key
                                    Proc_dict[tmp_Proc_name] = OlivOS.libEXEModelAPI.server(
                                        Proc_name = tmp_Proc_name,
                                        scan_interval = basic_conf_models_this['interval'],
                                        dead_interval = basic_conf_models_this['dead_interval'],
                                        rx_queue = None,
                                        tx_queue = multiprocessing_dict[basic_conf_models_this['tx_queue']],
                                        logger_proc = Proc_dict[basic_conf_models_this['logger_proc']],
                                        bot_info_dict = plugin_bot_info_dict[bot_info_key],
                                        target_proc = basic_conf_models[basic_conf_models_this['target_proc']],
                                        debug_mode = False
                                    )
                                    Proc_Proc_dict[tmp_Proc_name] = OlivOS.API.Proc_start(Proc_dict[tmp_Proc_name])
            elif rx_packet_data.action == 'restart_do':
                time.sleep(Proc_dict[rx_packet_data.key].Proc_info.dead_interval)
                Proc_Proc_dict[rx_packet_data.key].terminate()
                Proc_Proc_dict[rx_packet_data.key].join()
