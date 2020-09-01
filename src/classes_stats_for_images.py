import os
import supervisely_lib as sly
import random
from collections import defaultdict
import pandas as pd
import json
import numpy as np
# <!--    <sly-notification content="<Текст нотификации в маркдауне>" :options="{ type: 'note|info|warning|error', name: '<заголовок нотификации>'}" />-->


my_app = sly.AppService()

TEAM_ID = int(os.environ['modal.state.teamId'])
WORKSPACE_ID = int(os.environ['modal.state.workspaceId'])
PROJECT_ID = os.environ.get('modal.state.inputProjectId', None)
DATASET_ID = os.environ.get('modal.state.inputDatasetId', None)
SAMPLE_PERCENT = int(os.environ['modal.state.samplePercent'])
BG_COLOR = [0, 0, 0]
BATCH_SIZE = 1

progress = 0


def _col_name(name, color, icon):
    return '<b style="display: inline-block; border-radius: 50%; ' \
           'background: {}; width: 8px; height: 8px"></b> {} ' \
           ' <i class="zmdi {}" style="color:{};margin-right:3px"></i>'.format(color, name, icon, color)


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



@sly.timeit
@my_app.callback("calc")
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
    table_columns = ["id", "dataset", "name", "height", "width", "channels", "unlabeled"]
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
                    table_row.append(stat_area[class_name])
                    table_row.append(stat_count[class_name])

                if len(table_row) != len(table_columns):
                    raise RuntimeError("Values for some columns are missed")
                batch_stats.append(table_row)

            all_stats.extend(batch_stats)

            progress += len(batch_stats)
            payload = {
                "progress": int(progress * 100 / sample_count),
                "table": {
                    "data": batch_stats
                }
            }
            api.task.set_field(task_id, "data.progress", payload)
            api.task.set_field(task_id, "data.table.data", payload, append=True)

            task_progress.iters_done_report(len(batch_stats))


def main():
    sly.logger.info("Script arguments", extra={"teamId: ": TEAM_ID, "workspaceId: ": WORKSPACE_ID,
                                               "projectId": PROJECT_ID,"datasetId": DATASET_ID,
                                               "samplePercent": SAMPLE_PERCENT})

    api = sly.Api.from_env()
    # df = pd.DataFrame(
    #     [["a", "b"], ["c", "d"]],
    #     index=["row 1", "row 2"],
    #     columns=["col 1", "col 2"],
    # )
    # print(json.dumps(df.to_json(orient='split')))

    data = {
        # "table": [
        #     {"a": 1, "b": 10},
        #     {"a": 2, "b": 20},
        #     {"a": 3, "b": 30},
        # ],
        # "table": {
        #     "columns": ["b", "a"],
        #     "data": [
        #         [1, 10],
        #         [2, 20],
        #         [3, 30],
        #     ]
        # },
        "table": {
            "columns": [],
            "data": []
        },
        "progress": progress
    }

    state = {
        "test": 12,
        "perPage": 20,
        "pageSizes": [5, 10, 30, 50, 100],
    }

    initial_events = [
        {
            "state": None,
            "context": None,
            "command": "calc",
        }
    ]
    #initial_events = []


    # Run application service
    my_app.run(data=data, state=state, initial_events=initial_events)


if __name__ == "__main__":
    sly.main_wrapper("main", main)



# Area:
# <i class="zmdi zmdi-time-interval"></i>
# <i class="zmdi zmdi-format-color-fill"></i>
# Count
# <i class="zmdi zmdi-collection-item-7"></i>
# <i class="zmdi zmdi-n-3-square"></i>
# <i class="zmdi zmdi-equalizer"></i>
# <i class="zmdi zmdi-chart"></i>

# #http://host.robots.ox.ac.uk/pascal/VOC/voc2012/dbstats.html