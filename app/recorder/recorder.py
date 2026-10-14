"""录屏核心 — mss 截图 + FFmpeg 子进程管道编码（硬件加速）"""
import subprocess
import threading
import time
import numpy as np
import mss
import mss.tools
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from app.config import config, DEFAULT_OUTPUT_DIR
from app.history import history
import imageio_ffmpeg


class ScreenRecorder(QObject):
    """屏幕录制器：双线程架构（采集线程 + FFmpeg 编码进程）"""

    tick = pyqtSignal(int)       # 每秒触发一次，参数是已录制秒数
    finished = pyqtSignal(str)   # 录制结束，传出文件路径
    failed = pyqtSignal(str)     # 出错，传出错误信息

    def __init__(self):
        super().__init__()
        self.recording = False
        self._thread = None
        self._proc = None
        self._start_time = 0
        self._timer = None
        self.monitor = None  # mss monitor dict
        self.region = None   # (left, top, width, height)

    def start(self, region=None, fps=None, output_path=None):
        """
        region: (left, top, width, height)，None 表示全屏主显示器
        """
        if self.recording:
            return

        fps = fps or config.get("record", "fps", default=30)
        output_path = output_path or self._default_path()

        # 确定录制区域
        if region is None:
            with mss.mss() as sct:
                mon = sct.monitors[1]  # 主显示器
                self.region = (mon["left"], mon["top"], mon["width"], mon["height"])
        else:
            self.region = region

        left, top, width, height = self.region
        # 偶数尺寸，H.264 要求
        width = width - (width % 2)
        height = height - (height % 2)
        self.region = (left, top, width, height)

        # 启动 FFmpeg 子进程，从 stdin 读取 raw RGB 帧
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        cmd = [
            ffmpeg, "-y",
            "-f", "rawvideo",
            "-pix_fmt", "rgb24",
            "-s", f"{width}x{height}",
            "-r", str(fps),
            "-i", "-",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            str(output_path)
        ]

        try:
            self._proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
        except Exception as e:
            self.failed.emit(f"FFmpeg 启动失败：{e}")
            return

        self._output_path = output_path
        self.recording = True
        self._start_time = time.time()

        # 启动采集线程
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

        # 计时信号
        self._timer = QTimer()
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(1000)

    def _capture_loop(self):
        left, top, width, height = self.region
        monitor = {"left": left, "top": top, "width": width, "height": height}

        with mss.mss() as sct:
            frame_interval = 1.0 / (config.get("record", "fps", default=30))
            while self.recording:
                t0 = time.time()
                try:
                    img = sct.grab(monitor)
                    frame = np.array(img)[:, :, :3]  # BGRA -> BGR? mss 返回 BGRA
                    # mss 返回 BGRA，转 RGB
                    frame = frame[:, :, [2, 1, 0]]
                    self._proc.stdin.write(frame.tobytes())
                except (BrokenPipeError, ValueError):
                    break
                # 控制帧率
                elapsed = time.time() - t0
                sleep_time = frame_interval - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

    def _on_tick(self):
        seconds = int(time.time() - self._start_time)
        self.tick.emit(seconds)

    def stop(self):
        if not self.recording:
            return
        self.recording = False
        if self._timer:
            self._timer.stop()

        # 等待采集线程结束
        if self._thread:
            self._thread.join(timeout=3)

        # 关闭 FFmpeg stdin，让它正常结束编码
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.stdin.close()
                self._proc.wait(timeout=10)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass

        path = getattr(self, "_output_path", "")
        if path and Path(path).exists():
            history.add("video", path)
            self.finished.emit(path)
        else:
            self.failed.emit("录制文件未生成")

    def _default_path(self):
        out_dir = Path(config.get("save", "output_dir", default=str(DEFAULT_OUTPUT_DIR)))
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        return str(out_dir / f"SnipDeck_{ts}.mp4")


recorder = ScreenRecorder()
