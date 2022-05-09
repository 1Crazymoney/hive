from test_tools import Account, Asset
from .local_tools import create_account_and_fund_it, generate_sig_digest


def create_escrow(wallet, sender):
    # create agent account and receiver
    new_accounts = ['bill', 'clayton']
    for name in new_accounts:
        wallet.api.create_account(sender, name, '{}')
    wallet.api.escrow_transfer(sender, 'bill', 'clayton', 123, Asset.Tbd(25), Asset.Test(50), Asset.Tbd(1),
                               '2030-04-20T00:00:00', '2030-05-20T00:00:00', '{}')


def update_account_owner_key(wallet, account_name):
    key = 'TST8grZpsMPnH7sxbMVZHWEu1D26F3GwLW1fYnZEuwzT4Rtd57AER'
    # update_account_auth_key with owner parameter is called to change owner authority history
    wallet.api.update_account_auth_key(account_name, 'owner', key, 1)


def transfer_and_withdraw_from_savings(wallet, account_name):
    # just make transfer to savings account and withdraw low amount of hives from it
    wallet.api.transfer_to_savings(account_name, account_name, Asset.Test(50), 'test transfer to savings')
    wallet.api.transfer_from_savings(account_name, 124, account_name, Asset.Test(5), 'test transfer from savings')


def create_and_cancel_vesting_delegation(wallet, delegator, delegatee):
    wallet.api.delegate_vesting_shares(delegator, delegatee, Asset.Vest(5))
    # delegation of 0 removes the delegation
    wallet.api.delegate_vesting_shares(delegator, delegatee, Asset.Vest(0))


def create_proposal(wallet, account_name):
    wallet.api.post_comment(account_name, 'test-permlink', '', 'test-parent-permlink', 'test-title', 'test-body', '{}')
    # create proposal with permlink pointing to comment
    wallet.api.create_proposal(account_name, account_name, '2030-04-20T00:00:00', '2030-05-20T00:00:00', Asset.Tbd(5),
                               'test subject', 'test-permlink')


def create_account_recovery_request(wallet, account_name):
    account_to_recover_owner_key = Account('initminer').public_key
    # 'initminer' account is listed as recovery_account in 'alice' and only he has 'power' to recover account
    # that's why initminer's key is in new 'alice' authority
    authority = {"weight_threshold": 1, "account_auths": [], "key_auths": [[account_to_recover_owner_key, 1]]}
    # create new recovery request
    wallet.api.request_account_recovery('initminer', account_name, authority)


def test_find_account_recovery_requests(node, wallet):
    # create new account
    account_to_recover = "alice"
    wallet.api.create_account('initminer', account_to_recover, '{}')

    create_account_recovery_request(wallet, account_to_recover)
    requests = node.api.database.find_account_recovery_requests(accounts=[account_to_recover])['requests']
    # check if there is any requests output
    assert len(requests) != 0


def test_find_accounts(node, wallet):
    account_to_check = 'alice'
    wallet.api.create_account('initminer', account_to_check, '{}')
    accounts = node.api.database.find_accounts(account=[account_to_check])['accounts']
    # BUG: method outputs empty list even though 'alice' account exists
    assert len(accounts) != 0


def test_find_change_recovery_account_requests(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    # change recovery account
    wallet.api.change_recovery_account('alice', 'steem.dao')
    requests = node.api.database.find_change_recovery_account_requests(accounts=['alice'])['requests']
    assert len(requests) != 0


def test_find_collateralized_conversion_requests(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    # convert_hive_with_collateral changes hives for hbd, this process takes three and half days
    wallet.api.convert_hive_with_collateral('alice', Asset.Test(4))
    requests = node.api.database.find_collateralized_conversion_requests(account='alice')['requests']
    assert len(requests) != 0


def test_find_comments(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    wallet.api.post_comment('alice', 'test-permlink', '', 'someone', 'test-title', 'this is a body', '{}')
    comments = node.api.database.find_comments(comments=[['alice', 'test-permlink']])['comments']
    assert len(comments) != 0


def test_find_decline_voting_rights_requests(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    wallet.api.decline_voting_rights('alice', True)
    requests = node.api.database.find_decline_voting_rights_requests(accounts=['alice'])
    assert len(requests) != 0


def test_find_escrows(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    wallet.api.transfer('initminer', 'alice', Asset.Tbd(100), 'test memo')
    create_escrow(wallet, 'alice')
    # "from" is a Python keyword and needs workaround
    escrows = node.api.database.find_escrows(**{'from': 'alice'})['escrows']
    assert len(escrows) != 0


def test_find_hbd_conversion_requests(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    wallet.api.transfer('initminer', 'alice', Asset.Tbd(100), 'test memo')
    wallet.api.convert_hbd('alice', Asset.Tbd(1.25))
    requests = node.api.database.find_hbd_conversion_requests(account='alice')['requests']
    assert len(requests) != 0


def test_find_limit_orders(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    wallet.api.create_order('alice', 431, Asset.Test(50), Asset.Tbd(5), False, 3600)
    orders = node.api.database.find_limit_orders(account='alice')['orders']
    assert len(orders) != 0


def test_find_owner_histories(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    # to fill authority history, changing of owner key is needed, that's why update_account_auth_key is called with
    # 'owner' parameter
    update_account_owner_key(wallet, 'alice')
    owner_auths = node.api.database.find_owner_histories(owner='alice')['owner_auths']
    assert len(owner_auths) != 0


def test_find_proposals(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    wallet.api.transfer('initminer', 'alice', Asset.Tbd(100), 'test memo')
    create_proposal(wallet, 'alice')
    proposals = node.api.database.find_proposals(proposal_ids=[0])['proposals']
    assert len(proposals) != 0


def test_find_recurrent_transfers(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    wallet.api.create_account('initminer', 'bob', '{}')
    # create transfer from alice to bob for amount 5 test hives every 720 hours, repeat 12 times
    wallet.api.recurrent_transfer('alice', 'bob', Asset.Test(5), 'test memo', 720, 12)
    # "from" is a Python keyword and needs workaround
    recurrent_transfers = node.api.database.find_recurrent_transfers(**{'from': 'alice'})['recurrent_transfers']
    assert len(recurrent_transfers) != 0


def test_find_savings_withdrawals(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    transfer_and_withdraw_from_savings(wallet, 'alice')
    withdrawals = node.api.database.find_savings_withdrawals(account='alice')['withdrawals']
    assert len(withdrawals) != 0


def test_find_vesting_delegation_expirations(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    wallet.api.create_account('alice', 'bob', '{}')
    create_and_cancel_vesting_delegation(wallet, 'alice', 'bob')
    delegations = node.api.database.find_vesting_delegation_expirations(account='alice')['delegations']
    assert len(delegations) != 0


def test_find_vesting_delegations(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    wallet.api.create_account('alice', 'bob', '{}')
    wallet.api.delegate_vesting_shares('alice', 'bob', Asset.Vest(5))
    delegations = node.api.database.find_vesting_delegations(account='alice')
    assert len(delegations) != 0


def test_find_withdraw_vesting_routes(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    wallet.api.create_account('alice', 'bob', '{}')
    wallet.api.set_withdraw_vesting_route('alice', 'bob', 15, True)
    routes = node.api.database.find_withdraw_vesting_routes(account='bob', order='by_destination')['routes']
    assert len(routes) != 0


def test_find_witnesses(node, wallet):
    witnesses = node.api.database.find_witnesses(owners=['initminer'])['witnesses']
    assert len(witnesses) != 0


def test_get_comment_pending_payouts(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    wallet.api.post_comment('alice', 'test-permlink', '', 'test-parent-permlink', 'test-title', 'test-body', '{}')
    cashout_info = node.api.database.get_comment_pending_payouts(comments=[['alice', 'test-permlink']])['cashout_infos']
    assert len(cashout_info) != 0


def test_get_order_book(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    create_account_and_fund_it(wallet, 'bob')
    wallet.api.transfer('initminer', 'bob', Asset.Tbd(100), 'test memo')
    # create 2 orders from 2 different accounts to fill 'bids' in order book. One is for selling test hives, and getting
    # tbd and second one for selling tbd and getting test hives
    wallet.api.create_order('alice', 431, Asset.Test(150), Asset.Tbd(15), False, 3600)
    wallet.api.create_order('bob', 123, Asset.Tbd(50), Asset.Test(500), False, 3600)
    response = node.api.database.get_order_book(limit=100)
    assert len(response['bids']) != 0

    # cancel bob's order to clear order book
    wallet.api.cancel_order('bob', 123)
    # create new order to check 'asks' in order book
    wallet.api.transfer('initminer', 'alice', Asset.Test(100), 'test memo')
    wallet.api.create_order('alice', 868, Asset.Test(100), Asset.Tbd(10), False, 3600)
    response = node.api.database.get_order_book(limit=100)
    assert len(response['asks']) != 0


def test_get_potential_signatures(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    trx = wallet.api.create_order('alice', 431, Asset.Test(50), Asset.Tbd(5), False, 3600)
    keys = node.api.database.get_potential_signatures(trx=trx)['keys']
    assert len(keys) != 0


def test_get_required_signatures(node, wallet):
    trx = wallet.api.create_order('initminer', 431, Asset.Test(50), Asset.Tbd(5), False, 3600)
    keys = node.api.database.get_required_signatures(trx=trx, available_keys=[Account('initminer').public_key])['keys']
    assert len(keys) != 0


def test_get_transaction_hex(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    trx = wallet.api.create_order('alice', 431, Asset.Test(50), Asset.Tbd(5), False, 3600)
    output_hex = node.api.database.get_transaction_hex(trx=trx)['hex']
    assert len(output_hex) != 0


def test_is_known_transaction(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    trx = wallet.api.create_order('alice', 431, Asset.Test(50), Asset.Tbd(5), False, 360)
    response = node.api.database.is_known_transaction(id=trx['transaction_id'])['is_known']
    assert response is not False


def test_list_account_recovery_requests(node, wallet):
    account_to_recover = "alice"
    wallet.api.create_account('initminer', account_to_recover, '{}')
    create_account_recovery_request(wallet, account_to_recover)
    response = node.api.database.list_account_recovery_requests(start='', limit=100, order='by_account')
    assert len(response) != 0


def test_list_accounts(node, wallet):
    wallet.api.create_account('initminer', 'alice', '{}')
    accounts = node.api.database.list_accounts(start='', limit=100, order='by_name')['accounts']
    assert len(accounts) != 0


def test_list_change_recovery_account_requests(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    wallet.api.change_recovery_account('initminer', 'hive.fund')
    requests = node.api.database.list_change_recovery_account_requests(start='', limit=100, order='by_account')
    assert len(requests) != 0


def test_list_collateralized_conversion_requests(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    wallet.api.convert_hive_with_collateral('alice', Asset.Test(4))
    requests = node.api.database.list_collateralized_conversion_requests(start=[""], limit=100, order='by_account')
    assert len(requests) != 0


def test_list_decline_voting_rights_requests(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    wallet.api.decline_voting_rights('alice', True)
    requests = node.api.database.list_decline_voting_rights_requests(start='', limit=100, order='by_account')
    assert len(requests) != 0


def test_list_escrows(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    wallet.api.transfer('initminer', 'alice', Asset.Tbd(100), 'test memo')
    create_escrow(wallet, 'alice')
    escrows = node.api.database.list_escrows(start=['alice', 0], limit=5, order='by_from_id')['escrows']
    assert len(escrows) != 0


def test_list_hbd_conversion_requests(wallet, node):
    create_account_and_fund_it(wallet, 'alice')
    wallet.api.transfer('initminer', 'alice', Asset.Tbd(100), 'test memo')
    wallet.api.convert_hbd('alice', Asset.Tbd(1.25))
    requests = node.api.database.list_hbd_conversion_requests(start=['alice', 0], limit=100, order='by_account')['requests']
    assert len(requests) != 0


def test_list_limit_orders(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    wallet.api.create_order('alice', 431, Asset.Test(50), Asset.Tbd(5), False, 3600)
    orders = node.api.database.list_limit_orders(start=['alice', 0], limit=100, order='by_account')
    assert len(orders) != 0


def test_list_owner_histories(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    update_account_owner_key(wallet, 'alice')
    owner_auths = node.api.database.list_owner_histories(start=['alice', "2022-04-11T10:29:00"], limit=100)['owner_auths']
    assert len(owner_auths) != 0


def test_list_savings_withdrawals(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    transfer_and_withdraw_from_savings(wallet, 'alice')
    withdrawals = node.api.database.list_savings_withdrawals(start=["2022-04-11T10:29:00", "alice", 0], limit=100,
                                                             order='by_complete_from_id')['withdrawals']
    assert len(withdrawals) != 0


def test_list_vesting_delegation_expirations(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    wallet.api.create_account('alice', 'bob', '{}')
    create_and_cancel_vesting_delegation(wallet, 'alice', 'bob')
    delegations = node.api.database.list_vesting_delegation_expirations(start=['alice', '2022-04-11T10:29:00', 0],
                                                                        limit=100, order='by_account_expiration')['delegations']
    assert len(delegations) != 0


def test_list_vesting_delegations(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    wallet.api.create_account('alice', 'bob', '{}')
    wallet.api.delegate_vesting_shares('alice', 'bob', Asset.Vest(5))
    delegations = node.api.database.list_vesting_delegations(start=["alice", "bob"], limit=100, order='by_delegation')['delegations']
    assert len(delegations) != 0


def test_list_withdraw_vesting_routes(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    wallet.api.create_account('alice', 'bob', '{}')
    wallet.api.set_withdraw_vesting_route('alice', 'bob', 15, True)
    routes = node.api.database.list_withdraw_vesting_routes(start=["alice", "bob"], limit=100, order="by_withdraw_route")['routes']
    assert len(routes) != 0


def test_list_witness_votes(node, wallet):
    # create new witness
    create_account_and_fund_it(wallet, 'alice')
    create_account_and_fund_it(wallet, 'bob')
    wallet.api.update_witness('alice', 'http:\\url.html',
                              'TST6LLegbAgLAy28EHrffBVuANFWcFgmqRMW13wBmTExqFE9SCkg4',
                              {'account_creation_fee': '2789.030 TESTS', 'maximum_block_size': 131072,
                               'hbd_interest_rate': 1000})
    # vote for alice from bob account
    wallet.api.vote_for_witness('bob', 'alice', True)
    votes = node.api.database.list_witness_votes(start=["alice", "bob"], limit=100, order='by_witness_account')['votes']
    assert len(votes) != 0


def test_list_witnesses(node, wallet):
    # create new witness
    create_account_and_fund_it(wallet, 'alice')
    wallet.api.update_witness('alice', 'http:\\url.html',
                              'TST6LLegbAgLAy28EHrffBVuANFWcFgmqRMW13wBmTExqFE9SCkg4',
                              {'account_creation_fee': '2789.030 TESTS', 'maximum_block_size': 131072,
                               'hbd_interest_rate': 1000})
    witnesses = node.api.database.list_witnesses(start='', limit=100, order='by_name')['witnesses']
    assert len(witnesses) != 0


def test_verify_authority(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    trx = wallet.api.create_order('alice', 431, Asset.Test(50), Asset.Tbd(5), False, 3600)
    response = node.api.database.verify_authority(trx=trx)
    assert response is not False


def test_list_proposal_votes(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    wallet.api.transfer('initminer', 'alice', Asset.Tbd(100), 'test memo')
    create_proposal(wallet, 'alice')
    wallet.api.update_proposal_votes('alice', [0], True)
    proposal_votes = node.api.database.list_proposal_votes(start=['alice'], limit=100, order='by_voter_proposal',
                                                           order_direction='ascending', status='all')['proposal_votes']
    assert len(proposal_votes) != 0


def test_verify_signatures(node, wallet):
    wallet.api.create_account('initminer', 'alice', '{}')
    trx = wallet.api.transfer('initminer', 'alice', Asset.Test(500), 'test memo')
    initminer_private_key = Account('initminer').private_key
    sig_digest = generate_sig_digest(trx, initminer_private_key)
    response = node.api.database.verify_signatures(hash=sig_digest, signatures=trx['signatures'],
                                                   required_owner=[], required_active=['initminer'],
                                                   required_posting=[], required_other=[])['valid']
    assert response is not False


def test_list_proposals(node, wallet):
    create_account_and_fund_it(wallet, 'alice')
    wallet.api.transfer('initminer', 'alice', Asset.Tbd(100), 'test memo')
    create_proposal(wallet, 'alice')
    proposals = node.api.database.list_proposals(start=["alice"], limit=100, order='by_creator',
                                                 order_direction='ascending', status='all')['proposals']
    assert len(proposals) != 0


