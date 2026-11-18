# Comparação de heurísticas para o Block Relocation Problem (BRP)

[![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/alanssoares/ufba-relocation-problem-analysis/blob/main/notebooks/brp_demo.ipynb)

Implementação e comparação experimental de métodos para o Block Relocation Problem (BRP), nas
variantes restrita e irrestrita:

1. **Min-Max** (Caserta, Voß & Sniedovich, 2012): heurística construtiva de referência.
2. **A\*** (exato): busca com garantia de otimalidade, usada como referência na variante restrita.
3. **GLAH-R**: heurística gulosa com *look-ahead* (busca em árvore limitada), adaptada da
   proposta de Jin, Zhu & Lim (2015) para a variante restrita do BRP.
4. **GLAH-U**: a mesma heurística, como publicada no artigo, na variante irrestrita.
5. **A\*-U** (exato): referência exata da variante irrestrita.

**Acesso rápido:**

- [Demonstração no Google Colab](https://colab.research.google.com/github/alanssoares/ufba-relocation-problem-analysis/blob/main/notebooks/brp_demo.ipynb):
  roda os testes, resolve qualquer instância nas duas variantes, mostra a solução passo a passo e
  aceita uma instância digitada na hora. Não precisa instalar nada.
  O notebook está em [`notebooks/brp_demo.ipynb`](notebooks/brp_demo.ipynb).
- [Achados dos resultados e roteiro para a apresentação](brp_study/ACHADOS.md)
- [Resultados da variante restrita](brp_study/results/summary.md) ·
  [Resultados da variante irrestrita](brp_study/results/summary_unrestricted.md)
- [Instâncias e regras da disciplina](data/instances/LEIAME.md)
- [Código](brp_study/): [`brp.py`](brp_study/brp.py) (variante restrita) e
  [`brp_unrestricted.py`](brp_study/brp_unrestricted.py) (variante irrestrita)

Artigo de referência (arquivo em `artigos/`):

> B. Jin, W. Zhu, A. Lim. *Solving the container relocation problem by an improved greedy
> look-ahead heuristic.* European Journal of Operational Research 240 (2015) 837–847.
> `artigos/1-s2.0-S0377221714006043-main.pdf`

As instâncias estão em `data/instances/`. O arquivo `data/instances/LEIAME.md` define a
variante do problema, o formato dos arquivos e as regras de reporte.

Além da variante restrita (seções 1 a 10), o projeto implementa a **variante irrestrita**
com o método do artigo sem adaptações (**GLAH-U**) e um A\* exato próprio (**A\*-U**). Os
resultados ficam separados dos da variante restrita (seção 11).

A implementação usa apenas a biblioteca padrão do Python (3.10 ou superior). Nenhum pacote
externo é necessário.

---

## 1. Problema

Variante **restrita, única, determinística e estática** do BRP:

- Os contêineres são numerados de 1 a N. O número é a **ordem de retirada**: o 1 sai primeiro.
- O pátio tem W pilhas, cada uma com altura máxima H.
- Um contêiner só sai quando está no topo da sua pilha. A retirada é automática e gratuita:
  assim que o alvo atual (menor número ainda no pátio) estiver no topo, ele sai.
- **Restrito:** só podem ser relocados os contêineres acima do alvo atual, e apenas a partir
  da pilha do alvo. Cada relocação custa **1 reposicionamento** (*reshuffle*).
- Nenhuma pilha pode passar da altura H em nenhum momento.
- **Objetivo:** retirar todos os contêineres com o menor número de reposicionamentos.

Todas as instâncias satisfazem `W·H − N ≥ H − 1`, o que garante que sempre existe destino
com espaço para a relocação.

## 2. Estrutura do projeto

Todo o código fica em [`brp_study/`](brp_study/). Os caminhos abaixo são relativos à raiz do
repositório.

| Arquivo | Conteúdo |
|---|---|
| [`brp_study/brp.py`](brp_study/brp.py) | Modelo do problema, verificador independente, Min-Max, A*, GLAH-R, condensação e busca em largura (BFS) de referência |
| [`brp_study/run_experiments.py`](brp_study/run_experiments.py) | Executa a comparação em todos os arquivos de instâncias, verifica as soluções e grava os resultados |
| [`brp_study/test_brp.py`](brp_study/test_brp.py) | Testes unitários: regras do verificador, A* contra BFS em casos pequenos, validade das soluções do GLAH-R, integridade dos dados |
| [`brp_study/brp_unrestricted.py`](brp_study/brp_unrestricted.py) | Variante irrestrita: limite inferior do artigo, BFS, A\*-U e GLAH-U (seção 11) |
| [`brp_study/test_brp_unrestricted.py`](brp_study/test_brp_unrestricted.py) | Testes da variante irrestrita: verificador, limite inferior, A\*-U contra BFS, casos do nível inferior, categorias de relocação, GLAH-U |
| [`brp_study/demo.py`](brp_study/demo.py), [`brp_study/test_demo.py`](brp_study/test_demo.py) | Funções de apoio para demonstrações (desenho do pátio, solução passo a passo, comparação de todos os métodos numa instância) e seus testes |
| [`notebooks/brp_demo.ipynb`](notebooks/brp_demo.ipynb) | Notebook de demonstração para o Google Colab |
| `README.md` | Este documento |
| [`brp_study/ACHADOS.md`](brp_study/ACHADOS.md) | Achados dos resultados das duas variantes, com tabelas, exemplo ilustrado e roteiro para a apresentação |
| [`brp_study/results/results_long.csv`](brp_study/results/results_long.csv) | Uma linha por par (instância, método), com a sequência completa de relocações |
| [`brp_study/results/summary.md`](brp_study/results/summary.md) | Tabelas gerais e por arquivo, geradas pelo script |
| [`brp_study/results/unrestricted_long.csv`](brp_study/results/unrestricted_long.csv), [`brp_study/results/summary_unrestricted.md`](brp_study/results/summary_unrestricted.md) | O mesmo para a variante irrestrita, mais a comparação com a restrita |
| `brp_study/run_log.txt`, `brp_study/run_log_unrestricted.txt` | Saída local das execuções completas (não versionada, ver `.gitignore`) |
| [`data/instances/`](data/instances/) | As 17 instâncias da disciplina e o [`LEIAME.md`](data/instances/LEIAME.md) com as regras |
| `artigos/` | PDF do artigo de referência (não versionado) |
| [`.github/workflows/brp-evaluation.yml`](.github/workflows/brp-evaluation.yml) | Execução manual da comparação no GitHub Actions |

## 3. Mecânica comum (`brp.py`)

- **Representação.** As pilhas são listas, da base para o topo. Os movimentos são pares
  `(origem, destino)` com pilhas numeradas a partir de 1, o mesmo formato do `LEIAME.md`.
- **Retirada automática** (`_stabilize`). Após cada relocação, o alvo é retirado enquanto
  estiver no topo da sua pilha.
- **Verificador** (`verify`). Refaz uma sequência de relocações a partir da configuração
  inicial e rejeita o movimento se: a origem estiver fora do intervalo, for igual ao destino,
  estiver vazia, não contiver o alvo atual (regra da variante restrita), ou o destino estiver
  cheio (H). No fim, o pátio precisa estar vazio. **Toda solução reportada nas tabelas passa
  por esta verificação.**
- **Limite inferior** (`badly_placed`). Número de contêineres que têm um número menor
  em alguma posição abaixo deles na mesma pilha. Cada um deles precisa ser relocado pelo menos
  uma vez, então o limite é válido. É usado como heurística `h` do A* e para podar a árvore
  do GLAH-R.

## 4. Referência 1: Min-Max (Caserta, Voß & Sniedovich, 2012)

Regra construtiva com uma decisão por contêiner bloqueador, do topo para a base.

Para o bloqueador `r` no topo da pilha do alvo `s`:

- `D = { i ≠ s : altura(i) < H }`
- `min(i)` = menor número na pilha `i` (`N+1` se a pilha estiver vazia)
- Se existe `i ∈ D` com `min(i) > r`, escolhe-se a pilha com o **menor** `min(i)` entre elas.
- Caso contrário, escolhe-se a pilha com o **maior** `min(i)`.
- Empates: menor índice de pilha.

Determinística, executa em milissegundos.

## 5. Referência 2: A* (exato)

- **Estado:** a configuração completa do pátio, após as retiradas automáticas.
- **Sucessores:** o único movimento legal é mover o contêiner do topo da pilha do alvo para
  outra pilha com espaço. Custo unitário.
- **Função de avaliação** `f = g + h`, com `h` = `badly_placed` (admissível).
- **Duplicatas:** guarda-se o menor `g` de cada estado. Um estado é reexpandido se um
  caminho mais barato for encontrado, o que mantém o A* ótimo com `h` admissível.
- **Objetivo:** pátio vazio. O primeiro objetivo retirado da fila é ótimo.
- **Limite de tempo:** ao esgotar o orçamento, o resultado é `timeout` e o menor `f` restante
  na fila aberta é reportado como **limite inferior** do ótimo. Para calcular o gap, usa-se
  como `Z*` a melhor solução verificada entre todos os métodos (ver §7).
- **Validação cruzada:** `test_brp.py` compara o A* com uma busca em largura independente
  nas quatro primeiras instâncias de `W3_H4_N8` e no exemplo do `LEIAME.md`. Um script
  auxiliar também comparou as 10 instâncias de `W4_H4_N10`, `W5_H4_N15` e `W5_H5_N18`
  (0 divergências). Os arquivos da série W7 não foram cobertos por essa comparação.

## 6. Método proposto: GLAH-R (heurística gulosa com look-ahead, variante restrita)

A proposta de Jin, Zhu & Lim (2015) tem três níveis. Mantemos a estrutura e os valores de
parâmetro do artigo e adaptamos os movimentos à variante restrita. A tabela 6.3 lista todas
as mudanças.

### 6.1 Níveis

**Nível superior: mecanismo guloso.** Começa com uma solução inicial `Z` obtida pelo nível
inferior. Em cada etapa:
- se `|sol_atual| + LB(L) ≥ |melhor|`, para;
- senão, pede ao nível intermediário uma relocação, aplica, retira o que estiver livre e repete
  até o pátio ficar vazio.

**Nível intermediário: busca em árvore com look-ahead.**
- Cada nó é uma configuração do pátio. Os filhos são os destinos possíveis para o bloqueador
  atual.
- Os destinos candidatos (`reloList`) vêm de duas categorias:
  - **FT-BG:** destinos que sustentam o bloqueador (`min(s2) > r`). Ordenados pela folga
    `min(s2) − r` em ordem crescente; mantêm-se os primeiros `n_FT-BG = 5`.
  - **FT-BB:** demais destinos (`min(s2) < r`). Ordenados por `r − min(s2)` em ordem crescente;
    mantêm-se os primeiros `n_FT-BB = 3`.
  - A escolha do nível inferior é acrescentada, se ainda não estiver na lista (correção de
    sincronização entre os níveis).
- **Profundidade** `D`: testamos `D = 3` e `D = 4`, os dois valores usados no artigo.
- **Folha** (profundidade `D`, ou pátio vazio): avalia-se a folha com o nível inferior. Custo da
  folha = `d + |sequência avaliada|`, em que `d` é a profundidade da folha. Cada nó interno
  recebe o menor custo entre seus filhos.
- **Poda:** um nó é descartado quando `|sol_atual| + d + LB(L_d) ≥ |melhor|`.
- O conselho dado ao nível superior é o primeiro movimento do caminho de menor custo.

**Nível inferior: heurística de avaliação.** Completa uma configuração com uma decisão por
bloqueador, seguindo os casos 1, 3 e 4 do artigo:
- **Caso 1:** uma pilha que sustenta o bloqueador (`min > r`) e tem o menor mínimo.
- **Casos 3 e 4:** caso contrário, a pilha com o maior mínimo. Se essa pilha tiver altura
  `H − 1` e o bloqueador não for o menor número entre os contêineres acima do alvo, escolhe-se
  a segunda maior (verificação especial do caso 3).

**Completar e condensar.** Cada solução completa passa por condensação (artigo, seção 4.3.5):
dois movimentos consecutivos do mesmo contêiner, `s1→s2` e depois `s2→s3`, são unidos em
`s1→s3` quando nenhum contêiner sai ou entra em `s3` no intervalo. A união só é aceita se a
solução inteira continuar válida pela verificação. A melhor solução verificada é a incumbente.

### 6.2 Parâmetros

| Parâmetro | Valor | Observação |
|---|---|---|
| `D` (profundidade do look-ahead) | 3 e 4 | ambos reportados |
| `n_FT-BG` | 5 | |
| `n_FT-BB` | 3 | |
| `n_GG`, `n_GB` | 1 | não usados: movimentos GG e GB realocam contêineres que não são bloqueadores, o que a variante restrita proíbe |
| Limite de tempo | `--time-limit` (padrão 30 s por instância e método) | ver §7 |

### 6.3 Adaptações em relação ao artigo

| Componente | No artigo | Aqui | Motivo |
|---|---|---|---|
| Categorias de relocação | FT-BG, NF-BG, FT-BB, NF-BB, GG, GB | apenas FT-BG e FT-BB | Só os bloqueadores do alvo podem se mover. Todo bloqueador está mal posicionado e libera o alvo; as categorias NF-* e GG/GB não ocorrem. |
| Ramificação do look-ahead | qualquer relocação | destinos do bloqueador atual | Na variante restrita, o contêiner movido é determinado pela regra. |
| Caso 2 do nível inferior (liberar espaço movendo um não bloqueador) | sim | **removido** | Move um contêiner que não está acima do alvo. |
| Aproveitamento de folga (seção 4.3.3) | sim | **removido** | Move contêineres que não são bloqueadores para preencher folgas. |
| Limite inferior (seção 4.1.1) | contagem de mal posicionados + termo binário extra | apenas a contagem | O termo extra foi derivado para o problema irrestrito. Removê-lo enfraquece a poda, não a corretude. |
| Condensação (seção 4.3.5) | condições 1 a 3 | condições 1 a 3 + nova verificação completa | Na variante restrita, as retiradas também mudam o topo das pilhas; a verificação garante a viabilidade. |
| Casos 1, 3 e 4 com verificação especial | sim | sim | — |

**Consequência:** sem o caso 2 e sem o aproveitamento de folga, o nível inferior é igual ao
Min-Max, exceto pela verificação especial do caso 3. Assim, o ganho do GLAH-R sobre o Min-Max
vem do look-ahead e da condensação, que são as partes do método compatíveis com a variante
restrita.

### 6.4 Complexidade

A árvore de look-ahead tem no máximo `(n_FT-BG + n_FT-BB + 1)^D` folhas por etapa, que na
prática fica limitado a `(W − 1)^D`. Cada folha executa uma avaliação completa pelo nível
inferior. O tempo cresce rapidamente com `D` e com `W`. O limite de tempo torna o método
interrompível: quando o orçamento se esgota, devolve a melhor incumbente encontrada e marca a
execução como `timeout`.

## 7. Protocolo de comparação

| Regra | Aplicação |
|---|---|
| Instâncias pequenas, com ótimo obtido pelo A* | **Conjunto A:** `brp_W3_H4_N8`, `brp_W4_H4_N10`, `brp_W4_H5_N12`, `brp_W5_H4_N15`, `brp_W5_H5_N18` |
| Instâncias maiores | **Conjunto B:** arquivos `brp_W7_*` (W = 7, H de 5 a 8, N até 49), usados como fornecidos. Não são o conjunto da literatura de Caserta et al. (2011). |
| Referências: Min-Max e A* com `h` = bloqueadores | §4 e §5 |
| Métricas: reposicionamentos; gap = (Z − Z\*)/Z\*; tempo | colunas `reshuffles`, `gap_pct`, `time_s` |
| Mesmo limite de tempo por instância | `--time-limit` vale para o A* e para o GLAH-R |
| Métodos aleatórios: várias sementes, média e melhor valor | Nenhum dos quatro métodos é aleatório, então não há sementes. Cada método roda uma vez por instância. |
| Toda solução verificada (viável, respeita H) | `verify` em todas as soluções; o script conta as soluções não verificadas |

**Valor de referência Z\*.** Se o A* provar a otimalidade, `Z*` é o ótimo dele. Caso contrário,
`Z*` é a melhor solução verificada entre todos os métodos. O limite inferior do A* fica na
coluna `lower_bound`, para cálculo de gap em relação ao limite quando necessário.

## 8. Como reproduzir

Requisito: Python 3.10 ou superior.

```powershell
# a partir da raiz do projeto
python -m unittest discover -s brp_study -v           # testes unitários
python brp_study\run_experiments.py                    # execução completa, 30 s por instância e método
python brp_study\run_experiments.py --only W5_H5       # um único arquivo
python brp_study\run_experiments.py --variant unrestricted   # variante irrestrita (seção 11)
python brp_study\run_experiments.py --variant both           # as duas, na ordem restrita -> irrestrita
```

Os resultados vão para `brp_study/results/`:

- `results_long.csv`: uma linha por (instância, método), com `reshuffles`, `verified`, `z_star`,
  `z_star_source`, `gap_pct`, `time_s`, `lower_bound`, `nodes` e a sequência de relocações em
  JSON (pares `[origem, destino]` com pilhas a partir de 1, como no `LEIAME.md`).
- `summary.md`: tabelas gerais e por arquivo.

Para conferir uma solução manualmente, reexecute os `moves` com `brp.verify`:

```python
import sys
sys.path.insert(0, "brp_study")
from brp import load_instances, verify
from pathlib import Path

inst = load_instances(Path("data/instances/brp_W3_H4_N8.json"))[0]
print(verify(inst, [(3, 2), (3, 2), (3, 1)]))   # formato de exemplo do LEIAME.md
```

## 9. Resultados

Execução completa: 170 instâncias (17 arquivos), 4 métodos, orçamento de 30 s por instância e
método, em uma máquina Windows com Python 3.13. Resultado: **680 linhas, todas as soluções
verificadas** (0 falhas). Tempo total de execução: cerca de 17 minutos. Os valores completos
estão em [`brp_study/results/summary.md`](brp_study/results/summary.md) e `brp_study/results/results_long.csv`.

### 9.1 Resumo geral

| Método | Soluções verificadas | Gap médio (%) | Gap máximo (%) | Igual a Z\* | Melhor que Min-Max | Pior que Min-Max | Tempo médio (s) | Tempo máximo (s) | Timeouts |
|---|---|---|---|---|---|---|---|---|---|
| Min-Max | 170 | 4,59 | 31,03 | 101 | 0 | 0 | 0,000 | 0,00 | 0 |
| A* | 144 | 0,00 | 0,00 | 143 | 42 | 0 | 5,196 | 30,17 | 26 |
| GLAH-R (D=3) | 170 | 0,30 | 9,09 | 156 | 67 | 0 | 0,149 | 2,91 | 0 |
| GLAH-R (D=4) | 170 | 0,29 | 6,67 | 157 | 66 | 0 | 0,409 | 8,64 | 0 |

**Como ler a tabela.** O A* só tem solução para as instâncias em que provou o ótimo (144 de
170). Por isso a média de reposicionamentos do A* (12,65) é calculada só sobre essas 144 e não
é comparável às outras linhas. Para as 26 instâncias com timeout, o A* não devolveu solução, e
o valor de referência Z\* vem da melhor solução entre os outros métodos. Nas instâncias do
N49, o Z\* é o melhor valor conhecido, sem prova de ótimo.

### 9.2 Principais observações

- **GLAH-R nunca fica pior que o Min-Max.** Em todas as 170 instâncias, o GLAH-R (D=3 e D=4)
  devolve valor igual ou melhor. O gap médio cai de 4,59% (Min-Max) para cerca de 0,3%.
- **Nas instâncias pequenas (conjunto A), o GLAH-R encontra o ótimo.** Em todas as 50 instâncias,
  os dois valores de D chegam ao ótimo provado pelo A*.
- **Nas instâncias maiores, o GLAH-R fica quase sempre no ótimo.** Entre as 144 instâncias
  com ótimo provado, o D=3 não é ótimo em 10 casos, e o D=4 em 11. Todos os casos estão nos
  arquivos W7 (H de 5 a 7), com diferença de 1 ou 2 reposicionamentos. O pior gap do GLAH-R é
  9,09% (`brp_W7_H5_N31`, instância 6, D=3).
- **Aumentar D não melhorou a qualidade de forma clara nesta execução.** D=4 ficou praticamente
  empatado com D=3: gap médio de 0,29% contra 0,30%, e 157 instâncias iguais ao Z\* contra 156.
  Nas 144 instâncias com ótimo provado, porém, o D=4 ficou acima do ótimo em 11 casos e o D=3
  em 10. O custo de tempo cresce cerca de 2,7 vezes (0,409 s contra 0,149 s em média). Uma
  busca mais profunda não garante uma solução melhor, porque a regra de avaliação no nível
  inferior pode levar a outro caminho.
- **O A* é exato, mas perde o orçamento nas instâncias maiores.** Ele provou o ótimo em todas
  as 50 instâncias do conjunto A e em 94 das 120 do conjunto B. Os 26 timeouts estão nos
  arquivos W7 com N ≥ 32 e H de 6 a 8. Nesses casos, o limite inferior devolvido ficou entre 26 e 51.
- **Min-Max é rápido, mas bem mais distante do ótimo.** Ele fica acima do Z\* em 69 das 170
  instâncias e chega a 31% acima no pior caso.

### 9.3 Resultado por arquivo

Gap médio (%) em relação ao Z\* de cada instância, e número de instâncias em que o A\* provou o ótimo.

| Arquivo | W | H | N | Min-Max | GLAH-R (D=3) | GLAH-R (D=4) | A\* ótimo provado |
|---|---|---|---|---|---|---|---|
| `brp_W3_H4_N8` | 3 | 4 | 8 | 2,22 | 0,00 | 0,00 | 10/10 |
| `brp_W4_H4_N10` | 4 | 4 | 10 | 0,00 | 0,00 | 0,00 | 10/10 |
| `brp_W4_H5_N12` | 4 | 5 | 12 | 3,50 | 0,00 | 0,00 | 10/10 |
| `brp_W5_H4_N15` | 5 | 4 | 15 | 4,36 | 0,00 | 0,00 | 10/10 |
| `brp_W5_H5_N18` | 5 | 5 | 18 | 6,91 | 0,00 | 0,00 | 10/10 |
| `brp_W7_H5_N16` | 7 | 5 | 16 | 0,00 | 0,00 | 0,00 | 10/10 |
| `brp_W7_H5_N23` | 7 | 5 | 23 | 0,71 | 0,00 | 0,00 | 10/10 |
| `brp_W7_H5_N31` | 7 | 5 | 31 | 9,33 | 1,83 | 1,37 | 10/10 |
| `brp_W7_H6_N18` | 7 | 6 | 18 | 0,00 | 0,00 | 0,00 | 10/10 |
| `brp_W7_H6_N28` | 7 | 6 | 28 | 3,73 | 0,50 | 0,50 | 10/10 |
| `brp_W7_H6_N37` | 7 | 6 | 37 | 6,02 | 1,04 | 1,71 | 8/10 |
| `brp_W7_H7_N22` | 7 | 7 | 22 | 1,00 | 0,00 | 0,00 | 10/10 |
| `brp_W7_H7_N32` | 7 | 7 | 32 | 5,78 | 0,45 | 0,45 | 9/10 |
| `brp_W7_H7_N43` | 7 | 7 | 43 | 7,71 | 0,52 | 0,28 | 2/10 |
| `brp_W7_H8_N24` | 7 | 8 | 24 | 2,10 | 0,00 | 0,00 | 10/10 |
| `brp_W7_H8_N37` | 7 | 8 | 37 | 11,75 | 0,40 | 0,40 | 5/10 |
| `brp_W7_H8_N49` | 7 | 8 | 49 | 12,70 | 0,41 | 0,19 | 0/10 |

Tempo médio do A\* nos arquivos grandes: 24,6 s (N43), 17,9 s (H8_N37) e 30,0 s (N49, sempre
no limite). Os métodos do GLAH-R e o Min-Max ficam abaixo de 4 s nesses mesmos arquivos.

### 9.4 Limitações desta execução

- **Uma única máquina e um único orçamento.** Os tempos são de relógio, e um orçamento
  diferente muda quantas instâncias o A* consegue provar.
- **Referência fraca no N49.** Sem ótimo provado, o gap é medido contra o melhor valor
  encontrado, que pode estar acima do ótimo real.
- **Sem variação entre execuções.** Todos os métodos são determinísticos, então cada um foi
  executado uma vez por instância.

## 10. Limitações e observações

- **Variante do artigo.** O artigo resolve o problema irrestrito com prioridades agrupadas. O
  GLAH-R é uma adaptação para o problema restrito e com prioridades únicas, e a tabela 6.3 lista
  cada mudança. Não é uma reprodução dos números do artigo.
- **Tempo e hardware.** Os tempos dependem da máquina. O orçamento por instância é o mesmo para
  todos os métodos; execuções que atingem o limite aparecem como `timeout`. Os tempos são de
  relógio (tempo decorrido).
- **Limite inferior no timeout.** Para o A*, o limite é o menor `f` da fila aberta quando o
  orçamento se esgota. É válido, mas pode ser frouxo.
- **Determinismo.** Todos os métodos são determinísticos. Os resultados são reproduzíveis bit a
  bit no mesmo código, exceto pelas colunas de tempo.
- **Instâncias.** Os dados são usados como estão (o `LEIAME.md` pede isso para que todos os
  resultados sejam comparáveis).

---

## 11. Variante irrestrita (`brp_unrestricted.py`)

Esta seção implementa o problema que o artigo de Jin, Zhu & Lim (2015) de fato resolve: o
**U-CRP**, a variante irrestrita. Os resultados ficam separados dos das seções 1 a 10, porque o
`LEIAME.md` define a comparação entre equipes na variante restrita.

### 11.1 Problema

As regras são as da seção 1, com uma diferença: **qualquer contêiner que esteja no topo de
qualquer pilha pode ser relocado** para outra pilha com altura menor que H. Isso inclui
relocações antecipadas de contêineres que não estão acima do alvo. Toda solução restrita também
é uma solução irrestrita, então **Z\*_U ≤ Z\*_R** em toda instância.

O verificador é o mesmo da seção 3, chamado com `verify(inst, moves, restricted=False)`. Nesse
modo, ele deixa de exigir que a origem contenha o alvo e mantém as demais regras: origem válida
e não vazia, destino diferente da origem e com espaço, e pátio vazio no fim. O padrão continua
sendo `restricted=True`, de modo que o código e os resultados restritos não mudam.

### 11.2 Limite inferior

Usa o limite completo da seção 4.1.1 do artigo: **número de contêineres mal posicionados +
k_non-BG**. O termo binário `k_non-BG` vale 1 quando não há pilha vazia e
`min gtop(s) > max gmin(s)`. Nessa situação, todo topo está mal posicionado e qualquer destino já
tem um número menor, então o primeiro contêiner movido continua mal posicionado e precisa de mais
um movimento.

### 11.3 A\*-U (exato)

- **Sucessores:** todos os pares `(origem, destino)` legais, até W·(W−1) por estado.
- **Função de avaliação:** `f = g + LB`, com o limite da seção 11.2.
- **Reduções:** todas preservam a otimalidade e foram conferidas contra uma busca em largura
  sem reduções (`solve_bfs_u`).
  - **Simetria:** pátios que são permutações das mesmas pilhas compartilham uma única entrada
    na tabela de estados fechados, e só a primeira pilha vazia é usada como destino.
  - **Dominância:** o contêiner movido por último não é movido de novo, a menos que tenha
    havido uma retirada no meio. A sequência `c: s1→s2, c: s2→s3` nunca é mais curta que
    `c: s1→s3`.
  - **Incumbente:** a melhor solução heurística (Min-Max ou GLAH-U) serve como limite superior
    UB, e todo nó com `f ≥ UB` é descartado. Se a fila aberta esvaziar, ou se o menor `f` chegar
    a UB, a incumbente está provada ótima.
- **Orçamento:** limite de tempo e um limite de 3 milhões de nós como proteção de memória. No
  timeout, o A\*-U não reporta solução; a coluna `lower_bound` guarda o menor `f` da fila
  aberta. O tempo das heurísticas que fornecem a incumbente não é somado ao do A\*-U.

### 11.4 GLAH-U: o método do artigo, sem adaptações

O GLAH-U implementa os três níveis do GLAH como publicados. As diferenças em relação ao GLAH-R
(tabela 6.3) são exatamente as partes que a variante restrita proibia.

| Componente | GLAH-R (seção 6) | GLAH-U (aqui) |
|---|---|---|
| Categorias de relocação no look-ahead | FT-BG, FT-BB | **FT-BG, NF-BG, FT-BB, NF-BB, GG, GB** |
| Ramificação | destinos do bloqueador | **qualquer relocação `(origem, destino)`** |
| Caso 2 do nível inferior (abrir espaço movendo um topo bem posicionado para uma pilha assistente) | removido | **sim** |
| Aproveitamento de folga (*gap utilization*, Algoritmo 4) | removido | **sim**, antes de cada relocação X→Good dos casos 1 e 2 |
| Limite inferior | só a contagem | **contagem + k_non-BG** |
| Custo da folha | `d + |avaliação|` | comprimento da sequência condensada a partir da raiz (seção 4.3.5) |
| Correção de sincronização (outer-sync) | destino do nível inferior | **primeira relocação** do nível inferior, que pode ser de folga ou o GG do caso 2 |

**Parâmetros do artigo** (seção 5): `nFT-BG = nNF-BG = 5`, `nFT-BB = nNF-BB = 3`,
`nGG = nGB = 1` e `D ∈ {3, 4}`.

**Ordenação das categorias** (seção 4.2.2):

| Categoria | Critério |
|---|---|
| X-BG | `gmin(s2) − c`, crescente |
| X-BB | `c − gmin(s2)`, crescente |
| GG e GB | `f(s1) − gmin(s2)`, decrescente |

Empates são decididos pelo menor `(s1, s2)`. O texto do artigo dá o mesmo critério para GG e GB,
e ele foi usado como está.

**Definições** (seção 2 do artigo): `gmin(s)` é o menor número da pilha `s` (`N+1` se vazia), e
`f(s)` é o menor número da pilha sem contar o topo (`N+1` se a pilha tiver menos de dois
contêineres). Um topo está bem posicionado quando `gtop(s) < f(s)`. A pilha `s` suporta `c` quando
`h(s) < H` e `c < gmin(s)`. Com prioridades únicas, o alvo urgente da seção 4.3.1 é sempre o
menor número.

**Opção fora do artigo:** `solve_glah_u(..., seed=moves)` aceita uma solução inicial extra, por
exemplo a do GLAH-R. Ela fica desligada nos experimentos.

**Desempenho:** a avaliação do nível inferior fica em cache por estado, e a retirada automática
usa a ordem de retirada conhecida. Mesmo assim, o GLAH-U visita muito mais nós que o GLAH-R, até
cerca de 19 filhos por nó.

### 11.5 Testes (`test_brp_unrestricted.py`)

- **Verificador:** regras da variante irrestrita, e a variante restrita continua sendo o padrão.
- **Limite inferior:** o termo `k_non-BG`, e o limite nunca passa do ótimo.
- **A\*-U contra BFS:** resultados iguais, com e sem incumbente, nas instâncias pequenas.
- **Z\*_U ≤ Z\*_R** nos arquivos W3 e W4, com pelo menos um caso estritamente melhor.
- **Nível inferior:** caso 1 com aproveitamento de folga e caso 2 (GG seguido de BG), em pátios
  construídos para isso.
- **Classificação:** as seis categorias de relocação e a lista de candidatos.
- **GLAH-U:** soluções verificadas, entre o ótimo e a avaliação inicial.
- **Condensação.**

Uma validação cruzada extra conferiu o A\*-U contra o BFS nos arquivos `W4_H4_N10` e
`W4_H5_N12` completos: 0 divergências. As figuras 4 a 7 e 9 a 10 do artigo são imagens no PDF e
não puderam ser transcritas automaticamente como testes.

### 11.6 Resultados

Execução completa: 170 instâncias, 4 métodos, orçamento de 30 s por instância e método, na mesma
máquina da seção 9. Resultado: **680 linhas, todas as soluções verificadas** com as regras
irrestritas. Tempo total: cerca de 34 minutos. Os valores completos estão em
[`brp_study/results/summary_unrestricted.md`](brp_study/results/summary_unrestricted.md) e `brp_study/results/unrestricted_long.csv`.

| Método | Soluções verificadas | Gap médio (%) | Gap máximo (%) | Igual a Z\*_U | Melhor que Min-Max | Tempo médio (s) | Tempo máximo (s) | Timeouts |
|---|---|---|---|---|---|---|---|---|
| Min-Max | 170 | 11,39 | 50,00 | 72 | 0 | 0,000 | 0,00 | 0 |
| A\*-U | 129 | 0,00 | 0,00 | 128 | 57 | 7,926 | 30,15 | 41 |
| GLAH-U (D=3) | 170 | 0,38 | 11,11 | 156 | 97 | 0,649 | 11,67 | 0 |
| GLAH-U (D=4) | 170 | 0,25 | 11,11 | 160 | 97 | 3,269 | 30,00 | 9 |

O gap é medido contra Z\*_U, que é o ótimo do A\*-U quando provado e, caso contrário, a melhor
solução irrestrita encontrada. O Min-Max é o mesmo da seção 4: as soluções dele são válidas nas
duas variantes, mas o gap dele cresce aqui porque a referência Z\*_U é menor.

**Ganho do irrestrito sobre o restrito**, comparando os valores de referência por instância:

| Conjunto | Z\*_R médio | Z\*_U médio | Ganho médio | Ganho (%) | Instâncias com Z\*_U < Z\*_R |
|---|---|---|---|---|---|
| Todas (170) | 16,86 | 15,62 | 1,25 | 7,4 | 88 |
| Ótimos provados nas duas variantes (127) | — | — | 0,61 | — | 48 |

Por arquivo, o ganho vai de 0% (`W7_H5_N16`) a cerca de 10–11% (`W7_H5_N31`, `W7_H7_N32`), e
cresce com a ocupação do pátio. A tabela completa está em [`brp_study/results/summary_unrestricted.md`](brp_study/results/summary_unrestricted.md).

**Principais observações:**

- **Relocações antecipadas reduzem o número de movimentos.** Em nenhuma instância Z\*_U ficou
  acima de Z\*_R. Nas 127 instâncias com ótimo provado nas duas variantes, o irrestrito é
  estritamente melhor em 48, com ganho de até 4 movimentos.
- **O GLAH-U nunca fica pior que o GLAH-R com a mesma profundidade.** É estritamente melhor em
  89 (D=3) e 90 (D=4) das 170 instâncias, sem usar a solução restrita como semente.
- **O GLAH-U fica perto do ótimo.** Nas 129 instâncias com ótimo provado pelo A\*-U, o D=3 fica
  acima do ótimo em 6 e o D=4 em 4, sempre por 1 ou 2 movimentos, nos arquivos `W7_H5_N31`,
  `W7_H6_N28` e `W7_H7_N32`. O pior gap é 11,1% (`W7_H7_N32`, instância 6, 18 contra 20).
- **D=4 melhora pouco e custa bem mais.** Comparado ao D=3, o D=4 é melhor em 10 instâncias e
  pior em 5, e fica cerca de 5 vezes mais lento. No `W7_H8_N49`, o D=4 esgota os 30 s em 8 das
  10 instâncias e fica pior que o D=3 na média (43,9 contra 43,5), porque devolve a melhor
  solução encontrada até o limite.
- **O A\*-U é bem mais difícil que o A\* restrito.** Ele provou o ótimo em 129 instâncias, contra
  144 do A\* restrito, e todos os 41 timeouts estão em arquivos W7 (N ≥ 24, H ≥ 5). Nos arquivos
  `W7_H7_N43` e `W7_H8_N49`, nenhuma instância foi provada, e os limites inferiores devolvidos
  ficaram entre 15 e 40, bem abaixo das melhores soluções. Nessas instâncias, Z\*_U é só o melhor
  valor conhecido.

### 11.7 Limitações

- **Gap fraco nos arquivos grandes.** Sem ótimo provado, o gap e o ganho são medidos contra o
  melhor valor conhecido. Nesses arquivos, o ganho real do irrestrito pode ser maior que o
  reportado.
- **Uso da incumbente.** O A\*-U recebe a incumbente das heurísticas. O tempo do A\*-U não inclui
  o tempo dessas heurísticas.
- **Tempo em Python.** O artigo usa Java. Em Python, o D=4 não cabe no orçamento de 30 s nas
  maiores instâncias, e os tempos não são comparáveis aos da tabela do artigo.
- **Instâncias diferentes das do artigo.** As instâncias não são os conjuntos CVS, BF ou ZHU do
  artigo, então os números não reproduzem as tabelas 1 a 4. O que se reproduz é o método.
