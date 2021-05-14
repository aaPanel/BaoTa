# -*- coding: utf-8 -*-

from qiniu.utils import entry


def build_op(cmd, first_arg, **kwargs):
    op = [cmd]
    if first_arg is not None:
        op.append(first_arg)

    for k, v in kwargs.items():
        op.append('{0}/{1}'.format(k, v))

    return '/'.join(op)


def pipe_cmd(*cmds):
    return '|'.join(cmds)


def op_save(op, bucket, key):
    return pipe_cmd(op, 'saveas/' + entry(bucket, key))
