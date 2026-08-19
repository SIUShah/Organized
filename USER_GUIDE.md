# FindCut User Guide

## Start a project

Launch FindCut, choose **File → New Project**, and select **+ Add Media** or **Add Folder**. FindCut probes each video, audio, and image through FFmpeg and displays its type and duration in the media bin. Double-click a media item to place it on the matching timeline track. The original files remain untouched.

The media panel also includes **Remove**, which removes an asset from the project without deleting the source file, and **Open Location**, which opens the source folder in Windows Explorer.

## Edit clips

Select a timeline item and use **Split** to split it at the midpoint. Use **Cut** to remove the selected clip from the project. These operations alter only the `.findcut` project model and never modify the original media file.

## Add text

Choose **Text**, enter the title, and save the project. Text overlays are stored as project objects with timing and style fields so the renderer can use them in a later compositing milestone.

## Save and recover

Use **File → Save Project** or **Save Project As…**. Saves are atomic. When overwriting an existing project, FindCut preserves the prior file as `<project>.findcut.bak`.

## Export edited media

Choose **File → Export Edited Video…** to render the clips currently placed on the timeline into one MP4. FindCut uses FFmpeg filters to trim each clip, normalize the canvas, concatenate video clips in timeline order, and combine audio clips on the audio track.

Choose **File → Export Selected Clip…** to create an MP4 from the selected timeline clip. Choose **File → Extract Audio…** to save the selected clip’s audio, or the first project asset’s audio when no timeline clip is selected. **Open Output Folder** opens the project folder so you can retrieve exported files.
