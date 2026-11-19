# SMC Strong-Motion Waveform Viewer / SMC 强震动波形查看器

A Python desktop GUI for inspecting USGS NSMP SMC ASCII strong-motion time series.

基于 Python/Tkinter 的 SMC 强震动记录读取与波形查看工具，支持多文件载入、绘图、峰值查看和导出。

## Features / 功能

- Read supported SMC time-history records (uncorrected/corrected acceleration, velocity and displacement).
- Parse text, integer and floating-point headers, comments, and time series.
- Load multiple components and plot separately or overlay.
- Display sampling rate, component, station, start time, sample count and peak amplitude.
- Convert units to SI, or g for acceleration.
- Export a selected record to CSV and save waveform plots as PNG.
- Explicitly rejects spectrum-only SMC records (types 5 and 6).

## Requirements / 环境

- Python 3.10+
- `numpy`, `matplotlib`
- `tkinter` (typically bundled with desktop Python on Windows)

```bash
pip install -r requirements.txt
python smc_waveform_viewer.py
```

In the GUI, choose **打开 SMC 文件（可多选）** and select one or more `.smc` files.

## Tested data / 验证数据

Tested on three USGS SMC uncorrected acceleration files with HNE/HNN/HNZ components from a March 17, 2014 record. Each file contains 20,800 samples at 200 Hz. The records themselves are **not redistributed** in this repository.

## Units / 单位

SMC acceleration: cm/s²; velocity: cm/s; displacement: cm. Acceleration in g uses `1 g = 980.665 cm/s²`.

## Caution / 注意

Uncorrected acceleration records may contain offsets or long-period drift. Do not use them directly for reliable PGV/PGD integration without appropriate correction. Spectral SMC files are not time series and are not supported.

## Reference / 官方说明

USGS SMC format: https://escweb.wr.usgs.gov/nsmp-data/smcfmt.html

## License / 许可

No open-source license is granted in this initial package. Add a LICENSE file after choosing the intended terms before publishing as an open-source project.