# Instâncias do Block Relocation Problem (BRP)

Este pacote contém as instâncias que todas as equipes devem usar nos experimentos. Usem os arquivos **como estão**, sem gerar novas instâncias, para que os resultados de todas as equipes sejam comparáveis entre si e com as referências (Min-Max e A*).

## Variante do problema

Todas as instâncias seguem a variante vista em aula: BRP **restrito, único, determinístico e estático**.

- Os contêineres são numerados de 1 a N, e o número indica a **ordem de retirada**: o 1 sai primeiro, o N sai por último. Não há números repetidos.
- Um contêiner só pode ser retirado quando estiver no **topo** de sua pilha. A retirada não conta como movimento.
- **Restrito:** só podem ser relocados os contêineres que estão acima do alvo atual (o menor número ainda no pátio), na pilha do alvo. Cada relocação conta como **um *reshuffle***.
- Nenhuma pilha pode ultrapassar a altura máxima **H**, em nenhum momento.
- Todas as instâncias satisfazem W · H − N ≥ H − 1, o que garante que sempre existe um destino com espaço para relocar.

**Objetivo:** retirar todos os N contêineres com o menor número possível de *reshuffles*.

## Arquivos

Cada arquivo contém **10 instâncias** de uma mesma configuração. O nome indica os parâmetros: `brp_W{W}_H{H}_N{N}.json`, onde W é o número de pilhas, H a altura máxima e N o número de contêineres.

**Conjunto A** (pequeno; o ótimo é obtido pelo A* em poucos segundos):

| Arquivo | W | H | N |
|---|---|---|---|
| `brp_W3_H4_N8.json` | 3 | 4 | 8 |
| `brp_W4_H4_N10.json` | 4 | 4 | 10 |
| `brp_W4_H5_N12.json` | 4 | 5 | 12 |
| `brp_W5_H4_N15.json` | 5 | 4 | 15 |
| `brp_W5_H5_N18.json` | 5 | 5 | 18 |

**Conjunto B** (escala de uma baia real, W = 7, com ocupação de cerca de 50%, 75% e 100% da capacidade viável):

| H | Arquivos |
|---|---|
| 5 | `brp_W7_H5_N16.json`, `brp_W7_H5_N23.json`, `brp_W7_H5_N31.json` |
| 6 | `brp_W7_H6_N18.json`, `brp_W7_H6_N28.json`, `brp_W7_H6_N37.json` |
| 7 | `brp_W7_H7_N22.json`, `brp_W7_H7_N32.json`, `brp_W7_H7_N43.json` |
| 8 | `brp_W7_H8_N24.json`, `brp_W7_H8_N37.json`, `brp_W7_H8_N49.json` |

Nas instâncias maiores do conjunto B, o ótimo pode não ser conhecido. Nesses casos, a comparação é feita contra o melhor resultado conhecido e contra um limite inferior.

## Formato do arquivo JSON

O exemplo abaixo é ilustrativo: o cabeçalho segue o de `brp_W3_H4_N8.json`, mas a instância mostrada é a do exercício de fixação da aula, não uma das 10 do arquivo.

```json
{
  "metadata": {
    "W": 3,
    "H": 4,
    "N": 8,
    "total_instancias": 10,
    "semente": 2374
  },
  "instancias": [
    {
      "id": 1,
      "stacks": [
        [8, 7, 6],
        [2],
        [1, 3, 4, 5]
      ]
    }
  ]
}
```

**`metadata`**, comum a todas as instâncias do arquivo:

- `W`: número de pilhas.
- `H`: altura máxima de cada pilha.
- `N`: número de contêineres.
- `total_instancias`: quantidade de instâncias no arquivo.
- `semente`: semente usada na geração (apenas para registro).

**`instancias`**, uma lista em que cada elemento tem:

- `id`: identificador da instância dentro do arquivo (1 a 10). Use-o para reportar resultados.
- `stacks`: lista com exatamente **W** pilhas. Cada pilha é uma lista de contêineres **da base para o topo**: o primeiro elemento está no chão, o último está no topo. Uma pilha vazia é representada por `[]`.

As pilhas são numeradas pela sua posição na lista, **a partir de 1**: `stacks[0]` é a Pilha 1.

### Exemplo

A instância do exemplo acima corresponde a este pátio:

```
            5
    6       4
    7       3
    8   2   1
   --  --  --
   P1  P2  P3
```

O alvo inicial é o contêiner 1, na base da Pilha 3. Para retirá-lo, é preciso relocar 5, 4 e 3, nessa ordem.

## Leitura em Python

```python
import json

with open("brp_W7_H7_N43.json", encoding="utf-8") as f:
    dados = json.load(f)

W = dados["metadata"]["W"]
H = dados["metadata"]["H"]
N = dados["metadata"]["N"]

for inst in dados["instancias"]:
    pilhas = inst["stacks"]              # pilhas[i][-1] é o topo da Pilha i+1
    assert len(pilhas) == W
    assert sorted(c for p in pilhas for c in p) == list(range(1, N + 1))
    # ... resolver a instância ...
```

## Como reportar os resultados

Para cada instância, reportem pelo menos:

- `arquivo` e `id` da instância;
- número de *reshuffles* obtido;
- tempo de execução, em segundos;
- para métodos aleatórios, a média e o melhor valor entre as execuções, informando o número de execuções e as sementes usadas.

Recomendamos salvar também a **sequência de relocações**, como uma lista de pares `[origem, destino]` com as pilhas numeradas a partir de 1. As retiradas ficam implícitas: o alvo sai assim que chega ao topo. Por exemplo, `[[3, 2], [3, 2], [3, 1]]` significa mover o topo da Pilha 3 para a Pilha 2, depois de novo da 3 para a 2, e então da 3 para a 1.

Com a sequência, qualquer solução pode ser verificada: basta reexecutá-la e conferir que cada relocação parte da pilha do alvo, respeita a altura H e termina com o pátio vazio. Soluções que não passarem nessa verificação não serão consideradas na comparação.
