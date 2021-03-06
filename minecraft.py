#!/usr/bin/python3

import subprocess
from time import time, sleep


class MinecraftServer():
    def __init__(self, required_prefix=None):
        self.pane_id = None
        self.path = None
        # find server pane
        cmd = "tmux list-panes -aF \"#{pane_id} #{pane_current_command} #{pane_current_path}\""
        panes = subprocess.check_output(cmd, shell=True).decode()
        for p in panes.split('\n'):
            if "java" in p and "minecraft" in p and (required_prefix is None or required_prefix in p):
                self.pane_id = p.split()[0]
                self.path = p[p.find("/"):]
        assert self.pane_id is not None, "Minecraft freebox server not found"

    def _command(self, sent_cmd):
        cmd = "tmux send-keys -t %s \"%s\" C-m" % (self.pane_id, sent_cmd)
        subprocess.call(cmd, shell=True)
        # TODO REMOVE
        sleep(0.1)
        cmd = "tmux capture-pane -p -t %s" % (self.pane_id)
        output = subprocess.check_output(cmd, shell=True).decode()
        output_lines = output.split("\n")
        nb_lines = len(output_lines)
        for iline in range(nb_lines - 1, 0, -1):
            if output_lines[iline] == sent_cmd:
                return [a for a in output_lines[iline + 1:] if len(a) > 0]
        print("Couldn't find output in the %s last lines!" % (nb_lines))
        return ""

    def set_command_block_output(self, b):
        self._command("gamerule commandBlockOutput %s" % ("false" if not b else "true"))

    # check if a block is of given type
    def is_block(self, p, type_, subtype=None):
        cmd = "testforblock %d %d %d minecraft:%s" % (p[0], p[1], p[2], type_)
        if subtype is not None:
            cmd += " %s" % subtype
        ret = self._command(cmd)
        if "Successfully found" in ret[0]:
            return True
        return False

    def is_stone_button_state(self, p, state):
        return self.is_block(p, "stone_button", state)

    def is_stone_button_released(self, p):
        return self.is_stone_button_state(p, 5)

    def is_stone_button_pressed(self, p):
        return self.is_stone_button_state(p, 13)

    # set a range of blocks
    # replace blocks with old_type, old_data by blocks with new_type, new_data
    # in the selected region
    def replace(self, p1, p2, new_type, new_data, old_type="", old_data=None):
        if not new_type.startswith("minecraft:"):
            new_type = "minecraft:" + new_type
        if old_type != "" and not old_type.startswith("minecraft:"):
            old_type = "minecraft:" + old_type
        self._command("fill %d %d %d %d %d %d %s %d replace %s %s" %
                      (p1[0], p1[1], p1[2], p2[0], p2[1], p2[2],
                       new_type, new_data, old_type,
                       "" if old_data is None else int(old_data)))

    def particle(self, part_type, p1, p2, speed, count):
        self._command("particle %s %d %d %d %d %d %d %f %d" %
                      (part_type, p1[0], p1[1], p1[2], p2[0], p2[1], p2[2], speed, count))
