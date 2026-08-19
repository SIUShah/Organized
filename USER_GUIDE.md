# FindCut User Guide

## Start a project

Launch FindCut, choose **File → New Project**, and select **+ Add Media**. FindCut probes each file through FFmpeg and displays its type and duration in the media bin. Double-click a media item to place it on the matching timeline track.

## Edit clips

Select a timeline item and use **Split** to split it at the midpoint. Use **Cut** to remove the selected clip from the project. These operations alter only the `.findcut` project model and never modify the original media file.

## Add text

Choose **Text**, enter the title, and save the project. Text overlays are stored as project objects with timing and style fields so the renderer can use them in a later compositing milestone.

## Save and recover

Use **File → Save Project** or **Save Project As…**. Saves are atomic. When overwriting an existing project, FindCut preserves the prior file as `<project>.findcut.bak`.

## Export

Choose **File → Export…**, select an MP4 destination, and FindCut uses the project export settings and FFmpeg backend. The current milestone exports the first imported source through the validated backend; full multi-clip compositing is the next renderer milestone.
