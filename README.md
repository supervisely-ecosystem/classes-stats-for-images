<div align="center" markdown> 

<img src="https://github-production-user-asset-6210df.s3.amazonaws.com/48245050/264698175-9d0e0f0d-a8ed-4ae2-9a5c-1327df3bd30e.png"/>

# Classes Stats for Images 
  
<p align="center">

  <a href="#overview">Overview</a> •
  <a href="#How-To-Run">How To Run</a> •
  <a href="#Explanation">Explanation</a>
</p>

[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervisely.com/slack) 
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/classes-stats-for-images)
[![views](https://app.supervisely.com/img/badges/views/supervisely-ecosystem/classes-stats-for-images.png)](https://supervisely.com)
[![runs](https://app.supervisely.com/img/badges/runs/supervisely-ecosystem/classes-stats-for-images.png)](https://supervisely.com)

</div>

## Overview 

Data Exploration for Segmentation and Detection tasks is underestimated by many researchers. The accuracy of your models highly depends on how good you understand data. 

This app **"Classes Stats for Images"** generates report with detailed general and per image statistics for all classes in images project. It allows to see big picture as well as shed light on hidden patterns and edge cases (see <a href="#how-to-use">How to use</a> section).


## How To Run

### Step 1: Run from context menu of project / dataset

Go to "Context Menu" (images project or dataset) -> "Report" -> "Classes stats for images"

<img src="https://github-production-user-asset-6210df.s3.amazonaws.com/48245050/264698171-a5503512-37c7-4cfb-b96f-f9a3cb83541c.png" width="600"/>

### Step 2: Configure running settings

Choose the percentage of images that should be randomly sampled. By default all images will be used. And then press "Run" button. In advanced settings you can change agent that will host the app and change version (latest available version is used by default).

<img src="https://github-production-user-asset-6210df.s3.amazonaws.com/48245050/264698166-36c2fa3d-17bd-4c18-8eb1-c768ed5a094d.png" width="400"/>


### Step 3:  Open app

Once app is started, new task appear in workspace tasks. Monitor progress from both "Tasks" list and from application page. To open report in a new tab click "Open" button. 

<img src="https://github-production-user-asset-6210df.s3.amazonaws.com/48245050/264698164-98146f16-4e6c-4233-bb42-1442c70f1b94.png"/>

App saves resulting report to "Files": `/reports/classes_stats/{USER_LOGIN}/{WORKSPACE_NAME}/{PROJECT_NAME}.lnk`. To open report file in future use "Right mouse click" -> "Open".

## Explanation

### Per Image Stats
<img src="https://github-production-user-asset-6210df.s3.amazonaws.com/48245050/264698185-6938c2ba-be79-4fb2-8ca4-3f44b1530841.png"/>

Columns:
* `IMAGE ID` - image id in Supervisely Instance
* `IMAGE` - image name with direct link to annotation tool. You can use table to find some anomalies or edge cases in your data by sorting different columns and then quickly open images with annotations to investigate deeper. 
* `HEIGHT`, `WIDTH` - image resolution in pixels
* `CHANNELS` - number of image channels
* `UNLABELED` - percentage of pixels (image area)

Columns for every class:
* <img src="https://github-production-user-asset-6210df.s3.amazonaws.com/48245050/264698244-1506018e-a5b6-429e-821d-3b3ca534fa56.png" width="100"/> - class area (%)
* <img src="https://github-production-user-asset-6210df.s3.amazonaws.com/48245050/264698242-1da532f9-6bc5-4d1e-9aa4-a1f5de5e240e.png" width="100"/> - number of objects of a given class (%)

### Per Class Stats

<img src="https://github-production-user-asset-6210df.s3.amazonaws.com/48245050/264698193-af7ea3cb-95f8-43e1-9b19-00cee37a144a.png"/>

* `CLASS NAME`
* `IMAGES COUNT` - total number of images that have at least one object of a given class
* `OBJECTS COUNT` - total number of objects of a given class
* `AVG CLASS AREA PER IMAGE (%)` -

```
              the sum of a class area on all images               
 -------------------------------------------------------------- 
 the number of images with at least one object of a given class 
```
 
* `AVG OBJECTS COUNT PER IMAGE (%)` - 
```
              total number of class objects               
 -------------------------------------------------------------- 
 the number of images with at least one object of a given class 
```

### Histogram: AVG AREA / AVG OBJECTS COUNT

<img src="https://github-production-user-asset-6210df.s3.amazonaws.com/48245050/264698225-ae351c6c-8338-4dab-8036-54db6edcb7e4.png"/>

Histogram view for two metrics from previous chapter: `AVG CLASS AREA PER IMAGE (%)` and `AVG OBJECTS COUNT PER IMAGE (%)`

### Images Count With / Without Class

<img src="https://github-production-user-asset-6210df.s3.amazonaws.com/48245050/264698204-abd4b045-b149-41cf-af89-af7108f2d6ce.png"/>

### TOP-10 Image Resolutions

<img src="https://github-production-user-asset-6210df.s3.amazonaws.com/48245050/264698156-bb9c564a-22ca-4757-8aa4-753059850af9.png"/>
