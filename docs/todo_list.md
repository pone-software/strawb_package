## Todo List per Submodule

### Config Parser
- Config
- [x] Test: [/test/test_config_parser.py](/test/test_config_parser.py)
    - [x] basic type test
    
- Readme
  - [x] [/docs/Config_File.md](/docs/Config_File.md)
  
### ONC Downloader
- FileHandler
  - [x] added structured download (`<strawb.Config.raw_data_dir>/<dev_code>/<YYYY>_<MM>/<file>`)
    
- [x] Test: [/test/test_onc_downloader.py](/test/test_onc_downloader.py)
    - [x] basic download test
    
- Examples
  - [x] [/examples/onc_basic_download.py](/examples/onc_basic_download.py)
    - [x] tested
  - [x] [/examples/onc_filter_download.ipynb](/examples/onc_filter_download.ipynb)
    - [x] tested
  
- Readme
  - [x] [/docs/ONC_Readme.md](/docs/ONC_Readme.md)

### Module
- FileHandler
  - [x] supports new version
  - [x] supports older version (tested March 2021 for Muontracker). Lucifer no `current_mA`, `duration_seconds`
    
- [x] Test: [/test/test_module.py](/test/test_module.py)
    - [x] basic type test
    - [ ] run test for all files - if it is compatible with all files
    
- Examples
  - [x] [/examples/module_basic_notebook.ipynb](/examples/module_basic_notebook.ipynb)
    - [x] module.FileHandler
    - [x] pandas + plotly
    - [x] matplotlib
    - [ ] virtual file support
    
### Camera
- FileHandler
  - [x] supports new SDAQ version
  - [ ] supports older SDAQ version (tested <date> for <module>)
    
- [x] Test: [/test/test_camera.py](/test/test_camera.py)
    - [x] basic test
    - [ ] run test for all files - if it is compatible with all files
    
- Examples
  - [x] [/examples/camera_lucifer_export.py](/examples/camera_lucifer_export.py)
    - [x] tested
  - [x] [/examples/camera_all_pictures_export.py](/examples/camera_all_pictures_export.py)
    - [x] tested
  - [x] [/examples/camera_bright_pictures_export.py](/examples/camera_bright_pictures_export.py)
    - [x] tested
  - [ ] [/examples/basic_camera_notebook.ipynb](/examples/dev_camera_basic_notebook.ipynb)
    - [ ] camera.FileHandler
    - [ ] pandas + plotly
    - [ ] matplotlib
    - [ ] virtual file support
  