# SRB2 - Neo Metal

Neo Metal Sonic como forma extra do Metal Sonic no **Sonic Robo Blast 2** (SRB2): quando o Metal fica Super com as 7 Esmeraldas do Caos, ele vira o Neo. O Neo é um modelo 3D (MD3) cerca de 1,45 vez mais alto que o Metal, e as poses dele saem de um rig no Blender.

Este repositório guarda os scripts do Blender que posam o Neo e montam as folhas de conferência dos golpes. É público só para leitura: issues e wiki estão desligadas.

## O que tem aqui

`blender/` tem os scripts Python que rodam dentro do Blender 5.2 sem tela (`blender -b`) e alguns que rodam no Python do sistema, só para montar as folhas com PIL.

| Grupo | Exemplos | O que fazem |
|---|---|---|
| Golpes | `golpes_soco.py`, `golpes_chute.py`, `golpes_ref.py`, `golpes_medidas.py`, `golpes_medidas_chute.py` | Medem os golpes do Dark Sonic no modelo de referência e posam o Neo por cima dele, quadro a quadro |
| Poses | `braco_poses.py`, `perna_poses.py`, `mao_poses.py`, `punho_fechado.py` | Tronco, braços e pernas por alvo (IK de dois ossos com uma haste que estica ou encolhe) e as bibliotecas de mão e pé |
| Render | `renderizar_*.py`, `render_usuario.py`, `juntar_camera.py` | Fotografam o Neo em ângulos e quadros fixos |
| Folhas | `montar_*.py`, `sobrepor.py` | Montam as folhas de comparação: contorno da referência por cima do Neo, antes e depois na mesma câmera |
| Rodadas | `rodar_*.sh` | Chamam o Blender com os argumentos de cada etapa (`rodar_parte2.sh` a `rodar_parte4.sh` = chute por partes) |
| Modelo | `importar_md3.py`, `separar_partes.py`, `tabela_ilhas.py`, `corrigir_*.py`, `analisar_*.py`, `verificar_pontas.py` | Importação, inspeção e correções do modelo (pesos, espinhos, cinto, ilhas sem peso) |
| Estudos | `_*.py` | Testes e depuração de uma vez só, guardados como histórico |

## O que não tem aqui

Nenhum arquivo do jogo, modelo (MD3, FBX, .blend), textura, sprite ou render de personagem. Os personagens e os modelos pertencem aos donos deles. Os scripts precisam desses arquivos na máquina local para rodar; sozinhos, servem para ler e estudar.

## Como roda

No Git Bash, na pasta de trabalho do Neo (com o `.blend` local):

```bash
blender -b neo_base_pose.blend --python blender/golpes_chute.py -- saida 273,274,275,276 560 - 1.4 - 1 1.45 1.4 1.0
```

Argumentos: pasta de saída, quadros do modelo de referência, tamanho da imagem em pixels, mão do soco (`-`), escala da perna, escala da coxa (`-`), alinhar (1 ou 0), escala do corpo, da capa e do cinto. As variáveis de ambiente opcionais (`NEO_CAMERA_JSON`, `NEO_PE_FRACAO`, `NEO_MAO`, `NEO_COMPRIME_BRACO` e outras) são lidas no começo de `golpes_chute.py`.

## Estado (novembro de 2026)

- Feito: modelo 3D no jogo, idle, andar, voo, corrida, bibliotecas de mão e pé, soco (TAL1).
- Em andamento: chute (TAL2), refeito por partes com o Neo por cima do modelo de referência. Pé e pernas aprovados; braços e mãos em ajuste; faltam corpo, placa e efeitos e a forma normal.
- Depois: avanço (TAL0), quedas e pancada no chão (TAL4).

## Créditos

SRB2 é da Sonic Team Junior. Sonic, Metal Sonic e Neo Metal Sonic são da SEGA. Os modelos usados como base e como referência são de terceiros e não estão neste repositório.
