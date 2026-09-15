# -*- coding: utf-8 -*-
"""把 摄影作品/ 下的原图压缩成网页版，输出到 docs/photos/，并打印对应 HTML 片段。

用法: python build_photos.py
- 长边缩到 1600px，JPEG 质量 82，自动按 EXIF 转正
- 左图 = 文件名排序在前，右图 = 排序在后
- 漫展 人像 有 4 张，按 "1 (x)" / "2 (x)" 分成两组
"""
import os
from PIL import Image, ImageOps

SRC = "摄影作品"
OUT = os.path.join("docs", "photos")
MAX_SIDE = 1600
QUALITY = 82

# (文件夹名, 组标签, slug)  组标签为 None 表示整组一张对
GROUPS = [
    ("北京 祈年殿", None, "beijing-qiniandian"),
    ("天圆地方（天坛与地坛）", None, "tianyuan-difang"),
    ("颐和园", None, "yiheyuan"),
    ("圆明园", None, "yuanmingyuan"),
    ("暮色 建筑", None, "dusk-architecture"),
    ("秋日 氛围", None, "autumn-mood"),
    ("深圳 公园", None, "shenzhen-park"),
    ("潮州 凤凰天池", None, "chaozhou-fenghuangtianchi"),
    ("广州塔", None, "guangzhou-tower"),
    ("广州灯光节", None, "guangzhou-light-festival"),
    ("珠江新城日落", None, "zhujiangxincheng-sunset"),
    ("粤海关 夜景人像", None, "yuehaiguan-night-portrait"),
    ("漫展 人像", "（一）", "comiccon-portrait-1"),
    ("漫展 人像", "（二）", "comiccon-portrait-2"),
    ("给阿嬷的情书导演演员", None, "ama-director-actors"),
    ("给阿嬷的情书取景地", None, "ama-location"),
    ("云南 玉龙雪山", None, "yunnan-yulong"),
    ("云南 日照金山", None, "yunnan-jinshan"),
]


def compress(src, dst):
    img = Image.open(src)
    img = ImageOps.exif_transpose(img)
    if img.mode != "RGB":
        img = img.convert("RGB")
    w, h = img.size
    if max(w, h) > MAX_SIDE:
        scale = MAX_SIDE / max(w, h)
        img = img.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
    img.save(dst, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    return img.size


def main():
    os.makedirs(OUT, exist_ok=True)
    total_in = total_out = 0
    snippets = []
    for folder, suffix, slug in GROUPS:
        src_dir = os.path.join(SRC, folder)
        files = sorted(
            f for f in os.listdir(src_dir) if f.lower().endswith(".jpg")
        )
        if suffix:  # 漫展 两组：按文件名前缀 "1 "/"2 " 分
            prefix = "1" if suffix == "（一）" else "2"
            files = [f for f in files if f.startswith(prefix)]
        files = files[:2]
        img_names = []
        for i, f in enumerate(files, 1):
            dst = os.path.join(OUT, f"{slug}-{i}.jpg")
            size = compress(os.path.join(src_dir, f), dst)
            total_in += os.path.getsize(os.path.join(src_dir, f))
            total_out += os.path.getsize(dst)
            img_names.append((os.path.basename(dst), size))
        label = folder + (suffix or "")
        alt = folder
        snippets.append(f'''        <figure class="photo-pair">
            <div class="photo-duo">
                <img src="photos/{img_names[0][0]}" alt="{alt}" loading="lazy">
                <img src="photos/{img_names[1][0]}" alt="{alt}" loading="lazy">
            </div>
            <figcaption>{label}</figcaption>
        </figure>''')
    print(f"压缩完成: {len(snippets)} 组, "
          f"{total_in/1e6:.1f}MB -> {total_out/1e6:.1f}MB")
    print("\n".join(snippets))


if __name__ == "__main__":
    main()
