import os
import supervisely_lib as sly

my_app = sly.AppService()

# @my_app.callback("manual_selected_figure_changed")
# @sly.timeit
# def manual_selected_figure_changed(api: sly.Api, task_id, context, state, app_logger):
#     pass
#     #_refresh_upc(api, task_id, context, state, app_logger)

def main():
    api = sly.Api.from_env()

    data = {
    }

    state = {
        "test": 12,
    }

    # # start event after successful service run
    # events = [
    #     {
    #         "state": {},
    #         "context": {},
    #         "command": "calculate"
    #     }
    # ]

    # Run application service
    my_app.run(data=data, state=state)


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
#
# # coding: utf-8
#
# import numpy as np
# from collections import defaultdict
# import supervisely_lib as sly
# import json
# import pandas as pd
# import os
# import plotly.express as px
# import plotly.graph_objects as go
# import plotly.offline as po
# import random
#
#
# # workspace_id = '%%WORKSPACE_ID%%'
# # project_name = '%%IN_VIDEO_PROJECT_NAME%%'
# # src_dataset_ids = '%%DATASET_IDS:None%%'
# # sample_ratio = '%%SAMPLE_RATIO:None%%'
#
# # workspace_id = '1'
# # project_name = 'pascal_colors'
# # src_dataset_ids = 'None'
# # sample_ratio = '0.01'
#
#
# team_id = int(os.environ['modal.state.teamId'])
# workspace_id = int(os.environ['modal.state.workspaceId'])
# project_id = int(os.environ['modal.state.projectId'])
# sample_percentage = int(os.environ['modal.state.samplePercentage'])
#
# sly.logger.info("Script arguments",
#                 extra={"teamId: ": team_id,
#                        "workspaceId: ": workspace_id,
#                        "projectId": project_id,
#                        "samplePercentage": sample_percentage})
#
# BG_COLOR = [0, 0, 0]
# api = sly.Api.from_env()
#
# widgets = []
#
# project = api.project.get_info_by_id(project_id)
# if project is None:
#     raise RuntimeError("Project (ID={!r}) not found".format(project_id))
# if project.type != str(sly.ProjectType.IMAGES):
#     raise RuntimeError('Project {!r} has type {!r}. This app works only with project type {!r}'
#                        .format(project.name, project.type, str(sly.ProjectType.IMAGES)))
#
# meta_json = api.project.get_meta(project.id)
# meta = sly.ProjectMeta.from_json(meta_json)
#
# # list classes
# class_names = []
# class_colors = []
# class_indices = [] # 0 - for unlabeled area
# class_indices_colors = []
# _name_to_index = {}
# for idx, obj_class in enumerate(meta.obj_classes):
#     class_names.append(obj_class.name)
#     class_colors.append(obj_class.color)
#     class_index = idx + 1
#     class_indices.append(class_index)
#     class_indices_colors.append([class_index, class_index, class_index])
#     _name_to_index[obj_class.name] = class_index
#
#
# # list tags
# tag_names = []
# tag_colors = []
# for tag_meta in meta.tag_metas:
#     tag_names.append(tag_meta.name)
#     tag_colors.append(tag_meta.color)
#
#
# # check colors uniq
# color_names = defaultdict(list)
# for name, color in zip(class_names, class_colors):
#     hex = sly.color.rgb2hex(color)
#     color_names[hex].append(name)
#
# class_colors_notify = ""
# for k, v in color_names.items():
#     if len(v) > 1:
#         warn_str = "Classes {!r} have the same RGB color = {!r}".format(v, sly.color.hex2rgb(k))
#         sly.logger.warn(warn_str)
#         class_colors_notify += warn_str + '\n\n'
# if class_colors_notify != "":
#     widgets.append(api.report.create_notification("Classes colors", class_colors_notify, sly.NotificationType.WARNING))
#
#
# all_images = []
# image_dataset = []
# for dataset in api.dataset.get_list(project.id):
#     if src_dataset_ids is not None and dataset.id not in src_dataset_ids:
#         continue
#     images = api.image.get_list(dataset.id)
#     all_images.extend(images)
#     temp_dataset = [dataset] * len(images)
#     image_dataset.extend(temp_dataset)
# img_ds_pairs = list(zip(all_images, image_dataset))
# if len(img_ds_pairs) == 0:
#     raise RuntimeError("0 items to process")
#
# if sample_ratio is not None:
#     random.shuffle(img_ds_pairs)
#     sample_count = max(int(len(img_ds_pairs) * sample_ratio), 1)
#     sample_count = min(len(img_ds_pairs), sample_count)
#     img_ds_pairs = img_ds_pairs[:sample_count]
#
#
# ds_to_images = defaultdict(list)
# ds_id_to_info = {}
# for image_info, dataset_info in img_ds_pairs:
#     ds_to_images[dataset_info.id].append(image_info)
#     ds_id_to_info[dataset_info.id] = dataset_info
#
# total_images_in_project = 0
# stats_area = []
# stats_count = []
# stats_img_tags = []
#
#
# ds_progress = sly.Progress('Processing', total_cnt=len(img_ds_pairs))
# for dataset_id, dataset in ds_id_to_info.items():
#     images = ds_to_images[dataset.id]
#
#     for batch in sly.batched(images):
#         image_ids = [image_info.id for image_info in batch]
#         image_names = [image_info.name for image_info in batch]
#
#         ann_infos = api.annotation.download_batch(dataset.id, image_ids)
#         ann_jsons = [ann_info.annotation for ann_info in ann_infos]
#
#         for info, ann_json in zip(batch, ann_jsons):
#             ann = sly.Annotation.from_json(ann_json, meta)
#
#             render_img = np.zeros(ann.img_size + (3,), dtype=np.uint8)
#             render_img[:] = BG_COLOR
#             ann.draw(render_img)
#             # temp_area = sly.Annotation.stat_area(render_img, class_names, class_colors)
#
#             render_idx_rgb = np.zeros(ann.img_size+ (3,), dtype=np.uint8)
#             render_idx_rgb[:] = BG_COLOR
#             ann.draw_class_idx_rgb(render_idx_rgb, _name_to_index)
#             temp_area = sly.Annotation.stat_area(render_idx_rgb, class_names, class_indices_colors)
#
#             temp_count = ann.stat_class_count(class_names)
#             if len(tag_names) != 0:
#                 temp_img_tags = ann.stat_img_tags(tag_names)
#
#             temp_area['id'] = info.id
#             temp_area['dataset'] = dataset.name
#             temp_area['name'] = '<a href="{0}" rel="noopener noreferrer" target="_blank">{1}</a>'\
#                                 .format(api.image.url(team.id,
#                                                       workspace.id,
#                                                       project.id,
#                                                       dataset.id,
#                                                       info.id),
#                                         info.name)
#
#             stats_area.append(temp_area)
#             stats_count.append(temp_count)
#             if len(tag_names) != 0:
#                 stats_img_tags.append(temp_img_tags)
#
#         ds_progress.iters_done_report(len(batch))
#         total_images_in_project += len(batch)
#
#
# def area_name(name):
#     return "{} [area %]".format(name)
#
#
# def count_name(name):
#     return "{} [count]".format(name)
#
#
# def color_name(name, color):
#     return '<b style="display: inline-block; border-radius: 50%; background: {}; width: 8px; height: 8px"></b> {}'.format(color, name)
#
#
# #@TODO: add fieald tags count
# def create_df(stats_area, stats_count, stats_img_tags, class_names, class_colors, tag_names, tag_colors):
#     if len(stats_area) != len(stats_count):
#         raise RuntimeError("len(stats_area) != len(stats_count)")
#
#     df_area = pd.read_json(json.dumps(stats_area, cls=sly._utils.NpEncoder), orient='records')
#     df_area['unlabeled area %'] = (df_area['unlabeled area'] * 100) / df_area['total area']
#     for name in class_names:
#         df_area[name] = (df_area[name] * 100) / df_area['total area']
#     df_area = df_area.drop(['total area'], axis=1)
#     df_area = df_area.rename(columns={name: area_name(name) for name in class_names})
#
#     df_count = pd.read_json(json.dumps(stats_count, cls=sly._utils.NpEncoder), orient='records')
#     df_count = df_count.rename(columns={name: count_name(name) for name in class_names})
#
#     df = pd.concat([df_area, df_count], axis=1)
#     df = df.round(1)
#
#     cols_ordered = ['id', 'name', 'dataset', 'height', 'width', 'channels', 'unlabeled area %', 'total count']
#     classes_cols = []
#     for name in class_names:
#         classes_cols.append(area_name(name))
#         classes_cols.append(count_name(name))
#
#     df = df[[*cols_ordered, *classes_cols]]
#
#     if len(stats_img_tags) != 0:
#         df_img_tags = pd.read_json(json.dumps(stats_img_tags, cls=sly._utils.NpEncoder), orient='records')
#
#         series = None
#         for tag_name in tag_names:
#             if series is None:
#                 series = df_img_tags[tag_name].copy()
#             else:
#                 series += df_img_tags[tag_name]
#
#         df_img_tags['any tag'] = series
#
#         df = pd.concat([df, df_img_tags], axis=1)
#
#     raw_df = df.copy()
#
#     class_with_color = {}
#     for name, color in zip(class_names, class_colors):
#         class_with_color[area_name(name)] = color_name(area_name(name), sly.color.rgb2hex(color))
#         class_with_color[count_name(name)] = color_name(count_name(name), sly.color.rgb2hex(color))
#     df = df.rename(columns=class_with_color)
#
#     if len(stats_img_tags) != 0:
#         class_with_icon = {}
#         for name, color in zip(tag_names, tag_colors):
#             class_with_icon[name] = '<i class="zmdi zmdi-label" style="color:{};margin-right:3px"></i>{}'.format(sly.color.rgb2hex(color), name)
#         df = df.rename(columns=class_with_icon)
#
#     return df, raw_df
#
#
# df, raw_df = create_df(stats_area, stats_count, stats_img_tags, class_names, class_colors, tag_names, tag_colors)
#
# widgets.append(api.report.create_table(df,
#                                        "Images stats",
#                                        "Area/count distribution of objects and tags on every image",
#                                        fix_columns=2)
#                )
#
#
# # average class area per image
# class_area_nonzero = []
# class_count_nonzero = []
#
# images_with_count = []
# images_with_count_text = []
# images_without_count = []
# images_without_count_text = []
#
# unlabeled_col_name = 'unlabeled area %'
# for name in [unlabeled_col_name, *class_names]:
#     # print(name)
#     if name == unlabeled_col_name:
#         col_name = unlabeled_col_name
#     else:
#         col_name = area_name(name)
#     area_col = raw_df[col_name].copy()
#     area_col = area_col.replace(0, np.NaN)
#     area = area_col.mean(skipna=True)
#     class_area_nonzero.append(area if area is not np.NaN else 0)
#
#     count = np.NaN
#     if name == unlabeled_col_name:
#         count = np.NaN
#     else:
#         count_col = raw_df[count_name(name)].copy()
#         count_col = count_col.replace(0, np.NaN)
#         count = count_col.mean(skipna = True)
#     class_count_nonzero.append(count if count is not np.NaN else 0)
#
#     if name == unlabeled_col_name:
#         continue
#
#     without_count = count_col.isna().sum()
#     with_count = len(count_col) - without_count
#     images_with_count.append(with_count)
#     images_with_count_text.append("{} ({:.2f} %)".format(with_count, with_count * 100 / total_images_in_project))
#     images_without_count.append(without_count)
#     images_without_count_text.append("{} ({:.2f} %)".format(without_count, without_count * 100 / total_images_in_project))
#
#     if with_count + without_count != total_images_in_project:
#         raise RuntimeError("Some images are missed")
#
# fig = go.Figure(
#     data=[
#         go.Bar(name='Area %', x=[unlabeled_col_name, *class_names], y=class_area_nonzero, yaxis='y', offsetgroup=1),
#         go.Bar(name='Count', x=[unlabeled_col_name, *class_names], y=class_count_nonzero, yaxis='y2', offsetgroup=2)
#     ],
#     layout={
#         'yaxis': {'title': 'Area'},
#         'yaxis2': {'title': 'Count', 'overlaying': 'y', 'side': 'right'}
#     }
# )
# # Change the bar mode
# fig.update_layout(barmode='group')#, legend_orientation="h")
# widgets.append(api.report.create_plotly(fig.to_json(),
#                                         "Average class area/count (only non-zero values)",
#                                         "Average labels area and count for every class across images which have this class"
#                                         )
#                )
#
#
# # images count with/without classes
# fig_with_without_count = go.Figure(
#     data=[
#         go.Bar(name='# of images that have class', x=class_names, y=images_with_count, text=images_with_count_text),
#         go.Bar(name='# of images that do not have class', x=class_names, y=images_without_count, text=images_without_count_text)
#     ],
# )
# fig_with_without_count.update_layout(barmode='stack')#, legend_orientation="h")
#
# widgets.append(api.report.create_plotly(fig_with_without_count.to_json(),
#                                         "Number of images with/without specific class",
#                                         "For every class two values are calculated: how many images have / don't have a specific class"
#                                         )
#                )
#
# if len(stats_img_tags) != 0:
#
#     col_tags_count = 'any tag'
#
#     #images with without tags
#     images_with_tag_count = []
#     images_with_tag_count_text = []
#
#     images_without_tag_count = []
#     images_without_tag_count_text = []
#     for name in [col_tags_count, *tag_names]:
#         tag_col = raw_df[name].copy()
#         tag_col = tag_col[tag_col > 0]
#
#         with_tag = len(tag_col)
#         images_with_tag_count.append(with_tag)
#         images_with_tag_count_text.append("{} ({:.2f} %)".format(with_tag, with_tag * 100 / total_images_in_project))
#
#         without_tag = total_images_in_project - with_tag
#         images_without_tag_count.append(without_tag)
#         images_without_tag_count_text.append("{} ({:.2f} %)".format(without_tag, without_tag * 100 / total_images_in_project))
#
#     fig_tag_with_without_count = go.Figure(
#         data=[
#             go.Bar(name='# of images that have tag',
#                    x=[col_tags_count, *tag_names], y=images_with_tag_count,
#                    text=images_with_tag_count_text),
#             go.Bar(name='# of images that do not have tag',
#                    x=[col_tags_count, *tag_names], y=images_without_tag_count,
#                    text=images_without_tag_count_text)
#         ],
#     )
#     fig_tag_with_without_count.update_layout(barmode='stack')
#
#     widgets.append(api.report.create_plotly(fig_tag_with_without_count.to_json(),
#                                             "Number of images with/without specific tag",
#                                             "For every tag two values are calculated: how many images have / don't have a specific tag"
#                                             )
#                    )
#
#
# # barchart resolution
# df["resolution"] = df["height"].astype(str) + " x " + df["width"].astype(str) + " x " + df["channels"].astype(str)
#
# labels = df["resolution"].value_counts().index
# values = df["resolution"].value_counts().values
#
# df_resolution = pd.DataFrame({'resolution': labels, 'count': values})
# df_resolution['percent'] = df_resolution['count'] / df_resolution['count'].sum() * 100
# #df_resolution['percent'].apply("{:.2f}".format)
# #df_resolution = df_resolution.sort_values('percent', ascending=False)
# df_resolution.loc[df_resolution.index > 10, 'resolution'] = 'other'
#
# pie_resolution = px.pie(df_resolution, names='resolution', values='count')# labels='text')
# widgets.append(api.report.create_plotly(pie_resolution.to_json(),
#                                         "Images resolutions (height x width x channels)",
#                                         "How many different resolutions are in the project"
#                                         )
#                    )
#
#
# report_id = api.report.create(team.id, "Project stats: {!r}".format(project_name), widgets)
# print(api.report.url(report_id))
# sly.logger.info('Report URL', extra={'report_url': api.report.url(report_id)})
# sly.logger.info('REPORT_CREATED', extra={'event_type': sly.EventType.REPORT_CREATED, 'report_id': report_id})
#
# # from supervisely_lib.report.table import compile_report
# # html_div1 = po.plot(pie_resolution, output_type='div')
# # html = compile_report([], html_divs=[html_div1], index=False)
# # with open(os.path.join(sly.TaskPaths.TASK_DIR, 'report_xxx.html'), "w") as text_file:
# #     text_file.write(html)
#
#
#
