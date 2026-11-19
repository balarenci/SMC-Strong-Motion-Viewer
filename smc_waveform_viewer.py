#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""USGS SMC ASCII strong-motion time-series viewer (SMC v1/v2).
Dependencies: numpy, matplotlib; tkinter is part of most Python installations.
"""
from __future__ import annotations
import csv
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

KINDS = {0: ('Unknown / uncorrected acceleration', 'cm/s²'),
         1: ('Uncorrected acceleration', 'cm/s²'),
         2: ('Corrected acceleration', 'cm/s²'),
         3: ('Velocity', 'cm/s'), 4: ('Displacement', 'cm')}
FLOAT_RE = re.compile(r'[+-]?(?:\d+\.?\d*|\.\d+)(?:[EeDd][+-]?\d+)?')


def number(x: str) -> float:
    return float(x.strip().replace('D', 'E').replace('d', 'e'))


def parse_header_rows(lines: list[str], width: int, count_per_line: int, integer=False) -> list[float]:
    out = []
    for line in lines:
        # Official fixed-width fields; whitespace fallback for non-canonical exports.
        pieces = [line[i:i + width] for i in range(0, width * count_per_line, width)]
        try:
            values = [number(v) for v in pieces if v.strip()]
            if len(values) != count_per_line:
                raise ValueError('incomplete fixed width line')
        except ValueError:
            tokens = line.split()
            if len(tokens) != count_per_line:
                raise ValueError(f'Invalid header line: {line[:100]!r}')
            values = [number(v) for v in tokens]
        if integer and any(v != int(v) for v in values):
            raise ValueError('Integer header contains non-integers')
        out.extend(values)
    return [int(v) for v in out] if integer else out


def missing(x, sentinel=None) -> bool:
    if x is None or not np.isfinite(x):
        return True
    if sentinel is not None and np.isfinite(sentinel) and x == sentinel:
        return True
    return abs(x) > 1e35 or x == -32768


def read_numeric_data(lines: list[str], expected: int) -> np.ndarray:
    result = []
    for line in lines:
        if len(result) >= expected:
            break
        if not line.strip():
            continue
        # A regex also handles adjacent signed scientific values without spaces.
        # Fortran 1P E notation always includes an explicit exponent letter.
        # First honor the official ten-character fields if complete.
        # This matters for adjacent positive numbers, e.g. 1.0000E+02.0000E+0.
        fields = [line[i:i + 10] for i in range(0, len(line), 10)]
        if len(line) % 10 == 0 and all(
            not f.strip() or FLOAT_RE.fullmatch(f.strip()) for f in fields
        ):
            tokens = [f.strip() for f in fields if f.strip()]
        else:
            tokens = FLOAT_RE.findall(line)
            if not tokens or re.sub(FLOAT_RE, '', line).strip():
                raise ValueError(f'Invalid data line: {line[:80]!r}')
        result.extend(number(v) for v in tokens)
    if len(result) < expected:
        raise ValueError(f'Incomplete time series: expected {expected} numbers, found {len(result)}')
    return np.asarray(result[:expected], dtype=np.float64)


@dataclass
class SMCRecord:
    path: Path
    kind: int
    text: list[str]
    ints: list[int]
    reals: list[float]
    comments: list[str]
    t: np.ndarray
    y: np.ndarray
    rate: float | None
    start: datetime | None
    station: str
    component: str
    uneven: bool

    @property
    def unit(self):
        return KINDS[self.kind][1]

    @property
    def peak(self):
        return float(np.max(np.abs(self.y)))


def read_smc(path: str | Path) -> SMCRecord:
    path = Path(path)
    # SMC is ASCII; latin-1 preserves old legacy byte values without decode errors.
    lines = path.read_bytes().decode('latin-1').splitlines()
    if len(lines) < 27:
        raise ValueError('File too short for SMC header')
    first = lines[0].strip()
    if first.startswith('*'):
        kind = 1  # v1: conventionally uncorrected acceleration
    else:
        m = re.match(r'^\s*(\d+)\s+', first)
        if not m:
            raise ValueError(f'Not an SMC time-series file: {first!r}')
        kind = int(m.group(1))
    if kind not in KINDS:
        if kind in (5, 6):
            raise ValueError('This is an SMC spectrum file (type 5/6), not a time series; waveform plotting is not applicable.')
        raise ValueError(f'Unsupported SMC data kind: {kind}')
    text_lines = lines[:11]
    ih = parse_header_rows(lines[11:17], 10, 8, integer=True)
    rh = parse_header_rows(lines[17:27], 15, 5)
    if len(ih) != 48 or len(rh) != 50:
        raise ValueError('Incorrect SMC header size')
    ncomment = ih[15]
    expected = ih[16]
    if ncomment < 0 or expected <= 0:
        raise ValueError(f'Invalid SMC comment or sample counts: {ncomment}, {expected}')
    data_start = 27 + ncomment
    if data_start >= len(lines):
        raise ValueError('Data segment missing')
    comments = lines[27:data_start]
    values = read_numeric_data(lines[data_start:], expected)
    rate = rh[1]
    uneven = missing(rate, rh[0]) or rate <= 0
    if uneven:
        if len(values) % 2:
            raise ValueError('Uneven sampling requires an even number of time-amplitude values')
        t, y = values[::2], values[1::2]
        if np.any(np.diff(t) <= 0):
            raise ValueError('Uneven sample timestamps must strictly increase')
        rate = None
    else:
        y = values
        t = np.arange(len(y), dtype=float) / rate
    start = None
    try:
        yy, day, hh, mm, ss, ms = ih[1:7]
        if all(not missing(k, ih[0]) for k in (yy, day, hh, mm, ss)):
            start = datetime(yy, 1, 1, tzinfo=timezone.utc) + timedelta(
                days=day - 1, hours=hh, minutes=mm, seconds=ss,
                milliseconds=0 if missing(ms, ih[0]) else ms)
    except (OverflowError, ValueError):
        pass
    station_match = re.search(r'station\s*=\s*(.*?)(?:component\s*=|$)', text_lines[5], re.I)
    station = station_match.group(1).strip() if station_match else text_lines[2].strip()
    component_match = re.search(r'component\s*=\s*(.*)', text_lines[5], re.I)
    component = component_match.group(1).strip() if component_match else text_lines[2].strip()
    return SMCRecord(path, kind, text_lines, ih, rh, comments, t, y, rate, start,
                     station, component, uneven)


def scaled_values(rec: SMCRecord, mode: str):
    if mode == 'g' and rec.kind in (0, 1, 2):
        return rec.y / 980.665, 'g'
    if mode == 'SI':
        return rec.y / 100, {'cm/s²': 'm/s²', 'cm/s': 'm/s', 'cm': 'm'}[rec.unit]
    return rec.y, rec.unit


def save_csv(rec: SMCRecord, path: str, mode: str):
    y, unit = scaled_values(rec, mode)
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(['Time (s)', f'{KINDS[rec.kind][0]} ({unit})'])
        w.writerows(zip(rec.t, y))


class Viewer:
    def __init__(self, root):
        self.root = root
        root.title('USGS SMC 地震波形查看器 V1.0')
        root.geometry('1200x780')
        self.records: list[SMCRecord] = []
        self.mode = tk.StringVar(value='Original')
        self.overlap = tk.BooleanVar(value=False)
        top = ttk.Frame(root, padding=8)
        top.pack(fill='x')
        ttk.Button(top, text='打开 SMC 文件（可多选）', command=self.open_files).pack(side='left', padx=3)
        ttk.Button(top, text='移除选中', command=self.remove).pack(side='left', padx=3)
        ttk.Button(top, text='清空', command=self.clear).pack(side='left', padx=3)
        ttk.Label(top, text='显示单位:').pack(side='left', padx=(22, 4))
        ttk.Combobox(top, textvariable=self.mode, state='readonly', width=12,
                     values=['Original', 'SI', 'g']).pack(side='left')
        self.mode.trace_add('write', lambda *_: self.plot())
        ttk.Checkbutton(top, text='叠加显示', variable=self.overlap,
                        command=self.plot).pack(side='left', padx=12)
        ttk.Button(top, text='导出选中 CSV', command=self.export_csv).pack(side='right', padx=3)
        ttk.Button(top, text='保存 PNG', command=self.save_png).pack(side='right', padx=3)
        layout = ttk.Panedwindow(root, orient=tk.HORIZONTAL)
        layout.pack(fill='both', expand=True, padx=8, pady=5)
        left = ttk.Frame(layout, width=320)
        right = ttk.Frame(layout)
        layout.add(left, weight=1)
        layout.add(right, weight=4)
        ttk.Label(left, text='文件列表（可选多条）').pack(anchor='w')
        self.listbox = tk.Listbox(left, selectmode=tk.EXTENDED, exportselection=False, height=12)
        self.listbox.pack(fill='x', pady=4)
        self.listbox.bind('<<ListboxSelect>>', self.selection_changed)
        ttk.Label(left, text='记录信息').pack(anchor='w', pady=(12, 0))
        self.info = tk.Text(left, height=25, width=36, wrap='word', state='disabled')
        self.info.pack(fill='both', expand=True, pady=3)
        fig = Figure(figsize=(9, 6), dpi=100)
        self.figure = fig
        self.canvas = FigureCanvasTkAgg(fig, master=right)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        toolbar = NavigationToolbar2Tk(self.canvas, right)
        toolbar.update()
        self.status = tk.StringVar(value='请打开一个或多个 SMC 文件。')
        ttk.Label(root, textvariable=self.status, padding=6).pack(fill='x')
        self.plot()

    def open_files(self):
        paths = filedialog.askopenfilenames(title='选择 SMC ASCII 文件',
            filetypes=[('SMC / text files', '*.smc *.SMC *.v1 *.V1 *.v2 *.V2 *.txt *.TXT *.dat *.DAT'), ('All files', '*.*')])
        failures = []
        added = 0
        old = {str(r.path.resolve()) for r in self.records}
        for p in paths:
            if str(Path(p).resolve()) in old:
                continue
            try:
                rec = read_smc(p)
                self.records.append(rec)
                self.listbox.insert('end', f'{Path(p).name} [{rec.component}]')
                old.add(str(Path(p).resolve()))
                added += 1
            except Exception as e:
                failures.append(f'{Path(p).name}: {e}')
        if added:
            self.listbox.selection_clear(0, 'end')
            self.listbox.selection_set(max(0, len(self.records) - added), 'end')
            self.selection_changed()
        if failures:
            messagebox.showwarning('部分文件无法读取', '\n'.join(failures[:12]))
        self.status.set(f'已载入 {len(self.records)} 条记录；本次新增 {added} 条。')

    def selected(self):
        indices = self.listbox.curselection()
        return [self.records[i] for i in indices] if indices else self.records

    def selection_changed(self, *_):
        sel = self.selected()
        info = []
        for r in sel[:5]:
            info.extend([f'文件: {r.path.name}', f'台站: {r.station}',
                         f'分量: {r.component}', f'类型: {KINDS[r.kind][0]}',
                         f'样本数: {len(r.y)}',
                         f'采样率: {r.rate:g} Hz' if r.rate else '采样率: 非均匀采样',
                         f'时长: {r.t[-1] - r.t[0]:.3f} s',
                         f'峰值 |Peak|: {r.peak:.7g} {r.unit}',
                         f'起始 UTC: {r.start.isoformat() if r.start else "未知"}',
                         f'水平角: {r.ints[13] if not missing(r.ints[13], r.ints[0]) else "未知"}',
                         f'垂直角: {r.ints[12] if not missing(r.ints[12], r.ints[0]) else "未知"}',
                         '------------------------------'])
        self.info.config(state='normal')
        self.info.delete('1.0', 'end')
        self.info.insert('1.0', '\n'.join(info) if info else '尚未选择文件')
        self.info.config(state='disabled')
        self.plot()

    def plot(self):
        fig = self.figure
        fig.clear()
        selected = self.selected()
        if not selected:
            ax = fig.add_subplot(111)
            ax.text(.5, .5, 'Open SMC waveform files', ha='center', va='center', transform=ax.transAxes)
            ax.set_axis_off()
        elif self.overlap.get():
            ax = fig.add_subplot(111)
            units = set()
            for r in selected:
                y, unit = scaled_values(r, self.mode.get())
                units.add(unit)
                ax.plot(r.t, y, linewidth=.85, label=f'{r.path.name} ({unit})')
            ax.set_xlabel('Time (s)')
            ax.set_ylabel(next(iter(units)) if len(units) == 1 else 'Mixed units - see legend')
            ax.grid(alpha=.3)
            ax.legend(loc='upper right', fontsize=8)
        else:
            axes = fig.subplots(len(selected), 1, sharex=False, squeeze=False)
            for ax, r in zip(axes[:, 0], selected):
                y, unit = scaled_values(r, self.mode.get())
                ax.plot(r.t, y, linewidth=.75)
                ax.set_title(f'{r.path.name} | {r.station} | {r.component} | peak={np.max(np.abs(y)):.6g} {unit}', fontsize=10)
                ax.set_ylabel(unit)
                ax.set_xlabel('Time (s)')
                ax.grid(alpha=.3)
        fig.tight_layout()
        self.canvas.draw_idle()

    def remove(self):
        for i in sorted(self.listbox.curselection(), reverse=True):
            del self.records[i]
            self.listbox.delete(i)
        self.selection_changed()

    def clear(self):
        self.records.clear()
        self.listbox.delete(0, 'end')
        self.selection_changed()

    def export_csv(self):
        sel = self.selected()
        if not sel:
            messagebox.showinfo('提示', '请先打开文件。')
            return
        if len(sel) == 1:
            dst = filedialog.asksaveasfilename(defaultextension='.csv', initialfile=sel[0].path.stem + '.csv',
                                                 filetypes=[('CSV', '*.csv')])
            if dst:
                save_csv(sel[0], dst, self.mode.get())
                self.status.set(f'已导出: {dst}')
        else:
            directory = filedialog.askdirectory(title='选择 CSV 导出目录')
            if directory:
                for n, r in enumerate(sel, 1):
                    save_csv(r, str(Path(directory) / f'{r.path.stem}_{n}.csv'), self.mode.get())
                self.status.set(f'已导出 {len(sel)} 条 CSV 到 {directory}')

    def save_png(self):
        dst = filedialog.asksaveasfilename(defaultextension='.png', filetypes=[('PNG image', '*.png')])
        if dst:
            self.figure.savefig(dst, dpi=180, bbox_inches='tight')
            self.status.set(f'已保存: {dst}')


def main():
    root = tk.Tk()
    Viewer(root)
    root.mainloop()


if __name__ == '__main__':
    main()