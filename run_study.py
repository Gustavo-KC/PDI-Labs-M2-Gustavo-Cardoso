"""Reproduz os dois casos em todos os estágios e prepara um quadro comparativo."""
from pathlib import Path
import csv
import json
import cv2
import numpy as np
from pdi_lab.__main__ import segment, analyze, write_image

root = Path(__file__).parent
records = []
for case in ('cena_favoravel', 'cena_dificil'):
    img = cv2.imread(str(root/'images/input'/f'{case}.png'))
    for method in ('fixed', 'otsu'):
        mask = segment(img, method, threshold=120, invert=True)
        write_image(root/'images/output'/f'{case}_{method}_mask.png', mask)
        ratio = float(np.count_nonzero(mask)/mask.size)
        records.append({'image':case,'method':method,'threshold':120 if method=='fixed' else 'otsu_auto',
                        'foreground_pixels':int(np.count_nonzero(mask)),'foreground_ratio':f'{ratio:.5f}'})
        # Visualização: objetos coloridos em vermelho transparente sobre original.
        overlay = img.copy()
        red = np.zeros_like(img);red[:,:,2]=255
        overlay[mask>0] = cv2.addWeighted(img,.55,red,.45,0)[mask>0]
        write_image(root/'images/output'/f'{case}_{method}_overlay.png',overlay)
    # Otsu foi escolhida para ambas; contraste com limiar 120 ilustrado no relatório.
    src = root/'images/output'/f'{case}_otsu_mask.png'
    analyze(cv2.imread(str(src),cv2.IMREAD_UNCHANGED),root/'results'/case,8,20,3,'ellipse','open,close',1)
    # Comparação visual com rótulos e máscara final.
    def tile(im, title):
        im = cv2.resize(im,(330,220)); cv2.putText(im,title,(7,20),cv2.FONT_HERSHEY_SIMPLEX,.56,(0,120,255),2)
        return im
    stages = [img,cv2.imread(str(src)),cv2.imread(str(root/'results'/f'{case}_stage1_open.png')),
              cv2.imread(str(root/'results'/f'{case}_stage2_close.png')),
              cv2.imread(str(root/'results'/f'{case}_labels.png'))]
    stages = [cv2.cvtColor(v,cv2.COLOR_GRAY2BGR) if v.ndim==2 else v for v in stages]
    panel = np.hstack([tile(v,t) for v,t in zip(stages,['Original','Otsu','Abertura','Fechamento','Rotulos'])])
    write_image(root/'results'/f'{case}_comparison.png',panel)
with open(root/'results'/'segmentation_comparison.csv','w',newline='',encoding='utf-8') as f:
    writer=csv.DictWriter(f,fieldnames=records[0].keys());writer.writeheader();writer.writerows(records)
print(json.dumps(records,ensure_ascii=False,indent=2))
