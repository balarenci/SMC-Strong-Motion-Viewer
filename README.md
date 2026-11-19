# SMC 强震动波形查看器 / SMC Strong-Motion Waveform Viewer

**中文** | [English](#english)

基于 Python、Tkinter 和 Matplotlib 的桌面工具，用于读取美国地质调查局（USGS）NSMP 的 SMC ASCII 强震动时程数据，并显示地震波形。

A Python/Tkinter desktop application for reading USGS NSMP SMC ASCII strong-motion time histories and plotting earthquake waveforms.

## 中文

### 1. 项目简介

本项目适用于地震加速度、速度和位移时程的初步查看与数据导出。可同时打开多个 SMC 文件，例如 HNE（东西向）、HNN（南北向）和 HNZ（垂直向），分别绘图或叠加显示。

> 当前为 **V1.0**，重点是 SMC 文件解析与波形查看；不是完整的强震动信号处理软件。

### 2. 主要功能

- **SMC 读取**：解析文本头、整数头、浮点头、注释与时程序列；支持标准固定宽度数值及部分空格分隔变体。
- **时程类型**：读取未校正/校正加速度、速度及位移时程；对不支持的类型给出提示。
- **多文件绘图**：一次导入多个文件，按分量分别显示，或勾选“叠加显示”。
- **记录信息**：显示台站、分量、记录类型、采样率、采样点数、时长、UTC 起始时间、方向角及峰值绝对幅值。
- **单位选择**：原始单位、SI 单位；加速度可选择 g。
- **图形操作**：通过 Matplotlib 工具栏缩放、平移和还原视图。
- **导出功能**：选中记录导出 CSV，当前绘图保存为 PNG。
- **采样方式**：支持等间隔采样；也可读取以时间—幅值成对存储的非均匀采样时程。

**当前不支持**：SMC Type 5/6 的反应谱或傅里叶幅值谱绘制；不提供基线校正、滤波、积分或 PGV/PGD 自动计算。

### 3. 运行环境

- Python 3.10 或更新版本
- NumPy、Matplotlib
- Tkinter（Windows 官方 Python 安装通常包含）

### 4. 安装与运行

在 PowerShell、终端或命令提示符中：

```bash
git clone https://github.com/balarenci/SMC-Strong-Motion-Viewer.git
cd SMC-Strong-Motion-Viewer
python -m pip install -r requirements.txt
python smc_waveform_viewer.py
```

如果仓库已设为 **Private**，需要有权限的 GitHub 账户才能克隆。

### 5. 操作说明

1. 启动程序，点击 **“打开 SMC 文件（可多选）”**。
2. 选择一个或多个 `.smc` 文件；左侧列表将显示已载入的记录。
3. 在列表中选择目标分量；默认分别绘图，可勾选 **“叠加显示”**。
4. 在 **“显示单位”** 中选择 `Original`、`SI` 或 `g`。
5. 点击 **“导出选中 CSV”** 保存时程数据，或点击 **“保存 PNG”** 保存图像。

> 叠加不同物理量时请注意单位不同；图中时轴为各记录相对于自身起始位置的秒数，并非自动按绝对 UTC 时间对齐。

### 6. 数据类型和单位

| SMC 类型 | 含义 | 原始单位 |
| --- | --- | --- |
| Type 1 | 未校正加速度 / Uncorrected acceleration | cm/s² |
| Type 2 | 校正加速度 / Corrected acceleration | cm/s² |
| Type 3 | 速度 / Velocity | cm/s |
| Type 4 | 位移 / Displacement | cm |
| Type 5 / 6 | 反应谱 / 傅里叶幅值谱 | 当前不支持 |

加速度单位转换：**1 g = 980.665 cm/s²**。SI 模式将 cm/s²、cm/s 和 cm 分别转换为 m/s²、m/s 和 m。

程序显示的峰值为时程的 **最大绝对幅值**。仅当记录是加速度时，该值才可按相应处理级别理解为 PGA；未校正记录的峰值不等于经完整校正的工程分析结果。

### 7. 实际数据验证

已用 2014 年 3 月 17 日的一组三分量 USGS SMC 未校正加速度记录检查读取与绘图：

| 文件分量 | 采样率 | 样本数 | 记录类型 |
| --- | ---: | ---: | --- |
| HNE | 200 Hz | 20,800 | 未校正加速度 |
| HNN | 200 Hz | 20,800 | 未校正加速度 |
| HNZ | 200 Hz | 20,800 | 未校正加速度 |

原始 SMC 数据文件**未随仓库发布**。可以运行基础单元测试：

```bash
python -m unittest discover -s tests
```

### 8. 使用限制与注意事项

- 未校正加速度可能包含零点偏置、基线漂移或其他仪器影响；不能未经处理直接积分并将结果视为可靠 PGV/PGD。
- 本程序不会进行滤波、重采样或基线校正；原始采样数据按文件内容绘制。
- SMC 时程格式与 COSMOS Strong-Motion 格式并不相同，请使用对应格式的解析工具。
- CSV 导出采用选中显示单位，时间列为相对时间（秒）。
- 不支持的 SMC 谱文件会显示错误提示，不会作为普通时程绘制。

### 9. 项目文件

```text
SMC-Strong-Motion-Viewer/
├── smc_waveform_viewer.py   # GUI 主程序
├── requirements.txt         # 依赖
├── tests/
│   └── test_parser.py       # 基础测试
├── .gitignore
└── README.md
```

### 10. 官方参考与许可

- [USGS NSMP — SMC 数据格式说明](https://escweb.wr.usgs.gov/nsmp-data/smcfmt.html)
- 本仓库目前**未添加开源 LICENSE 文件**。公开可见不等于已获得再分发或修改许可；如计划开源，请由仓库所有者另行选择许可证。

---

## English

### 1. Overview

SMC Strong-Motion Waveform Viewer is a Python desktop GUI for inspecting USGS NSMP SMC ASCII strong-motion time histories, including acceleration, velocity, and displacement. Multiple components (such as HNE, HNN, and HNZ) can be loaded together and plotted separately or overlaid.

**Version 1.0** focuses on parsing, visualization, and export. It is not a complete strong-motion processing or correction suite.

### 2. Features

- Parses SMC text, integer, and real-number headers, comments, and time-history samples.
- Reads supported uncorrected/corrected acceleration, velocity, and displacement records.
- Loads multiple files and plots them individually or as an overlay.
- Displays station, component, sample rate, sample count, duration, UTC start time, orientation, and peak absolute amplitude.
- Supports original units, SI units, and acceleration in g.
- Includes Matplotlib zoom and pan controls.
- Exports selected records to CSV and the current figure to PNG.
- Handles uniformly sampled and supported unevenly sampled time series.

**Not supported:** Type 5/6 response or Fourier spectra, baseline correction, filtering, integration, and automatic PGV/PGD computation.

### 3. Requirements and installation

- Python 3.10+
- NumPy and Matplotlib
- Tkinter (normally included with standard Windows Python installations)

```bash
git clone https://github.com/balarenci/SMC-Strong-Motion-Viewer.git
cd SMC-Strong-Motion-Viewer
python -m pip install -r requirements.txt
python smc_waveform_viewer.py
```

A GitHub account with access is required if this repository is private.

### 4. How to use

1. Launch the application and click **打开 SMC 文件（可多选）** (“Open SMC files”).
2. Select one or more `.smc` files.
3. Select components in the list; enable **叠加显示** (“Overlay”) if desired.
4. Choose `Original`, `SI`, or `g` from **显示单位** (“Display units”).
5. Use **导出选中 CSV** (“Export selected CSV”) or **保存 PNG** (“Save PNG”).

Overlaid traces share a relative-time axis; they are **not automatically aligned by absolute UTC start time**. Avoid comparing mixed physical units on a shared scale.

### 5. Data types and units

| SMC type | Description | Native unit |
| --- | --- | --- |
| 1 | Uncorrected acceleration | cm/s² |
| 2 | Corrected acceleration | cm/s² |
| 3 | Velocity | cm/s |
| 4 | Displacement | cm |
| 5 / 6 | Response/Fourier spectrum | Not supported |

Acceleration conversion: **1 g = 980.665 cm/s²**. SI conversions use meters instead of centimeters.

The displayed peak is the **maximum absolute sample amplitude**. It represents a PGA-like peak only for acceleration records and must be interpreted in light of the record's correction level.

### 6. Validation

Parsing and plotting were checked with three USGS uncorrected-acceleration SMC records (HNE, HNN, HNZ) from March 17, 2014. Each file has **20,800 samples at 200 Hz**. Source seismic records are **not redistributed** here.

Run the included basic tests with:

```bash
python -m unittest discover -s tests
```

### 7. Limitations

- Uncorrected acceleration may contain offset and drift. Appropriate correction is needed before deriving reliable velocity or displacement by integration.
- The viewer does not modify the input time series with filters, resampling, or baseline correction.
- SMC and COSMOS strong-motion file formats are distinct.
- Exported CSV time values are relative seconds.
- Spectrum-only SMC records are rejected rather than interpreted as waveforms.

### 8. Repository layout

```text
SMC-Strong-Motion-Viewer/
├── smc_waveform_viewer.py
├── requirements.txt
├── tests/test_parser.py
├── .gitignore
└── README.md
```

### 9. Reference and license

- [USGS NSMP SMC format description](https://escweb.wr.usgs.gov/nsmp-data/smcfmt.html)
- **No open-source license has been added** at this stage. Please choose and add an explicit LICENSE before distributing this project under open-source terms.
