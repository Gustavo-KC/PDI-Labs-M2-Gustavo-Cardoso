"""Cria imagens sintéticas originais; seed fixa permite reproduzir os estudos."""
from pathlib import Path
import cv2
import numpy as np
root = Path(__file__).parent / 'images' / 'input'
root.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(20261020)
h, w = 220, 330
# Caso 1: cena clara com 3 objetos escuros separados e pequenos pixels espúrios.
a = np.full((h, w, 3), 225, np.uint8)
cv2.circle(a, (63, 83), 29, (35, 35, 35), -1)
cv2.rectangle(a, (144, 48), (202, 109), (45, 45, 45), -1)
cv2.circle(a, (262, 159), 32, (40, 40, 40), -1)
for x, y in [(13,14),(95,173),(206,182),(323,34),(130,17)]: a[y, x] = [12, 12, 12]
cv2.imwrite(str(root / 'cena_favoravel.png'), a)
# Caso 2: gradiente de iluminação, objetos escuros, contato e ruído.
grad = np.linspace(100, 235, w, dtype=np.float32)
b = np.tile(grad, (h, 1)) + rng.normal(0, 5, size=(h, w))
b = np.clip(b, 0, 255).astype(np.uint8)
cv2.circle(b, (74, 78), 32, 45, -1)
cv2.circle(b, (133, 90), 35, 57, -1)
cv2.rectangle(b, (219, 119), (277, 172), 61, -1)
cv2.circle(b, (251, 144), 7, 210, -1) # furo no objeto
for x,y in zip(rng.integers(0,w,60),rng.integers(0,h,60)):
    b[y,x] = 23
cv2.imwrite(str(root / 'cena_dificil.png'), cv2.cvtColor(b, cv2.COLOR_GRAY2BGR))
print('Imagens sintéticas criadas com semente 20261020')
