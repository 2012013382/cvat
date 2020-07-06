
# Copyright (C) 2020 Intel Corporation
#
# SPDX-License-Identifier: MIT

import argparse
import logging as log
import os.path as osp

from datumaro.components.project import Project
from datumaro.components.operations import merge_datasets

from ..util import at_least, MultilineFormatter, CliException
from ..util.project import generate_next_dir_name, load_project


def build_parser(parser_ctor=argparse.ArgumentParser):
    parser = parser_ctor(help="Merge few projects",
        description="""
            Merges multiple datasets into one. This can be useful if you
            have few annotations and wish to merge them,
            taking into consideration potential overlaps and conflicts.
            This command can try to find a common ground by voting or
            return a list of conflicts.|n
            |n
            Examples:|n
            - Merge annotations from 3 (or more) annotators:|n
            |s|smerge project1/ project2/ project3/
        """,
        formatter_class=MultilineFormatter)

    parser.add_argument('project', nargs='+', action=at_least(2),
        help="Path to a project (repeatable)")
    parser.add_argument('-iou', '--iou-thresh', default=0.5, type=float,
        help="IoU match threshold for segments (default: %(default)s)")
    parser.add_argument('-nms', action='store_true',
        help="Run non-maxima suppression algorithm prior to merging")
    parser.add_argument('-iconf', '--input-conf-thresh',
        default=0.25, type=float,
        help="Confidence threshold for input "
            "annotations (default: %(default)s)")
    parser.add_argument('-oconf', '--output-conf-thresh',
        default=0.0, type=float,
        help="Confidence threshold for output "
            "annotations (default: %(default)s)")
    parser.add_argument('--consensus', default=0, type=int,
        help="Minimum count for a label and attribute voting "
            "results to be counted (default: %(default)s)")
    parser.add_argument('-o', '--output-dir', dest='dst_dir', default=None,
        help="Output directory (default: current project's dir)")
    parser.add_argument('--overwrite', action='store_true',
        help="Overwrite existing files in the save directory")
    parser.set_defaults(command=merge_command)

    return parser

def merge_command(args):
    source_projects = [load_project(p) for p in args.project]

    dst_dir = args.dst_dir
    if dst_dir:
        if not args.overwrite and osp.isdir(dst_dir) and os.listdir(dst_dir):
            raise CliException("Directory '%s' already exists "
                "(pass --overwrite to overwrite)" % dst_dir)
    else:
        dst_dir = generate_next_dir_name('merged')

    source_datasets = []
    for p in source_projects:
        log.debug("Loading project '%s' dataset", p.config.project_name)
        source_datasets.append(p.make_dataset())

    merged_dataset = merge_datasets(source_datasets,
        iou_threshold=args.iou_thresh, conf_threshold=args.input_conf_thresh,
        output_conf_thresh=args.output_conf_thresh,
        consensus=args.consensus, do_nms=args.nms)

    merged_project = Project()
    output_dataset = merged_project.make_dataset()
    output_dataset.define_categories(merged_dataset.categories())
    merged_dataset = output_dataset.update(merged_dataset)
    merged_dataset.save(save_dir=dst_dir)

    dst_dir = osp.abspath(dst_dir)
    log.info("Merge results have been saved to '%s'" % dst_dir)

    return 0
