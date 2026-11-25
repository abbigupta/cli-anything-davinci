# Resolve API compatibility

The implementation targets the documented Resolve 21.1+ call forms. The local reference was Blackmagic Design's Resolve 21.2.0 distribution, including `Developer/Scripting/README.md` (31 Aug 2026), `CHANGELOG.md` (4 Nov 2026), and Python examples 1, 2, 3, 5, 7, 8 and 9. Its README points to a .pyi definition that was absent from the installed bundle. We checked the methods against a preserved copy of the vendor’s 21.2.0 type definitions and its July 2026 scripting reference. The older deric reference uses obsolete render queue indexes. This CLI uses string job IDs.

[Vendor website](https://www.blackmagicdesign.com/products/davinciresolve) · [21.2 SDK type definitions](https://github.com/WheheoHu/bmd_doc/blob/e5b403901366caf9319d3943ac8ebcd34d5445f7/_README_API/21_2_0/DaVinciResolveScript.pyi) · [July 2026 SDK reference copy](https://gist.github.com/X-Raym/2f2bf453fc481b9cca624d7ca0e19de8) · [Older API reference](https://deric.github.io/DaVinciResolve-API-Docs/)

| CLI operation | Documented SDK calls or constants |
| --- | --- |
| status, doctor | `DaVinciResolveScript.scriptapp("Resolve")`, `GetProductName`, `GetVersionString`, `GetProjectManager` |
| project list/current/create/open | ProjectManager `GetProjectListInCurrentFolder`, `GetCurrentProject`, `CreateProject`, `LoadProject`; object `GetName` |
| project save/close/export/import | ProjectManager `SaveProject`, `CloseProject(project)`, `ExportProject(name,path)`, `ImportProject(path[,name])` |
| media list/search/info | Project `GetMediaPool`; MediaPool `GetRootFolder`; Folder `GetName`, `GetClipList`, `GetSubFolderList`; MediaPoolItem `GetMediaId`, `GetName`, `GetClipProperty()` |
| media import/folder | MediaPool `ImportMedia([{"FilePath": path}])`, `GetCurrentFolder`, `AddSubFolder(parent,name)` |
| timeline list/current/select/create | Project `GetTimelineCount`, `GetTimelineByIndex`, `GetCurrentTimeline`, `SetCurrentTimeline`; MediaPool `CreateEmptyTimeline` |
| timeline append | MediaPool `AppendToTimeline([{"mediaPoolItem": clip}])`, result items' `GetUniqueId` |
| timeline info/tracks/clips | Timeline `GetName`, `GetStartFrame`, `GetEndFrame`, `GetStartTimecode`, `GetTrackCount`, `GetTrackName`, `GetIsTrackEnabled`, `GetItemListInTrack`; TimelineItem `GetName`, `GetUniqueId`, `GetStart`, `GetEnd` |
| timeline marker | Timeline `AddMarker(offset,color,name,note,duration,customData)`, `GetMarkers` |
| timeline export | Timeline `Export(path,type,subtype)`; Resolve constants `EXPORT_DRT`, `EXPORT_OTIO`, `EXPORT_TEXT_CSV`, `EXPORT_EDL` with `EXPORT_NONE` as the subtype (ignored for non-EDL formats) |
| render formats/codecs/presets/configure | Project `GetRenderFormats`, `GetRenderCodecs`, `GetRenderPresetList`, `LoadRenderPreset`, `SetCurrentRenderMode`, `SetCurrentRenderFormatAndCodec`, `SetRenderSettings` |
| render queue/start/status/cancel | Project `AddRenderJob`, `StartRendering([ids],False)`, `GetRenderJobList`, `GetRenderJobStatus(id)`, `IsRenderingInProgress`, `StopRendering()` |
| timeline track add/enable | Timeline `AddTrack(type[,subTrackType])`, `SetTrackEnable(type,index,bool)`; audio creation specifies stereo |
| clip properties/set | TimelineItem `GetProperties()`, `SetProperties({key:value})`. Reads back the value Resolve actually accepted |
| clip fusion | TimelineItem `GetFusionCompNameList`, optional `AddFusionComp` |
| color lut/grade | TimelineItem `GetNodeGraph()`; Graph `SetLUT(node,path)`, `GetLUT(node)`, `ApplyGradeFromDRX(path,mode)` |
| batch editing | Ordered CLI imports and appends, shell or REPL sequencing over the same SDK operations |

## Capability boundaries

- A reachable external session is required for editing. The tested Free build supplied the SDK and declined the connection. The API can also reject Studio-only features from Free. See [test evidence](../TEST.md).
- Resolve owns codec support, marker colors, property ranges, current selections and any prompts. A missing method returns `unsupported`. A rejected SDK call often gives insufficient detail to distinguish edition, selection and invalid arguments.
- Grade import replaces the current graph. LUTs must be known to Resolve. This release operates on the first graph layer and existing nodes.
- Audio controls include track enable/mute and the writable timeline item properties reported by the installation. Fusion support covers attached compositions. Mixer plug-in automation, arbitrary node editing and GUI-only controls have no command in this release.
- Append operates on entire imported clips. The CLI exposes no frame-accurate trim, ripple/undo transaction or project-level locking. Coordinate concurrent GUI edits when automating the active selection.
- Render start is asynchronous. StopRendering has a void return. The CLI queries the actual rendering state after requesting a stop.
