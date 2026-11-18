# Achados dos experimentos: BRP restrito e irrestrito

Este documento reúne os resultados das duas variantes do BRP e o que eles mostram. Ele foi
pensado para servir de base à apresentação. Os detalhes de implementação estão no
[README](../README.md): seções 1 a 10 para a variante restrita e seção 11 para a irrestrita. Todos
os números abaixo vêm de [`results/results_long.csv`](results/results_long.csv) e
[`results/unrestricted_long.csv`](results/unrestricted_long.csv).

---

## 1. Resumo em números

| | Variante restrita | Variante irrestrita |
|---|---|---|
| Instâncias | 170 (17 arquivos × 10) | as mesmas 170 |
| Soluções verificadas | 680 de 680 | 680 de 680 |
| Valor de referência médio (Z\*) | 16,86 | **15,62** (−7,4%) |
| Ótimos provados pelo A\* | 144 de 170 | 129 de 170 |
| Gap médio do Min-Max | 4,59% | 11,39% |
| Gap médio do GLAH (D=3 / D=4) | 0,30% / 0,29% | 0,38% / 0,25% |
| Tempo médio do GLAH (D=3 / D=4) | 0,15 s / 0,41 s | 0,65 s / 3,27 s |

**Mensagens principais:**

1. O **GLAH** (Jin, Zhu & Lim, 2015) fica **quase sempre no ótimo** nas duas variantes, com gap
   médio abaixo de 0,4%, e nunca é pior que o Min-Max.
2. **Permitir relocações antecipadas** (variante irrestrita) reduz os reposicionamentos em
   **7,4%** em média. O ganho chega a cerca de 11% nos pátios mais cheios.
3. A versão irrestrita é **mais difícil de resolver de forma exata**, porque o espaço de busca é
   bem maior: o A\* prova menos ótimos (129 contra 144).
4. **D=4 quase não melhora sobre D=3** e custa de 3 a 5 vezes mais tempo.

---

## 2. Contexto (para os primeiros slides)

### 2.1 O problema

- **Pátio:** W pilhas com altura máxima H, e N contêineres numerados pela ordem de retirada
  (o 1 sai primeiro).
- **Retirada:** um contêiner só sai quando está no topo da sua pilha. A retirada é automática e
  não custa nada.
- **Custo:** cada relocação de um contêiner de uma pilha para outra custa 1 *reshuffle*. O
  objetivo é minimizar esse número.

### 2.2 As duas variantes

| | Restrita (`LEIAME.md`) | Irrestrita (artigo) |
|---|---|---|
| O que pode ser relocado | só os contêineres **acima do alvo atual** | **qualquer topo** de qualquer pilha |
| Relocações antecipadas | não | sim |
| Relação entre os ótimos | Z\*_R | Z\*_U ≤ Z\*_R (toda solução restrita vale no irrestrito) |

### 2.3 Os métodos

| Método | Tipo | Variante |
|---|---|---|
| Min-Max (Caserta, Voß & Sniedovich, 2012) | heurística construtiva | as duas (as soluções dele valem nas duas) |
| A\* | exato, `h` = mal posicionados | restrita |
| A\*-U | exato, `h` = mal posicionados + `k_non-BG`, com redução de simetria e poda pela melhor solução heurística | irrestrita |
| GLAH-R (D=3, D=4) | look-ahead do artigo adaptado à variante restrita | restrita |
| GLAH-U (D=3, D=4) | look-ahead do artigo **como publicado** | irrestrita |

### 2.4 Instâncias e protocolo

- **Conjunto A:** 5 arquivos pequenos, de W3_H4_N8 a W5_H5_N18.
- **Conjunto B:** 12 arquivos com W = 7, H de 5 a 8 e ocupação de cerca de 50%, 75% e 100% da
  capacidade viável.
- **Orçamento:** 30 s por instância e por método. Todos os métodos são determinísticos, então
  cada um roda uma vez por instância.
- **Verificação:** toda solução é verificada por um simulador independente antes de entrar nas
  tabelas.
- **Gap:** `(Z − Z*) / Z*`. Z\* é o ótimo do A\* quando provado e, caso contrário, a melhor
  solução conhecida.

---

## 3. Variante restrita

| Método | Gap médio (%) | Gap máx. (%) | Igual a Z\* | Melhor que Min-Max | Tempo médio (s) | Timeouts |
|---|---|---|---|---|---|---|
| Min-Max | 4,59 | 31,03 | 101 | — | 0,000 | 0 |
| A\* | 0,00 | 0,00 | 143\* | 42 | 5,196 | 26 |
| GLAH-R (D=3) | 0,30 | 9,09 | 156 | 67 | 0,149 | 0 |
| GLAH-R (D=4) | 0,29 | 6,67 | 157 | 66 | 0,409 | 0 |

\* O A\* só tem solução nas 144 instâncias em que provou o ótimo. Ele aparece com 143 porque o
"Igual a Z\*" conta gap 0, e numa instância Z\* = 0, o que deixa o gap sem valor.

**Achados:**

- **O GLAH-R nunca é pior que o Min-Max** e é estritamente melhor em 67 instâncias (D=3).
- **No conjunto A, o GLAH-R acerta o ótimo nas 50 instâncias.**
- **No conjunto B, os erros são raros e pequenos:** nas 144 instâncias com ótimo provado, o
  GLAH-R fica fora do ótimo em 10 (D=3) ou 11 (D=4), sempre por 1 ou 2 movimentos.
- **O Min-Max piora com a ocupação:** o gap médio sobe para 12,7% no W7_H8_N49.
- **O A\* esgota o orçamento em 26 instâncias,** todas em arquivos W7 com N ≥ 32.

**Por que o GLAH-R ganha do Min-Max:** sem as partes do artigo que a variante restrita proíbe, o
nível inferior do GLAH-R é praticamente o próprio Min-Max. O ganho vem do look-ahead e da
condensação de movimentos.

---

## 4. Variante irrestrita

| Método | Gap médio (%) | Gap máx. (%) | Igual a Z\*_U | Melhor que Min-Max | Tempo médio (s) | Timeouts |
|---|---|---|---|---|---|---|
| Min-Max | 11,39 | 50,00 | 72 | — | 0,000 | 0 |
| A\*-U | 0,00 | 0,00 | 128\* | 57 | 7,926 | 41 |
| GLAH-U (D=3) | 0,38 | 11,11 | 156 | 97 | 0,649 | 0 |
| GLAH-U (D=4) | 0,25 | 11,11 | 160 | 97 | 3,269 | 9 |

\* O A\*-U só tem solução nas 129 instâncias em que provou o ótimo.

**Achados:**

- **O GLAH-U fica quase sempre no ótimo.** Nas 129 instâncias com ótimo provado, fica acima dele
  em 6 (D=3) ou 4 (D=4), por 1 ou 2 movimentos. Todos esses casos estão em `W7_H5_N31`,
  `W7_H6_N28` e `W7_H7_N32`. O pior caso é `W7_H7_N32` id 6: 20 movimentos contra 18 (11,1%).
- **O GLAH-U nunca é pior que o GLAH-R com a mesma profundidade.** É estritamente melhor em 89
  (D=3) e 90 (D=4) das 170 instâncias, mesmo sem usar a solução restrita como ponto de partida.
- **O Min-Max fica bem mais distante aqui** (11,4% contra 4,6%), porque ele nunca faz relocações
  antecipadas, e a referência Z\*_U é menor que Z\*_R.
- **O A\*-U sofre com o espaço de busca maior.** São até W·(W−1) = 42 movimentos por estado, contra
  no máximo 6 no restrito. Ele provou o ótimo em 129 instâncias. Nos arquivos `W7_H7_N43` e
  `W7_H8_N49`, não provou nenhuma, e os limites inferiores ficaram entre 15 e 40, frouxos.
- **D=4 é melhor que D=3 em 10 instâncias e pior em 5,** e é cerca de 5 vezes mais lento. No
  W7_H8_N49, o D=4 esgota os 30 s em 8 de 10 instâncias e termina, em média, pior que o D=3
  (43,9 contra 43,5).

---

## 5. Restrito contra irrestrito: quanto valem as relocações antecipadas

### 5.1 Ganho geral

| Recorte | Z\*_R médio | Z\*_U médio | Ganho |
|---|---|---|---|
| Todas as 170 instâncias | 16,86 | 15,62 | **7,4%** (1,25 movimento por instância) |
| Conjunto A (50) | 6,50 | 6,14 | 5,5% |
| Conjunto B (120) | 21,18 | 19,57 | 7,6% |
| Ótimos provados nas duas variantes (127) | — | — | 0,61 movimento por instância; 48 estritamente melhores; até 4 a menos |

- **Z\*_U < Z\*_R em 88 das 170 instâncias,** e **Z\*_U nunca ficou acima de Z\*_R,** como a
  teoria garante.
- **O maior ganho provado** é de 4 movimentos, em `W7_H5_N31` id 10.

### 5.2 O ganho cresce com a ocupação do pátio (conjunto B)

| Ocupação | Instâncias | Z\*_R médio | Z\*_U médio | Ganho |
|---|---|---|---|---|
| ~50% | 40 | 9,72 | 9,47 | 2,6% |
| ~75% | 40 | 19,43 | 17,75 | 8,6% |
| ~100% | 40 | 34,40 | 31,48 | 8,5% |

**Interpretação:** com o pátio vazio, quase sempre existe uma pilha que "aceita" o bloqueador sem
criar um novo bloqueio, e antecipar movimentos ajuda pouco. Com o pátio cheio, preparar pilhas com
antecedência evita relocações em cadeia.

**Ressalva:** nos arquivos de 100%, Z\*_U muitas vezes é só o melhor valor conhecido, sem prova
de ótimo. O ganho real pode ser maior.

### 5.3 Exemplo pequeno para slide (`brp_W3_H4_N8`, instância 8, H = 4)

```
Configuração inicial (base embaixo)

        3
        1       7
        6       5
        4   8   2
       --  --  --
       P1  P2  P3
```

O alvo é o 1, embaixo do 3 na pilha P1. Os dois ótimos foram provados pelo A\* e pelo A\*-U.

**Restrito: ótimo de 5 movimentos.** Só pode mover o que está acima do alvo atual.

1. `P1→P3`: o 3 vai para cima do 7. A P3 fica cheia, e o 1 sai.
2. `P3→P1`: o 3 volta para a P1, porque agora bloqueia o 2.
3. `P3→P2`: o 7 vai para cima do 8.
4. `P3→P2`: o 5 vai para cima do 7. Saem o 2 e o 3.
5. `P1→P3`: o 6 vai para a P3, que está vazia. Saem o 4, 5, 6, 7 e 8.

**Irrestrito: ótimo de 4 movimentos.** Começa com duas relocações antecipadas.

1. `P3→P2`: o 7 vai para cima do 8. É **antecipado**: o 7 não bloqueia o alvo 1.
2. `P3→P2`: o 5 vai para cima do 7. Também **antecipado**.
3. `P1→P2`: o 3 vai para cima do 5. Saem o 1, o 2 (que ficou sozinho na P3) e o 3.
4. `P1→P3`: o 6 vai para a P3, que está vazia. Saem o 4, 5, 6, 7 e 8.

**A ideia:** no restrito, o 3 precisa ser movido duas vezes, porque o único lugar livre para ele
no começo é em cima do 7, onde ele passa a bloquear o 2. No irrestrito, esvaziar a P3 antes cria
um destino bom para o 3 e para o 6, e economiza um movimento.

---

## 6. Tempo de execução

Tempo médio por instância, em segundos (máximo entre parênteses):

| Método | Conjunto A | Conjunto B |
|---|---|---|
| Min-Max | 0,000 | 0,000 |
| A\* (restrito) | 0,001 (0,02) | 7,36 (30,2) |
| A\*-U | 0,011 (0,35) | 11,23 (30,2) |
| GLAH-R D=3 | 0,002 (0,03) | 0,21 (2,9) |
| GLAH-R D=4 | 0,002 (0,06) | 0,58 (8,6) |
| GLAH-U D=3 | 0,007 (0,17) | 0,92 (11,7) |
| GLAH-U D=4 | 0,018 (0,62) | 4,62 (30,0) |

- **O GLAH-U é de 4 a 8 vezes mais lento que o GLAH-R.** Na árvore, cada nó tem até cerca de 19
  filhos, contra até 9 no GLAH-R.
- **Implementação em Python.** O artigo usa Java. Os tempos servem para comparar os métodos
  entre si, não com as tabelas do artigo.
- **O A\*-U recebe a solução das heurísticas como limite superior.** O tempo dessas heurísticas
  não entra no tempo do A\*-U.

---

## 7. Tabela completa por arquivo

As colunas de método mostram o gap médio (%) em relação ao Z\* da própria variante. "Prova" é o
número de instâncias em que o exato provou o ótimo.

| Arquivo | W | H | N | Z\*_R | Z\*_U | Ganho (%) | A\* prova (R) | A\*-U prova (U) | Min-Max (R) | GLAH-R D=3 | GLAH-R D=4 | Min-Max (U) | GLAH-U D=3 | GLAH-U D=4 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `W3_H4_N8` | 3 | 4 | 8 | 4,10 | 4,00 | 2,4 | 10/10 | 10/10 | 2,22 | 0,00 | 0,00 | 5,56 | 0,00 | 0,00 |
| `W4_H4_N10` | 4 | 4 | 10 | 4,40 | 4,10 | 6,8 | 10/10 | 10/10 | 0,00 | 0,00 | 0,00 | 5,60 | 0,00 | 0,00 |
| `W4_H5_N12` | 4 | 5 | 12 | 7,10 | 6,90 | 2,8 | 10/10 | 10/10 | 3,50 | 0,00 | 0,00 | 6,25 | 0,00 | 0,00 |
| `W5_H4_N15` | 5 | 4 | 15 | 7,10 | 6,80 | 4,2 | 10/10 | 10/10 | 4,36 | 0,00 | 0,00 | 8,93 | 0,00 | 0,00 |
| `W5_H5_N18` | 5 | 5 | 18 | 9,80 | 8,90 | 9,2 | 10/10 | 10/10 | 6,91 | 0,00 | 0,00 | 18,69 | 0,00 | 0,00 |
| `W7_H5_N16` | 7 | 5 | 16 | 7,00 | 7,00 | 0,0 | 10/10 | 10/10 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 |
| `W7_H5_N23` | 7 | 5 | 23 | 11,60 | 11,10 | 4,3 | 10/10 | 10/10 | 0,71 | 0,00 | 0,00 | 5,29 | 0,00 | 0,00 |
| `W7_H5_N31` | 7 | 5 | 31 | 22,20 | 19,90 | 10,4 | 10/10 | 8/10 | 9,33 | 1,83 | 1,37 | 21,97 | 0,62 | 0,00 |
| `W7_H6_N18` | 7 | 6 | 18 | 7,80 | 7,70 | 1,3 | 10/10 | 10/10 | 0,00 | 0,00 | 0,00 | 1,11 | 0,00 | 0,00 |
| `W7_H6_N28` | 7 | 6 | 28 | 17,40 | 16,10 | 7,5 | 10/10 | 10/10 | 3,73 | 0,50 | 0,50 | 11,94 | 1,70 | 1,14 |
| `W7_H6_N37` | 7 | 6 | 37 | 29,60 | 27,60 | 6,8 | 8/10 | 1/10 | 6,02 | 1,04 | 1,71 | 13,55 | 0,38 | 0,38 |
| `W7_H7_N22` | 7 | 7 | 22 | 10,50 | 10,20 | 2,9 | 10/10 | 10/10 | 1,00 | 0,00 | 0,00 | 3,89 | 0,00 | 0,00 |
| `W7_H7_N32` | 7 | 7 | 32 | 20,90 | 18,60 | 11,0 | 9/10 | 7/10 | 5,78 | 0,45 | 0,45 | 18,78 | 2,02 | 1,57 |
| `W7_H7_N43` | 7 | 7 | 43 | 38,00 | 35,00 | 7,9 | 2/10 | 0/10 | 7,71 | 0,52 | 0,28 | 17,10 | 1,11 | 0,00 |
| `W7_H8_N24` | 7 | 8 | 24 | 13,60 | 13,00 | 4,4 | 10/10 | 9/10 | 2,10 | 0,00 | 0,00 | 7,00 | 0,00 | 0,00 |
| `W7_H8_N37` | 7 | 8 | 37 | 27,80 | 25,20 | 9,4 | 5/10 | 4/10 | 11,75 | 0,40 | 0,40 | 23,19 | 0,42 | 0,00 |
| `W7_H8_N49` | 7 | 8 | 49 | 47,80 | 43,40 | 9,2 | 0/10 | 0/10 | 12,70 | 0,41 | 0,19 | 24,25 | 0,22 | 1,09 |

**Como ler a tabela:** um gap de 0,00 no GLAH, num arquivo em que o exato não provou todas as
instâncias, significa "igual ao melhor valor conhecido", não "ótimo provado". Isso vale em
especial para N43 e N49.

---

## 8. Ressalvas para mencionar na apresentação

- **Referência fraca nos arquivos grandes.** Em N43 e N49, quase nada foi provado. Os gaps e o
  ganho são medidos contra o melhor valor conhecido.
- **Instâncias.** São as da disciplina, não os conjuntos CVS, BF ou ZHU do artigo. Os números não
  reproduzem as tabelas do artigo; o que se reproduz é o método.
- **Comparação com outras equipes.** A comparação oficial é na variante restrita. O irrestrito é
  um estudo adicional, autorizado pelo professor.
- **Execução.** Uma máquina, um orçamento de 30 s, Python 3.13 e tempos de relógio.
- **Testes.** O A\*-U foi validado contra uma busca em largura sem podas nas instâncias pequenas,
  com 0 divergências. As figuras do artigo são imagens no PDF e não viraram casos de teste.

---

## 9. Sugestão de roteiro para os slides

| # | Slide | Conteúdo | Fonte neste documento |
|---|---|---|---|
| 1 | Título | BRP: heurística gulosa com look-ahead nas variantes restrita e irrestrita | — |
| 2 | O problema | Pátio, retirada, custo; desenho de um pátio | 2.1 |
| 3 | Restrito × irrestrito | Tabela de regras; Z\*_U ≤ Z\*_R | 2.2 |
| 4 | Métodos | Min-Max, A\*, GLAH (três níveis: guloso, look-ahead, avaliação) | 2.3 e README §6/§11 |
| 5 | Adaptação do GLAH | O que sai no restrito (caso 2, aproveitamento de folga, NF/GG/GB) | README §6.3 e §11.4 |
| 6 | Protocolo | Conjuntos A e B, 30 s, verificação, definição de gap | 2.4 |
| 7 | Resultado restrito | Tabela geral; GLAH-R nunca pior que Min-Max, gap 0,3% | 3 |
| 8 | Resultado irrestrito | Tabela geral; GLAH-U ótimo em 123 a 125 de 129 | 4 |
| 9 | Exemplo ilustrado | Pátio pequeno, 5 contra 4 movimentos | 5.3 |
| 10 | Ganho do irrestrito | 7,4% geral; gráfico de barras do ganho por ocupação | 5.1 e 5.2 |
| 11 | Ganho por arquivo | Gráfico de Z\*_R e Z\*_U por arquivo | 7 (colunas Z\*_R e Z\*_U) |
| 12 | Tempo | Tabela de tempos; D=4 custa mais e quase não ajuda | 6 e 4 |
| 13 | Limitações | Referência fraca em N43/N49, Python, instâncias da disciplina | 8 |
| 14 | Conclusões | As quatro mensagens da seção 1 | 1 |

**Sugestões de gráficos:**

- **Barras agrupadas:** Z\*_R e Z\*_U por arquivo (17 grupos), a partir da seção 7.
- **Barras simples:** ganho (%) por ocupação, com 3 barras de 2,6%, 8,6% e 8,5%, a partir da
  seção 5.2.
- **Gap médio por método e variante**, mostrando que o Min-Max se afasta muito mais da
  referência no irrestrito.
- **Dispersão de tempo × gap** por método, mostrando que o GLAH fica no canto bom: rápido e
  perto do ótimo.

---

## 10. Como regenerar os dados

```powershell
python -m unittest discover -s brp_study -v                     # testes (35)
python brp_study\run_experiments.py                              # restrito (~17 min)
python brp_study\run_experiments.py --variant unrestricted       # irrestrito (~34 min)
```

- **Arquivos de saída:** `results/results_long.csv` e `results/unrestricted_long.csv` têm uma
  linha por instância e método, com a sequência de movimentos; os resumos ficam em
  `results/summary.md` e `results/summary_unrestricted.md`.
- **Ordem:** a variante irrestrita lê `results_long.csv` para calcular o ganho, então rode a
  restrita antes, ou use `--variant both`.
