# Arquitetura
Os nós estão conectados por uma rede de enlace p2p. Cada nó mantém uma lista de vizinhos, que é usada para repassar comandos.

# Processos
## Ataque
Cada nó implementa um ataque de slowloris, que consiste em um ataque a nível de aplicação, onde se tenta abrir um grande número de conexões TCP com um servidor HTTP, cada qual envia uma requisição HTTP e enviando seus cabeçalhos bem lentamente, até a conexão expire. Isso gera uma sobrecarga no servidor. Servidores Apache e Flask são especialmente suscetíveis a esse ataque, dados as suas técnicas de forking para atender requisições. 


## Comunicação entre nós

Todas as comunicações entre nós utilizam o protocolo UDP. O protocolo foi escolhido por sua simplicidade,

### Descoberta de nós e de comandos
Ao ser iniciado, cada nó contata um conjunto de nós iniciais (seeds), requisitando seus nós conhecidos e seu último comando recebido.

Requisição
```
<tamanho>|DSCVR
```

Resposta
```
<tamanho>|DSCVR|<ultimo_comando>|<node_1>[,node2]
```

### Ping
Periodicamente, cada nó verifica se seus vizinhos ainda estão disponíveis.

Requisição
```
<tamanho>|PING
```

Resposta
```
<tamanho>|PONG
```

### Propagação de comandos

Requisição
```
<tamanho>|CMD|<comando>|<host>|<porta>|<assinatura>
```
Comando: SLOWLORIS
Assinatura: Assinatura RSA do payload.

O nó que recebe essa requisição verifica a assinatura usando a chave pública estabelecida em sua configuração. Caso a assinatura seja válida, o nó passa a executar a instrução recebida, repassando a mensagem para todos os seus vizinhos.

