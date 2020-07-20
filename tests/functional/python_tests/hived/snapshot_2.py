#!/usr/bin/python3

import sys
import os
import tempfile
import argparse

sys.path.append("../../")

import hive_utils
from hive_utils.resources.configini import config as configuration
from hive_utils.common import wait_n_blocks, wait_for_node


parser = argparse.ArgumentParser()
parser.add_argument("--run-hived", dest="hived", help = "Path to hived executable", required=True, type=str)
parser.add_argument("--block-log", dest="block_log_path", help = "Path to block log", required=False, type=str, default=None)
parser.add_argument("--blocks", dest="blocks", help = "Blocks to replay", required=False, type=int, default=1000)
parser.add_argument("--leave", dest="leave", action='store_true')

args = parser.parse_args()
node = None

assert args.hived

# working dir
from uuid import uuid5, NAMESPACE_URL
from random import randint
work_dir = os.path.join( tempfile.gettempdir(), uuid5(NAMESPACE_URL,str(randint(0, 1000000))).__str__().replace("-", ""))
os.mkdir(work_dir)


# config paths
config_file_name = 'config.ini'
path_to_config = os.path.join(work_dir, config_file_name)

# snapshot dir
snapshot_root = os.path.join(work_dir, "snapshots")
# os.mkdir(snapshot_root)

# (optional) setting up block log
blockchain_dir = os.path.join(work_dir, "blockchain")
os.mkdir( blockchain_dir )
if args.block_log_path:
	os.symlink(args.block_log_path, os.path.join(blockchain_dir, "block_log"))
else:
	from hive_utils.common import get_testnet_block_log
	get_testnet_block_log(os.path.join(blockchain_dir, "block_log"))

# config
config = configuration()
config.witness = None	# no witness
config.private_key = None	# also no prv key
config.snapshot_root_dir = snapshot_root
config.plugin = config.plugin + " state_snapshot"	# this plugin is required

# config generation
config.generate(path_to_config)

def get_base_hv_args():
	return [ "--stop-replay-at-block", str(args.blocks), "--exit-after-replay" ].copy()

def dump_snapshot(Node, snapshot_name):
# setup for snapshot
	hv_args = get_base_hv_args()
	hv_args.extend(["--dump-snapshot", snapshot_name])
	Node.hived_args = hv_args
# creating snapshot
	wait_for_node(Node, "creating snapshot '{}' ...".format(snapshot_name))

def load_snapshot(Node, snapshot_name):
# setup for loading snapshot
	hv_args = get_base_hv_args()
	hv_args.extend(["--load-snapshot", snapshot_name])
	Node.hived_args = hv_args
	os.remove(os.path.join(blockchain_dir, "shared_memory.bin"))
# loading snapshot
	wait_for_node(Node, "loading snapshot '{}' ...".format(snapshot_name))

def run_for_n_blocks(Node, blocks : int, additional_args : list = []):
	args.blocks += blocks
	Node.hived_args = get_base_hv_args()
	if len(additional_args) > 0:
		Node.hived_args.extend(additional_args)
	wait_for_node(Node, "waiting for {} blocks...".format(int(args.blocks)))


def require_success(node):
	assert node.last_returncode == 0

def require_fail(node):
	assert node.last_returncode == 0

hv_args = get_base_hv_args()
hv_args.append("--replay-blockchain")

# setup for replay
node = hive_utils.hive_node.HiveNode(
	args.hived,
	work_dir, 
	hv_args
)

# replay
wait_for_node(node, "waiting for replay of {} blocks...".format(int(args.blocks)))
require_success(node)
print("replay completed, creating snapshot")


# try to create snapshot, while directory not exist
assert not os.path.exists(snapshot_root)
dump_snapshot(node, "snap_1")
require_success(node)
assert os.path.exists(snapshot_root)
assert os.path.exists(os.path.join(snapshot_root, "snap_1"))

# load snapshot
load_snapshot(node, "snap_1")
require_success(node)

# check is replaying 
run_for_n_blocks(node, 100, ["--replay-blockchain"])
require_success(node)

# dump to same directory
dump_snapshot(node, "snap_1")
require_fail(node)
from shutil import rmtree
rmtree(os.path.join(config.snapshot_root_dir, "snap_1"))
dump_snapshot(node, "snap_1")
require_success(node)

# load snapshot
load_snapshot(node, "snap_1")
require_success(node)

# check is replaying 
run_for_n_blocks(node, 100, ["--replay-blockchain"])
require_success(node)

print("success")


if not args.leave:
	from shutil import rmtree
	rmtree( work_dir )
	print("deleted: {}".format(work_dir))
else:
	print("datadir not deleted: {}".format(work_dir))

exit(0)