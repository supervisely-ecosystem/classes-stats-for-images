import os
import supervisely_lib as sly
import random
from collections import defaultdict
import pandas as pd
import json
import numpy as np
import plotly.graph_objects as go
#import plotly.express as px

my_app = sly.AppService()

TEAM_ID = int(os.environ['modal.state.teamId'])
WORKSPACE_ID = int(os.environ['modal.state.workspaceId'])
PROJECT_ID = os.environ.get('modal.state.inputProjectId', None)
DATASET_ID = os.environ.get('modal.state.inputDatasetId', None)
SAMPLE_PERCENT = int(os.environ['modal.state.samplePercent'])
BG_COLOR = [0, 0, 0]
BATCH_SIZE = 50

progress = 0
sum_class_area_per_image = []
sum_class_count_per_image = []
count_images_with_class = []
resolutions_count = defaultdict(int)


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

    cnt_images = len(all_images)
    if SAMPLE_PERCENT != 100:
        cnt_images = int(max(1, SAMPLE_PERCENT * len(all_images) / 100))
        random.shuffle(all_images)
        all_images = all_images[:cnt_images]

    ds_images = defaultdict(list)
    for image_info in all_images:
        ds_images[image_info.dataset_id].append(image_info)
    return ds_images, cnt_images


@my_app.callback("calc")
@sly.timeit
def calc(api: sly.Api, task_id, context, state, app_logger):
    global progress, sum_class_area_per_image, sum_class_count_per_image, count_images_with_class

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

    fields = [
        {
            "field": "data.projectName",
            "payload": project.name
        },
        {
            "field": "data.projectId",
            "payload": project.id,
        }
    ]
    api.task.set_fields(task_id, fields)

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

    sum_class_area_per_image = [0] * len(class_names)
    sum_class_count_per_image = [0] * len(class_names)
    count_images_with_class = [0] * len(class_names)
    count_images_with_class[0] = 1  # for unlabeled

    api.task.set_field(task_id, "data.table.columns", table_columns)

    ds_images, sample_count = sample_images(api, datasets)
    all_stats = []
    task_progress = sly.Progress("Stats", sample_count, app_logger)
    for dataset_id, images in ds_images.items():
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
                table_row.extend([stat_area["height"],
                                  stat_area["width"],
                                  stat_area["channels"],
                                  round(stat_area["unlabeled"], 2)])
                resolutions_count["{}x{}x{}".format(stat_area["height"], stat_area["width"], stat_area["channels"])] += 1
                for idx, class_name in enumerate(class_names):
                    sum_class_area_per_image[idx] += stat_area[class_name]
                    sum_class_count_per_image[idx] += stat_area[class_name]
                    if class_name == "unlabeled":
                        continue
                    count_images_with_class[idx] += 1 if stat_count[class_name] > 0 else 0
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

    # average nonzero class area per image
    avg_nonzero_area = np.divide(sum_class_area_per_image, count_images_with_class)
    avg_nonzero_count = np.divide(sum_class_count_per_image, count_images_with_class)
    fig = go.Figure(
        data=[
            go.Bar(name='Area %', x=class_names, y=avg_nonzero_area, yaxis='y', offsetgroup=1),
            go.Bar(name='Count', x=class_names, y=avg_nonzero_count, yaxis='y2', offsetgroup=2)
        ],
        layout={
            'yaxis': {'title': 'Area'},
            'yaxis2': {'title': 'Count', 'overlaying': 'y', 'side': 'right'}
        }
    )
    # Change the bar mode
    fig.update_layout(barmode='group')  # , legend_orientation="h")


    # images count with/without classes
    images_with_count = []
    images_without_count = []
    images_with_count_text = []
    images_without_count_text = []
    for idx, class_name in enumerate(class_names):
        if class_name == "unlabeled":
            continue
        with_count = count_images_with_class[idx]
        without_count = sample_count - with_count
        images_with_count.append(with_count)
        images_without_count.append(without_count)
        images_with_count_text.append("{} ({:.2f} %)".format(with_count, with_count * 100 / sample_count))
        images_without_count_text.append("{} ({:.2f} %)".format(without_count, without_count * 100 / sample_count))

    fig_with_without_count = go.Figure(
        data=[
            go.Bar(name='# of images that have class', x=class_names, y=images_with_count, text=images_with_count_text),
            go.Bar(name='# of images that do not have class', x=class_names, y=images_without_count, text=images_without_count_text)
        ],
    )
    fig_with_without_count.update_layout(barmode='stack')  # , legend_orientation="h")

    # barchart resolution
    resolution_labels = []
    resolution_values = []
    resolution_percent = []
    for label, value in sorted(resolutions_count.items(), key=lambda item: item[1], reverse=True):
        resolution_labels.append(label)
        resolution_values.append(value)
    if len(resolution_labels) > 10:
        resolution_labels = resolution_labels[:10]
        resolution_labels.append("other")
        other_value = sum(resolution_values[10:])
        resolution_values = resolution_values[:10]
        resolution_values.append(other_value)
    resolution_percent = [round(v * 100 / sample_count) for v in resolution_values]

    #df_resolution = pd.DataFrame({'resolution': resolution_labels, 'count': resolution_values, 'percent': resolution_percent})
    pie_resolution = go.Figure(data=[go.Pie(labels=resolution_labels, values=resolution_values)])
    #pie_resolution = px.pie(df_resolution, names='resolution', values='count')

    fields = [
        {
            "field": "data.avgAreaCount",
            "payload": json.loads(fig.to_json())
        },
        {
            "field": "data.imageWithClassCount",
            "payload": json.loads(fig_with_without_count.to_json())
        },
        {
            "field": "data.resolutionsCount",
            "payload": json.loads(pie_resolution.to_json())
        },
        {
            "field": "data.resolutionsCount",
            "payload": json.loads(pie_resolution.to_json())
        },
        {
            "field": "data.loading1",
            "payload": False
        },
        {
            "field": "data.loading2",
            "payload": False
        },
        {
            "field": "data.loading3",
            "payload": False
        }
    ]
    api.task.set_fields(task_id, fields)

    #@TODO: hotfix - pie chart do not refreshes automatically
    fields = [
        {
            "field": "data.resolutionsCount",
            "payload": json.loads(pie_resolution.to_json())
        }
    ]
    api.task.set_fields(task_id, fields)
    fields = [
        {
            "field": "data.resolutionsCount",
            "payload": json.loads(pie_resolution.to_json())
        }
    ]
    api.task.set_fields(task_id, fields)


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
        "progress": progress,
        "loading1": True,
        "loading2": True,
        "loading3": True,
        "avgAreaCount": json.loads(go.Figure().to_json()),
        "imageWithClassCount": json.loads(go.Figure().to_json()),
        "resolutionsCount": json.loads(go.Figure().to_json()),
        "projectName": "",
        "projectId": ""
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
        },
        {
            "state": None,
            "context": None,
            "command": "stop",
        }
    ]

    # Run application service
    my_app.run(data=data, state=state, initial_events=initial_events)


if __name__ == "__main__":
    sly.main_wrapper("main", main)
