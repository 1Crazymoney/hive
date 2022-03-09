import json

from concurrent.futures import ThreadPoolExecutor
from test_tools.communication import request
from typing import Dict, List

# account_names = ['null', 'steem.dao', 'hive.fund', 'gtg', 'blocktrades']
account_name = 'steem.dao'
server_develop_url = 'http://hive-2:8091'
json_server_develop_data_stored = f'/home/dev/Desktop/server_request_data/server_request_develop_data/{account_name}_server_request_develop_data.json'

server_master_url = 'http://hive-2:18091'
json_server_master_data_stored = f'/home/dev/Desktop/server_request_data/server_request_master_data/{account_name}_server_request_master_data.json'


def get_last_transaction_number(account_name: str, url: str) -> int:
    last_transaction = request(url,
                {"id": 9, "jsonrpc": "2.0", "method": "account_history_api.get_account_history",
                 "params": {"account": account_name, "start": -1, "limit": 1}})
    return last_transaction['result']['history'][0][0]


def load_json_from_file(path):
    with open(path, 'r') as f:
        data = json.load(f)
    return data


def json_sort(path):
    a = []
    with open(path, 'r') as f:
        data = json.load(f)
    for i in data:
        for j in i:
            a.append(j)
    return a


def get_all_account_transactions(account_name: str, start_transaction_number, last_transaction_number, url) -> List[Dict]:
    all_account_transaction = []
    for e, i in enumerate(range(last_transaction_number, start_transaction_number-1, -1000)):
        if start_transaction_number == 0 and i == 1:
            request_data = request(url,
                                   {"id": 9, "jsonrpc": "2.0", "method": "account_history_api.get_account_history",
                                    "params": {"account": account_name, "start": 0, "limit": 1}})
            all_account_transaction.append(request_data)
        elif last_transaction_number - start_transaction_number < 1000:
            request_data = request(url,
                                   {"id": 9, "jsonrpc": "2.0", "method": "account_history_api.get_account_history",
                                    "params": {"account": account_name, "start": i, "limit": last_transaction_number - start_transaction_number + 1}})
            all_account_transaction.append(request_data)
        else:
            request_data = request(url,
                                   {"id": 9, "jsonrpc": "2.0", "method": "account_history_api.get_account_history",
                                    "params": {"account": account_name, "start": i, "limit": 1000}})
            all_account_transaction.append(request_data)
            last_transaction_number -= 1000
        if e % 100 == 0:
            print('Downloaded 1000 packs of transactions', flush=True)
    return all_account_transaction


def save_transaction_to_json(source: str, account_name: str, start_transaction_number, last_transaction_number, url):
    single_saver_data = get_all_account_transactions(account_name, start_transaction_number, last_transaction_number, url)
    to_single_save = [list(reversed(item['result']['history'])) for item in single_saver_data]
    with open(f'/home/dev/Desktop/server_request_data/server_request_{source}_data/{account_name}_server_request_{source}_data.json', 'w') as file:
        json.dump(to_single_save, file)
    # multi_saver_datas = multi_saver(account_name, start_transaction_number, last_transaction_number, url)
    # to_save_multi = [list(reversed(item['result']['history'])) for item in multi_saver_datas]
    # print()
    # with open(data_stored, 'w') as file:
    #     json.dump(to_save_multi, file)


def multi_saver(account_name: str, start_transaction_number, last_transaction_number, url):
    tasks_list = []
    datas = []
    executor = ThreadPoolExecutor(max_workers=4)
    for i in range(last_transaction_number, start_transaction_number, -1000):
        if i - start_transaction_number < 1000:
            tasks_list.append(executor.submit(get_all_account_transactions, account_name, start_transaction_number, i, url))
        else:
            tasks_list.append(executor.submit(get_all_account_transactions, account_name, i - 1000, i, url))
    for thread_number in tasks_list:
        datas.extend(thread_number.result())
    return datas


def assign_transactions_keys(data):
    sorted_data = {}
    ignore_keys = ('virtual_op', 'op_in_trx')
    for all_transactions in data:
        sorted_data_key = (all_transactions[1]['block'], all_transactions[1]['timestamp'])
        if sorted_data_key not in sorted_data:
            sorted_data[sorted_data_key] = []
        no_vop_transaction = {k: v for k, v in all_transactions[1].items() if k not in ignore_keys}
        sorted_data[sorted_data_key].append(str(no_vop_transaction))
    return sorted_data


def compare_transactions(source: str, account_name: str, transaction_from, key_value_data):
    key_value_data = assign_transactions_keys(key_value_data)
    wrong_transactions = []
    operation_types = set()
    ignore_keys = ('virtual_op', 'op_in_trx')
    for all_transactions in transaction_from:
        data_key = (all_transactions[1]['block'], all_transactions[1]['timestamp'])
        no_vop_transaction = {k: v for k, v in all_transactions[1].items() if k not in ignore_keys}
        if all_transactions[1]['block'] <= 62000000:
            if data_key not in key_value_data:
                wrong_transactions.append(all_transactions)
                operation_types.add(all_transactions[1]['op']['type'])
            elif str(no_vop_transaction) not in key_value_data[data_key]:
                wrong_transactions.append(all_transactions)
                operation_types.add(all_transactions[1]['op']['type'])
    if source == 'master':
        with open(f'/home/dev/Desktop/server_request_data/differences_in_transactions/{account_name}_{source}_to_develop_differences_in_transactions.json', 'w') as f:
            f.write(f'Operation types: {operation_types}\n')
            json.dump(wrong_transactions, f)
    elif source == 'develop':
        with open(f'/home/dev/Desktop/server_request_data/differences_in_transactions/{account_name}_{source}_to_master_differences_in_transactions.json', 'w') as f:
            f.write(f'Operation types: {operation_types}\n')
            json.dump(wrong_transactions, f)
    else:
        print('Source error, please specify: master/ develop')
    return wrong_transactions

compare_transactions('develop', account_name, json_sort(json_server_develop_data_stored), json_sort(json_server_master_data_stored))
compare_transactions('master', account_name, json_sort(json_server_master_data_stored), json_sort(json_server_develop_data_stored))


# compare_transactions('develop', 'test', load_json_from_file(json_server_develop_data_stored), load_json_from_file(json_server_master_data_stored))
# compare_transactions('master', 'test', load_json_from_file(json_server_master_data_stored), load_json_from_file(json_server_develop_data_stored))

# save_transaction_to_json('master', 'hive.fund', 0, get_last_transaction_number('hive.fund', server_master_url), server_master_url)
# save_transaction_to_json('develop', 'hive.fund', 0, get_last_transaction_number('hive.fund', server_develop_url), server_develop_url)
# last hive.fund develop block 62330658
# compare_transactions('develop', 'hive.fund', json_sort(json_server_develop_data_stored), json_sort(json_server_master_data_stored))
# last 'hive.fund' master block 62330658
# compare_transactions('master', 'hive.fund', json_sort(json_server_master_data_stored), json_sort(json_server_develop_data_stored))


# save_transaction_to_json('master', 'steem.dao', 0, get_last_transaction_number('steem.dao', server_master_url), server_master_url)
# save_transaction_to_json('develop', 'steem.dao', 0, get_last_transaction_number('steem.dao', server_develop_url), server_develop_url)
# last steem.dao develop block 62355796
# compare_transactions('develop', 'steem.dao', json_sort(json_server_develop_data_stored), json_sort(json_server_master_data_stored))
# last steem.dao master block 62331853
# compare_transactions('master', 'steem.dao', json_sort(json_server_master_data_stored), json_sort(json_server_develop_data_stored))


# save_transaction_to_json('master', 'null', 0, get_last_transaction_number('null', server_master_url), server_master_url)
# save_transaction_to_json('develop', 'null', 0, get_last_transaction_number('null', server_develop_url), server_develop_url)
# last develop 'block' 62325189
# compare_transactions('develop', 'null', json_sort(json_server_develop_data_stored), json_sort(json_server_master_data_stored))
# last master 'block' 62325189
# compare_transactions('master', 'null', json_sort(json_server_master_data_stored), json_sort(json_server_develop_data_stored))


# last develop 'gtg', 'block' = 62245215
# compare_transactions('develop', 'gtg', json_sort(json_server_develop_data_stored), json_sort(json_server_master_data_stored))
# last master 'gtg', 'block' = 62246376
# compare_transactions('master', 'gtg', json_sort(json_server_master_data_stored), json_sort(json_server_develop_data_stored))

# compare_transactions('develop', 'blocktrades', json_sort(json_server_develop_data_stored), json_sort(json_server_master_data_stored))
# compare_transactions('master', 'blocktrades', json_sort(json_server_master_data_stored), json_sort(json_server_develop_data_stored))
