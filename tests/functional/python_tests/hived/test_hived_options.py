from os import remove
from os.path import join
from pathlib import Path

import pytest

from test_tools import World


def test_dump_config(world: World):
    node = world.create_init_node()
    old_config = dict()
    for key, value in node.config.__dict__.items():
        old_config[key] = value
    node.run()
    node.wait_number_of_blocks(2)
    node.close()
    node.dump_config()
    assert node.config.__dict__ == old_config


def test_no_appearance_of_deprecated_flag_exception_in_run_without_flag_exit_after_replay(world: World):
    node = world.create_init_node()
    node.run()

    with open(node.directory / 'stderr.txt') as file:
        stderr = file.read()

    warning = "flag `--exit-after-replay` is deprecated, please consider usage of `--exit-before-sync`"
    assert warning not in stderr


def test_appearance_of_deprecated_flag_exception_in_run_with_flag_exit_after_replay(world: World, block_log: Path):
    node = world.create_api_node()
    half_way = int(BLOCK_COUNT / 2.0)

    node.run(replay_from=block_log, stop_at_block=half_way, with_arguments=['--exit-after-replay'])

    with open(node.directory / 'stderr.txt') as file:
        stderr = file.read()

    warning = "flag `--exit-after-replay` is deprecated, please consider usage of `--exit-before-sync`"
    assert warning in stderr


@pytest.mark.parametrize("param1, param2", [(False, ['--exit-after-replay']), (True, "")])
def test_stop_after_replay(param1, param2, world: World, block_log: Path):
    node = world.create_api_node()
    half_way = int(BLOCK_COUNT / 2.0)
    node.run(replay_from=block_log, stop_at_block=half_way,  exit_before_synchronization=param1, with_arguments=param2)
    assert not node.is_running()


@pytest.mark.parametrize("param1, param2", [(False, ['--exit-after-replay']), (True, "")])
def test_stop_after_replay_with_second_node_in_network(param1, param2, world: World, block_log: Path):
    net = world.create_network()
    node = net.create_api_node()

    background_node = net.create_init_node()
    background_node.run(replay_from=block_log, wait_for_live=True)
    background_node.wait_number_of_blocks(6)

    node.run(replay_from=block_log, exit_before_synchronization=param1, with_arguments=param2)
    assert not node.is_running()

    background_node.close()
    node.run(wait_for_live=False)
    assert node.get_last_block_number() == BLOCK_COUNT + 3


@pytest.mark.parametrize("param1, param2", [(False, ['--exit-after-replay']), (True, "")])
def test_stop_after_replay_in_load_from_snapshot(param1, param2, world: World, block_log: Path):
    node = world.create_api_node()
    node.run(replay_from=block_log,  exit_before_synchronization=param1, with_arguments=param2)
    snap = node.dump_snapshot(close=True)
    remove(join(str(node.directory), 'blockchain', 'shared_memory.bin'))
    node.run(load_snapshot_from=snap,  exit_before_synchronization=param1, with_arguments=param2)
    assert not node.is_running()
