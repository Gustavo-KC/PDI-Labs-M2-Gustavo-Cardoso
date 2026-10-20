# Laboratórios M2.1 e M2.2 — Processamento de Imagens

Projeto individual consolidado — Gustavo Koerich Cardoso. Código em Python, adaptado ao contrato técnico complementar da M2; o ZIP do professor serviu como referência de organização, porém os algoritmos aqui são um módulo específico da M2 (não dependem de operações M1).

## Instalação e execução (Windows, Linux, macOS)

Requer Python 3.10+ e OpenCV (pacote `opencv-python-headless`, versão >=4.8,<5), NumPy e pytest. Na validação realizada, foi utilizado OpenCV 4.14.0.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pdi_lab --help
python -m pdi_lab --version
python -m pytest -q
```

Execute todos os comandos a partir da pasta que contém este README. Para reproduzir todos os dados/figuras incluídos: `python generate_examples.py` e `python run_study.py`. Ambas as imagens são sintéticas, feitas pelo código `generate_examples.py`, com semente fixa; podem ser substituídas por outras imagens com permissão de uso.

## M2.1 — `segment`

```bash
python -m pdi_lab --operation segment --input images/input/cena_favoravel.png --output images/output/cena_favoravel_fixed_mask.png --method fixed --threshold 120 --invert
python -m pdi_lab --operation segment --input images/input/cena_favoravel.png --output images/output/cena_favoravel_otsu_mask.png --method otsu --invert
python -m pdi_lab --operation segment --input images/input/cena_dificil.png --output images/output/cena_dificil_fixed_mask.png --method fixed --threshold 120 --invert
python -m pdi_lab --operation segment --input images/input/cena_dificil.png --output images/output/cena_dificil_otsu_mask.png --method otsu --invert
```

`fixed` atribui objeto a intensidades menores ou iguais a 120, pois `--invert` ativa a polaridade invertida: imagem original de objetos escuros → objeto branco (255), fundo preto (0). Pixels iguais a 120 são objeto com `THRESH_BINARY_INV`. `otsu` seleciona automaticamente o limiar global em cinza. Método `adaptive` também está implementado e pode ser usado com `--block-size 21 --c 5`. Todos geram máscara PNG com canal único e valores 0/255. A saída do comando informa contagem/proporção de primeiro plano. Se `--invert` não for usado, o objeto selecionado será o lado claro do limiar.

## M2.2 — `analyze`

```bash
python -m pdi_lab --operation analyze --input images/output/cena_favoravel_otsu_mask.png --output results/cena_favoravel --connectivity 8 --min-area 20 --kernel-size 3 --kernel-shape ellipse --sequence open,close --iterations 1
python -m pdi_lab --operation analyze --input images/output/cena_dificil_otsu_mask.png --output results/cena_dificil --connectivity 8 --min-area 20 --kernel-size 3 --kernel-shape ellipse --sequence open,close --iterations 1
# Exemplo obrigatório com conectividade 4:
python -m pdi_lab --operation analyze --input images/output/cena_favoravel_otsu_mask.png --output results/exemplo_conn4 --connectivity 4 --min-area 20 --kernel-size 3 --kernel-shape ellipse --sequence open,close --iterations 1
```

Argumentos: `--connectivity` 4 ou 8 (padrão 8), `--min-area` inteiro >=0 (padrão 20); `--kernel-size` ímpar positivo (padrão 3); `--kernel-shape` `rect`, `ellipse` ou `cross` (padrão ellipse); `--iterations` positivo (padrão 1); `--sequence` operações distintas separadas por vírgula (`open`, `close`, `erode`, `dilate`) com pelo menos duas, sendo uma `open` ou `close`. Ex.: `--sequence close,erode` para outra hipótese. Para comparar casos diferentes, configure os argumentos sem alterar o código.

O prefixo de saída gera: `_initial.png` (cópia da máscara), `_initial.csv`, `_stage1_open.png`, `_stage2_close.png`, `_final.png`, `_final.csv`, `_labels.png` (caixas verdes = mantidas por filtro, vermelhas = removidas), `_summary.json`. A convenção de nomes das etapas acompanha a sequência passada. Os CSVs contêm `label,area,x,y,width,height,cx,cy,kept`; fundo excluído. O filtro não remove componentes da imagem, apenas marca `kept` nos CSVs; as contagens bruta/filtrada permanecem distintas.

Máscaras devem ser PNG, **um canal**, `uint8`, apenas 0 e 255, com objeto branco. Erros retornam código diferente de zero. Não depende de execução anterior: recebe qualquer máscara válida fornecida pelo usuário.

## Arquivos do projeto

- `pdi_lab/`: aplicação de linha de comando.
- `images/input/`: duas cenas originais de estudo, produzidas sinteticamente.
- `images/output/`: quatro máscaras e sobreposições.
- `results/`: CSVs, resumos JSON, máscaras intermediárias, imagens com caixas e painéis de comparação.
- `tests/`: testes automáticos; `run_study.py` reproduz os estudos.
- `REPORT.md`: análises M2.1 e M2.2; `AI_USAGE.md`: declaração do uso de IA; `lab.json`: identificação.

## Referências

Enunciados M2.1 e M2.2, contrato complementar e rubrica disponibilizados pelo professor no Moodle da disciplina (20/10/2026). Projeto-base de referência: https://github.com/m4rc3lo/pdi_template (licença Apache-2.0). OpenCV: https://docs.opencv.org/4.x/ .

## Estudo fotográfico complementar

Execute `python study_photos.py` para reproduzir a análise de moedas na fotografia completa e no recorte incluídos. As entradas e a atribuição estão documentadas em `REPORT.md`. O script usa as mesmas dependências, sem exigir scikit-image. As duas entradas derivam da mesma fotografia, limitação explicitada no relatório.
