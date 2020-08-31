import os
import supervisely_lib as sly
import random
from collections import defaultdict

my_app = sly.AppService()

TEAM_ID = int(os.environ['modal.state.teamId'])
WORKSPACE_ID = int(os.environ['modal.state.workspaceId'])
PROJECT_ID = os.environ.get('modal.state.projectId', None)
DATASET_ID = os.environ.get('modal.state.datasetId', None)
SAMPLE_PERCENT = int(os.environ['modal.state.samplePercent'])


def validate_classes_colors(project_meta: sly.ProjectMeta):
    # check colors uniq
    color_names = defaultdict(list)
    for obj_class in project_meta.obj_classes:
        hex = sly.color.rgb2hex(obj_class.color)
        color_names[hex].append(obj_class.name)

    class_colors_notify = ""
    for k, v in color_names.items():
        if len(v) > 1:
            warn_str = "Classes {!r} have the same RGB color = {!r}".format(v, sly.color.hex2rgb(k))
            sly.logger.warn(warn_str)
            class_colors_notify += warn_str + '\n\n'
    if class_colors_notify != "":
        widgets.append(
            api.report.create_notification("Classes colors", class_colors_notify, sly.NotificationType.WARNING))

@sly.timeit
@my_app.callback("calc")
def calc(api: sly.Api, task_id, context, state, app_logger):
    project = None
    datasets = []
    if PROJECT_ID is not None:
        project = api.project.get_info_by_id(PROJECT_ID)
        datasets = api.dataset.get_list(PROJECT_ID)
    elif DATASET_ID is not None:
        dataset = api.dataset.get_info_by_id(DATASET_ID)
        datasets = [dataset]
        project = api.project.get_info_by_id(dataset.project_id)

    meta_json = api.project.get_meta(project.id)
    meta = sly.ProjectMeta.from_json(meta_json)



    all_images = []
    for dataset in datasets:
        images = api.image.get_list(dataset.id)
        all_images.extend(images)

    if SAMPLE_PERCENT != 100:
        cnt_images = max(1, SAMPLE_PERCENT * len(all_images) / 100)
        random.shuffle(all_images)
        all_images = all_images[:cnt_images]

    ds_images = defaultdict(list)
    for image_info in all_images:
        ds_images[image_info.dataset_id].append(image_info)

    all_stats = []
    for dataset_id, images in ds_images.items():
        for batch in sly.batched(images):
            stats = []
            for image_info in batch:





def main():
    sly.logger.info("Script arguments", extra={"teamId: ": TEAM_ID, "workspaceId: ": WORKSPACE_ID,
                                               "projectId": PROJECT_ID,"datasetId": DATASET_ID,
                                               "samplePercent": SAMPLE_PERCENT})

    api = sly.Api.from_env()

    data = {
        "table": [
            {"a": 1, "b": 10},
            {"a": 2, "b": 20},
            {"a": 3, "b": 30},
        ],

    }

    state = {
        "test": 12,
        "perPage": 20,
        "pageSizes": [5, 10, 30, 50, 100],
        "progress": 20
    }

    initial_events = [
        {
            "state": None,
            "context": None,
            "command": "calc"
        }
    ]

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