import argparse
import csv
import json
import sys
from pathlib import Path

import cv2
import numpy as np


def error(msg):
    raise ValueError(msg)


def write_image(path, img):
    dest = Path(path)
    if dest.suffix.lower() != '.png':
        error('Saídas de imagem devem utilizar extensão .png')
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(dest), img):
        error(f'Falha ao gravar imagem: {dest}')


def read_image(path, gray=False):
    p = Path(path)
    if not p.is_file():
        error(f'Arquivo inexistente: {p}')
    data = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE if gray else cv2.IMREAD_COLOR)
    if data is None or data.size == 0:
        error(f'Imagem ilegível ou incompatível: {p}')
    return data


def validate_mask(mask):
    if mask.ndim != 2 or mask.dtype != np.uint8 or not np.isin(mask, (0, 255)).all():
        error('Máscara incompatível: exige 1 canal uint8 e valores exclusivamente 0/255')


def segment(image, method, threshold=120, invert=False, block_size=21, c=5):
    if threshold < 0 or threshold > 255:
        error('--threshold deve estar entre 0 e 255')
    if method not in ('fixed', 'otsu', 'adaptive'):
        error('Método inválido: use fixed, otsu ou adaptive')
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    typ = cv2.THRESH_BINARY_INV if invert else cv2.THRESH_BINARY
    if method == 'fixed':
        _, mask = cv2.threshold(gray, threshold, 255, typ)
    elif method == 'otsu':
        _, mask = cv2.threshold(gray, 0, 255, typ | cv2.THRESH_OTSU)
    else:
        if block_size <= 1 or block_size % 2 == 0:
            error('--block-size deve ser ímpar e maior que 1')
        if block_size > min(gray.shape):
            error('--block-size deve caber nas dimensões da imagem')
        mask = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, typ, block_size, c)
    validate_mask(mask)
    return mask


def components(mask, connectivity, min_area):
    n, labels, stats, centers = cv2.connectedComponentsWithStats(mask, connectivity=connectivity)
    rows = []
    for i in range(1, n):
        x, y, w, h, area = (int(v) for v in stats[i])
        rows.append({'label': i, 'area': area, 'x': x, 'y': y, 'width': w, 'height': h,
                     'cx': round(float(centers[i, 0]), 4), 'cy': round(float(centers[i, 1]), 4),
                     'kept': str(area >= min_area).lower()})
    if sum(r['area'] for r in rows) != int(np.count_nonzero(mask)):
        error('Inconsistência entre pixels brancos e áreas dos componentes')
    return labels, rows


def save_csv(path, rows):
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['label', 'area', 'x', 'y', 'width', 'height', 'cx', 'cy', 'kept'])
        writer.writeheader()
        writer.writerows(rows)


def visualize(mask, labels, rows):
    canvas = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
    for row in rows:
        x, y, w, h = (row[k] for k in ('x', 'y', 'width', 'height'))
        color = (0, 210, 0) if row['kept'] == 'true' else (0, 0, 230)
        cv2.rectangle(canvas, (x, y), (x + w - 1, y + h - 1), color, 1)
        cv2.putText(canvas, str(row['label']), (x, max(10, y - 3)), cv2.FONT_HERSHEY_SIMPLEX, .35, color, 1)
    return canvas


def analyze(mask, prefix, connectivity, min_area, kernel_size, kernel_shape, sequence, iterations):
    validate_mask(mask)
    if connectivity not in (4, 8): error('--connectivity deve ser 4 ou 8')
    if min_area < 0: error('--min-area deve ser inteiro não negativo')
    if kernel_size < 1 or kernel_size % 2 == 0 or kernel_size > min(mask.shape):
        error('--kernel-size deve ser ímpar, positivo e caber na máscara')
    if iterations < 1: error('--iterations deve ser >= 1')
    if kernel_shape not in ('rect', 'ellipse', 'cross'): error('--kernel-shape inválido')
    names = sequence.split(',')
    allowed = {'open': cv2.MORPH_OPEN, 'close': cv2.MORPH_CLOSE, 'erode': cv2.MORPH_ERODE, 'dilate': cv2.MORPH_DILATE}
    if len(names) < 2 or any(n not in allowed for n in names) or not ({'open', 'close'} & set(names)):
        error('--sequence exige pelo menos 2 operações válidas, incluindo open ou close')
    if len(set(names)) != len(names): error('Não repita operações na mesma sequência')
    p = Path(prefix)
    p.parent.mkdir(parents=True, exist_ok=True)
    write_image(str(p) + '_initial.png', mask)
    labels_ini, rows_ini = components(mask, connectivity, min_area)
    _, rows4 = components(mask, 4, min_area)
    _, rows8 = components(mask, 8, min_area)
    save_csv(str(p) + '_initial.csv', rows_ini)
    structuring = cv2.getStructuringElement({'rect': cv2.MORPH_RECT, 'ellipse': cv2.MORPH_ELLIPSE, 'cross': cv2.MORPH_CROSS}[kernel_shape], (kernel_size, kernel_size))
    current = mask.copy()
    stages = []
    for idx, name in enumerate(names, start=1):
        current = cv2.morphologyEx(current, allowed[name], structuring, iterations=iterations)
        stage_file = str(p) + f'_stage{idx}_{name}.png'
        write_image(stage_file, current)
        stages.append({'operation': name, 'path': Path(stage_file).name, 'foreground_pixels': int(np.count_nonzero(current))})
    labels_fin, rows_fin = components(current, connectivity, min_area)
    save_csv(str(p) + '_final.csv', rows_fin)
    write_image(str(p) + '_final.png', current)
    write_image(str(p) + '_labels.png', visualize(current, labels_fin, rows_fin))
    def summary(rows, img):
        return {'components_raw': len(rows), 'components_filtered': sum(r['kept'] == 'true' for r in rows),
                'foreground_area_total': int(np.count_nonzero(img)), 'area_kept': sum(r['area'] for r in rows if r['kept'] == 'true')}
    payload = {'connectivity': connectivity, 'initial_connectivity_4': len(rows4), 'initial_connectivity_8': len(rows8),
               'min_area': min_area, 'kernel_size': kernel_size, 'kernel_shape': kernel_shape,
               'iterations_per_operation': iterations, 'sequence': names, 'stages': stages,
               'initial': summary(rows_ini, mask), 'final': summary(rows_fin, current)}
    with open(str(p) + '_summary.json', 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return payload


def main(argv=None):
    parser = argparse.ArgumentParser(prog='python -m pdi_lab', description='M2.1 segmentação; M2.2 componentes e morfologia')
    parser.add_argument('--operation', required=True, choices=['segment', 'analyze'])
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--method', default='fixed', help='fixed, otsu ou adaptive')
    parser.add_argument('--threshold', type=int, default=120)
    parser.add_argument('--invert', action='store_true')
    parser.add_argument('--block-size', type=int, default=21)
    parser.add_argument('--c', type=float, default=5)
    parser.add_argument('--connectivity', type=int, default=8)
    parser.add_argument('--min-area', type=int, default=20)
    parser.add_argument('--kernel-size', type=int, default=3)
    parser.add_argument('--kernel-shape', default='ellipse', choices=['rect', 'ellipse', 'cross'])
    parser.add_argument('--sequence', default='open,close')
    parser.add_argument('--iterations', type=int, default=1)
    parser.add_argument('--version', action='version', version='1.0.0')
    args = parser.parse_args(argv)
    try:
        if args.operation == 'segment':
            img = read_image(args.input)
            mask = segment(img, args.method, args.threshold, args.invert, args.block_size, args.c)
            write_image(args.output, mask)
            print(json.dumps({'method': args.method, 'width': mask.shape[1], 'height': mask.shape[0],
                              'foreground_pixels': int(np.count_nonzero(mask)), 'foreground_ratio': float(np.count_nonzero(mask)/mask.size)}))
        else:
            mask = read_image(args.input, gray=False)
            # IMREAD_UNCHANGED evita aceitar RGB ou conversão implícita para grayscale.
            mask = cv2.imread(args.input, cv2.IMREAD_UNCHANGED)
            if mask is None: error('Máscara ilegível')
            print(json.dumps(analyze(mask, args.output, args.connectivity, args.min_area,
                                     args.kernel_size, args.kernel_shape, args.sequence, args.iterations), ensure_ascii=False))
        return 0
    except (ValueError, OSError, cv2.error) as exc:
        print(f'Erro: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
