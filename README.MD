# Fast Bluestacks screenshots with pywin32

## pip install nescree32

### Tested against Windows 10 / Python 3.11 / Anaconda / BlueStacks


```PY
# pywin32 is not listed in requirements.txt
# install it using: pip install pywin32

from nescree32 import get_screenshots_from_bluestacks
import cv2

# INTER_NEAREST: int
# INTER_LINEAR: int
# INTER_CUBIC: int
# INTER_AREA: int
# INTER_LANCZOS4: int
# INTER_LINEAR_EXACT: int
# INTER_NEAREST_EXACT: int
# INTER_MAX: int
# WARP_FILL_OUTLIERS: int
# WARP_INVERSE_MAP: int

interpolation = cv2.INTER_AREA
show_original_android_size = True
bst_instance = "Rvc64_37"
adb_path = r"C:\ProgramData\chocolatey\lib\adb\tools\platform-tools\adb.exe"
printresults = False
show_fps = True
for (
    image,
    original_rect,
    start_x,
    start_y,
    width,
    height,
    end_x,
    end_y,
    adb_width,
    adb_height,
) in get_screenshots_from_bluestacks(
    instance_to_automate=bst_instance,
    adb_path=adb_path,
    show_fps=show_fps,
):
    if printresults:
        print(
            image.shape,
            original_rect,
            start_x,
            start_y,
            width,
            height,
            end_x,
            end_y,
            adb_width,
            adb_height,
        )
    if not show_original_android_size:
        # use this to automate via win32
        cv2.imshow(bst_instance, image)
    else:
        # use this to automate via adb.exe
        if adb_width == -1:
            adb_width = 900
        if adb_height == -1:
            adb_height = 1600
        image_original_adb = cv2.resize(
            image, (adb_width, adb_height), interpolation=interpolation
        )
        cv2.imshow(bst_instance, image_original_adb)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
cv2.destroyAllWindows()

```