# Comparação de heurísticas para o Block Relocation Problem (BRP)

Implementação e comparação experimental de três métodos para o Block Relocation Problem (BRP):

1. **Min-Max** (Caserta, Voß & Sniedovich, 2012): heurística construtiva de referência.
2. **A\*** (exato): busca com garantia de otimalidade, usada como referência.
3. **GLAH-R**: heurística gulosa com *look-ahead* (busca em árvore limitada), adaptada da
   proposta de Jin, Zhu & Lim (2015) para a variante restrita do BRP.

Artigo de referência (arquivo em `artigos/`):

> B. Jin, W. Zhu, A. Lim. *Solving the container relocation problem by an improved greedy
> look-ahead heuristic.* European Journal of Operational Research 240 (2015) 837–847.
> `artigos/1-s2.0-S0377221714006043-main.pdf`

As instâncias estão em `data/instances/`. O arquivo `data/instances/LEIAME.md` define a
variante do problema, o formato dos arquivos e as regras de reporte.

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

| Arquivo | Conteúdo |
|---|---|
| `brp.py` | Modelo do problema, verificador independente, Min-Max, A*, GLAH-R, condensação e busca em largura (BFS) de referência |
| `run_experiments.py` | Executa a comparação em todos os arquivos de instâncias, verifica as soluções e grava os resultados |
| `test_brp.py` | Testes unitários: regras do verificador, A* contra BFS em casos pequenos, validade das soluções do GLAH-R, integridade dos dados |
| `README.md` | Este documento |
| `results/results_long.csv` | Uma linha por par (instância, método), com a sequência completa de relocações |
| `results/summary.md` | Tabelas gerais e por arquivo, geradas pelo script |
| `run_log.txt` | Saída local da execução completa (não versionada, ver `.gitignore`) |

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
estão em `results/summary.md` e `results/results_long.csv`.

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
