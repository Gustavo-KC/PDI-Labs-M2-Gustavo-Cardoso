"""Estudo complementar com fotografia real e recorte sem alteração de intensidades."""
from pathlib import Path
import cv2
import numpy as np
from pdi_lab.__main__ import segment, analyze, write_image
root = Path(__file__).parent
for case in ('moedas_original', 'moedas_recorte'):
    image = cv2.imread(str(root/'images/input'/f'{case}.png'))
    masks = []
    for method in ('fixed', 'otsu'):
        mask = segment(image, method, threshold=120)
        assert mask.shape == image.shape[:2]
        write_image(root/'images/output'/f'{case}_{method}_mask.png', mask)
        overlay = image.copy()
        red = np.zeros_like(image); red[:,:,2] = 255
        overlay[mask>0] = cv2.addWeighted(image,.55,red,.45,0)[mask>0]
        write_image(root/'images/output'/f'{case}_{method}_overlay.png', overlay)
        masks.append(mask)
        print(case, method, int(np.count_nonzero(mask)), float(np.count_nonzero(mask)/mask.size))
    summary = analyze(masks[1], root/'results'/case, 8, 20, 3, 'ellipse', 'open,close', 1)
    print(summary)
