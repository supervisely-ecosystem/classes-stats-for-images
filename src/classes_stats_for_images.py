import os
import supervisely_lib as sly
import random
from collections import defaultdict
import pandas as pd
import json
import numpy as np

my_app = sly.AppService()

TEAM_ID = int(os.environ['modal.state.teamId'])
WORKSPACE_ID = int(os.environ['modal.state.workspaceId'])
PROJECT_ID = os.environ.get('modal.state.inputProjectId', None)
DATASET_ID = os.environ.get('modal.state.inputDatasetId', None)
SAMPLE_PERCENT = int(os.environ['modal.state.samplePercent'])
BG_COLOR = [0, 0, 0]
BATCH_SIZE = 15

progress = 0


def _col_name(name, color, icon):
    hexcolor=sly.color.rgb2hex(color)
    return '<div style="color:{}"><i class="zmdi {}" style="margin-right:3px"></i> {} </div>'.format(hexcolor, icon, name)


def get_col_name_area(name, color):
    return _col_name(name, color, "zmdi-time-interval")


def get_col_name_count(name, color):
    return _col_name(name, color, "zmdi-equalizer")


def sample_images(api, datasets):
    all_images = []
    for dataset in datasets:
        images = api.image.get_list(dataset.id)
        all_images.extend(images)

    if SAMPLE_PERCENT != 100:
        cnt_images = int(max(1, SAMPLE_PERCENT * len(all_images) / 100))
        random.shuffle(all_images)
        all_images = all_images[:cnt_images]

    ds_images = defaultdict(list)
    for image_info in all_images:
        ds_images[image_info.dataset_id].append(image_info)
    return ds_images, cnt_images

# def convert_to_columns_view(data_info, class_names, col_name_func):
#     result = []
#     for class_name in class_names:


@my_app.callback("calc")
@sly.timeit
def calc(api: sly.Api, task_id, context, state, app_logger):
    global progress

    project = None
    datasets = []
    if PROJECT_ID is not None:
        project = api.project.get_info_by_id(PROJECT_ID)
        datasets = api.dataset.get_list(PROJECT_ID)
    elif DATASET_ID is not None:
        dataset = api.dataset.get_info_by_id(DATASET_ID)
        datasets = [dataset]
        project = api.project.get_info_by_id(dataset.project_id)
    else:
        raise ValueError("Both project and dataset are not defined.")

    meta_json = api.project.get_meta(project.id)
    meta = sly.ProjectMeta.from_json(meta_json)
    colors_warning = meta.obj_classes.validate_classes_colors()

    # list classes
    class_names = ["unlabeled"]
    class_colors = [[0, 0, 0]]
    class_indices_colors = [[0, 0, 0]]
    _name_to_index = {}
    table_columns = ["id", "dataset", "image", "height", "width", "channels", "unlabeled"]
    for idx, obj_class in enumerate(meta.obj_classes):
        class_names.append(obj_class.name)
        class_colors.append(obj_class.color)
        class_index = idx + 1
        class_indices_colors.append([class_index, class_index, class_index])
        _name_to_index[obj_class.name] = class_index
        table_columns.append(get_col_name_area(obj_class.name, obj_class.color))
        table_columns.append(get_col_name_count(obj_class.name, obj_class.color))

    api.task.set_field(task_id, "data.table.columns", table_columns)

    ds_images, sample_count = sample_images(api, datasets)
    all_stats = []
    task_progress = sly.Progress("Stats", sample_count, app_logger)
    for dataset_id, images in ds_images.items():
        #@TODO: debug batch size
        for batch in sly.batched(images, batch_size=BATCH_SIZE):
            batch_stats = []

            image_ids = [image_info.id for image_info in batch]
            ann_infos = api.annotation.download_batch(dataset_id, image_ids)
            ann_jsons = [ann_info.annotation for ann_info in ann_infos]

            for info, ann_json in zip(batch, ann_jsons):
                ann = sly.Annotation.from_json(ann_json, meta)

                render_idx_rgb = np.zeros(ann.img_size + (3,), dtype=np.uint8)
                render_idx_rgb[:] = BG_COLOR
                ann.draw_class_idx_rgb(render_idx_rgb, _name_to_index)
                stat_area = sly.Annotation.stat_area(render_idx_rgb, class_names, class_indices_colors)
                stat_count = ann.stat_class_count(class_names)

                table_row = []
                table_row.append(info.id)
                table_row.append(dataset.name)
                table_row.append('<a href="{0}" rel="noopener noreferrer" target="_blank">{1}</a>'
                                 .format(api.image.url(TEAM_ID, WORKSPACE_ID, project.id, dataset.id, info.id), info.name))
                table_row.extend([stat_area["height"], stat_area["width"], stat_area["channels"], stat_area["unlabeled"]])
                for class_name in class_names:
                    if class_name == "unlabeled":
                        continue
                    table_row.append(round(stat_area[class_name], 2))
                    table_row.append(round(stat_count[class_name], 2))

                if len(table_row) != len(table_columns):
                    raise RuntimeError("Values for some columns are missed")
                batch_stats.append(table_row)

            all_stats.extend(batch_stats)

            progress += len(batch_stats)

            fields = [
                {
                    "field": "data.progress",
                    "payload": int(progress * 100 / sample_count)
                },
                {
                    "field": "data.table.data",
                    "payload": batch_stats,
                    "append": True
                }
            ]
            api.task.set_fields(task_id, fields)
            task_progress.iters_done_report(len(batch_stats))


def main():
    sly.logger.info("Script arguments", extra={"teamId: ": TEAM_ID, "workspaceId: ": WORKSPACE_ID,
                                               "projectId": PROJECT_ID,"datasetId": DATASET_ID,
                                               "samplePercent": SAMPLE_PERCENT})

    api = sly.Api.from_env()

    data = {
        "table": {
            "columns": [],
            "data": []
        },
        "progress": progress
    }

    state = {
        "test": 12,
        "perPage": 10,
        "pageSizes": [10, 15, 30, 50, 100],
    }

    initial_events = [
        {
            "state": None,
            "context": None,
            "command": "calc",
        }
    ]

    # Run application service
    my_app.run(data=data, state=state, initial_events=initial_events)


if __name__ == "__main__":
    sly.main_wrapper("main", main)



# Icons:
# <i class="zmdi zmdi-time-interval"></i>
# <i class="zmdi zmdi-format-color-fill"></i>
# Count
# <i class="zmdi zmdi-collection-item-7"></i>
# <i class="zmdi zmdi-n-3-square"></i>
# <i class="zmdi zmdi-equalizer"></i>
# <i class="zmdi zmdi-chart"></i>

#Pascal stats
# #http://host.robots.ox.ac.uk/pascal/VOC/voc2012/dbstats.html