import subprocess
import win32gui
import win32ui
import win32con
import sys
import numpy as np
import time
from nodepsutils import get_short_path_name_cached, invisibledict
import re
from getbstacksinfo import get_info_bluestacks


class WindowCapture:
    # constructor
    def __init__(self, hwnd):
        self.hwnd = hwnd
        self.window_rect = win32gui.GetWindowRect(self.hwnd)
        self.w = self.window_rect[2] - self.window_rect[0]
        self.h = self.window_rect[3] - self.window_rect[1]
        self.offset_x = self.window_rect[0]
        self.offset_y = self.window_rect[1]

    def get_window_position(self):
        self.window_rect = win32gui.GetWindowRect(self.hwnd)
        self.offset_x = self.window_rect[0]
        self.offset_y = self.window_rect[1]
        self.w = self.window_rect[2] - self.window_rect[0]
        self.h = self.window_rect[3] - self.window_rect[1]

    def get_screenshot(self, brg_to_rgb=False):
        allok = False
        try:
            self.get_window_position()
            wDC = win32gui.GetWindowDC(self.hwnd)
            dcObj = win32ui.CreateDCFromHandle(wDC)
            cDC = dcObj.CreateCompatibleDC()
            dataBitMap = win32ui.CreateBitmap()
            dataBitMap.CreateCompatibleBitmap(dcObj, self.w, self.h)
            cDC.SelectObject(dataBitMap)
            cDC.BitBlt((0, 0), (self.w, self.h), dcObj, (0, 0), win32con.SRCCOPY)
            signedIntsArray = dataBitMap.GetBitmapBits(True)
            img = np.frombuffer(signedIntsArray, dtype="uint8")
            img.shape = (self.h, self.w, 4)
            allok = True
        finally:
            try:
                dcObj.DeleteDC()
            except Exception:
                pass
            try:
                cDC.DeleteDC()
            except Exception:
                pass
            try:
                win32gui.ReleaseDC(self.hwnd, wDC)
            except Exception:
                pass
            try:
                win32gui.DeleteObject(dataBitMap.GetHandle())
            except Exception:
                pass
            if not allok:
                return (np.array([], dtype=np.uint8), (-1, -1, -1, -1), -1, -1, -1, -1)
        try:
            img2 = img[..., :3]
            if brg_to_rgb:
                img2 = img2[..., ::-1]
            return (
                np.ascontiguousarray(img2),
                self.window_rect,
                self.offset_x,
                self.offset_y,
                self.w,
                self.h,
            )
        except Exception as e:
            sys.stderr.write(str(e))
            sys.stderr.flush()
            return (np.array([], dtype=np.uint8), (-1, -1, -1, -1), -1, -1, -1, -1)


def cropimage(img, coords):
    return img[coords[1] : coords[3], coords[0] : coords[2]]


def adb_get_screenwidth(adb_path, deviceserial):
    ADB_SHELL_DUMPSYS_WINDOW = "dumpsys window"
    ADB_SHELL_GET_WM_SIZE = "wm size"
    screenres_reg_cur = re.compile(rb"\bcur=(\d+)x(\d+)\b")
    screenres_reg = re.compile(rb"\b(\d+)x(\d+)\b")
    adbshort = get_short_path_name_cached(adb_path)
    try:
        width, height = [
            [int(g[0][0]), int(g[0][1])]
            for x in subprocess.run(
                f'{adbshort} -s {deviceserial} shell "{ADB_SHELL_DUMPSYS_WINDOW}"',
                capture_output=True,
                **invisibledict,
            ).stdout.splitlines()
            if (g := screenres_reg_cur.findall(x))
        ][0]
    except Exception:
        width, height = [
            [int(g[0][0]), int(g[0][1])]
            for x in subprocess.run(
                f'{adbshort} -s {deviceserial} shell "{ADB_SHELL_GET_WM_SIZE}"',
                capture_output=True,
                **invisibledict,
            ).stdout.splitlines()
            if (g := screenres_reg.findall(x))
        ][0]
    return width, height


def get_screenshots_from_bluestacks(
    instance_to_automate,
    adb_path,
    show_fps=False,
):
    (
        data,
        bstconfigpath,
        bstconfigpath_folder,
        bstconfigpath_folder_short,
        bstconfigpath_short,
        bluestacksinstances,
    ) = get_info_bluestacks()

    try:
        hwnd = bluestacksinstances[instance_to_automate]["window_hwnd"]
        x, y = bluestacksinstances[instance_to_automate]["keymap_dim"]
        adbport = bluestacksinstances[instance_to_automate]["adbport"]
    except Exception:
        bluestacksinstances[instance_to_automate]["startcommand"]()
        while True:
            time.sleep(5)
            try:
                (
                    data,
                    bstconfigpath,
                    bstconfigpath_folder,
                    bstconfigpath_folder_short,
                    bstconfigpath_short,
                    bluestacksinstances,
                ) = get_info_bluestacks()

                hwnd = bluestacksinstances[instance_to_automate]["window_hwnd"]
                x, y = bluestacksinstances[instance_to_automate]["keymap_dim"]
                adbport = bluestacksinstances[instance_to_automate]["adbport"]
                break
            except Exception:
                time.sleep(5)

    hwnd_screenshot_grabber = WindowCapture(hwnd)
    deviceserial = f"127.0.0.1:{adbport}"
    try:
        screenadbx, screenadby = adb_get_screenwidth(adb_path, deviceserial)
    except Exception:
        screenadbx, screenadby = -1, -1

    while True:
        try:
            if show_fps:
                loop_time = time.time()
            (
                ctypescreen,
                window_rect,
                offset_x,
                offset_y,
                w,
                h,
            ) = hwnd_screenshot_grabber.get_screenshot(brg_to_rgb=False)
            if len(ctypescreen) == 0 and w == -1 and h == -1:
                break
            yield (
                cropimage(
                    ctypescreen, (1, ctypescreen.shape[0] - y, x, ctypescreen.shape[0])
                ),
                window_rect,
                offset_x,
                offset_y + y,
                w - x,
                h - y,
                offset_x + w - x,
                offset_y + h - y,
                screenadbx,
                screenadby,
            )
            if show_fps:
                print(
                    "FPS {}            ".format(1 / (time.time() - loop_time)), end="\r"
                )
        except Exception as fe:
            sys.stderr.write(f"{fe}\n")
            sys.stderr.flush()
        except KeyboardInterrupt:
            try:
                time.sleep(1)
            except:
                pass
            break
