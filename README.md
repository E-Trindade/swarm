# Arquitetura
Cada nó implementa um ataque de slowloris
Os nós estão conectados por uma rede de enlace p2p. Cada nó mantém uma lista de vizinhos, que é usada para repassar comandos.

# Processos
## Ataque

## Comunicação entre nós

Cada mensagem enviada por nós é terminada com um campo de hash MD5, que é usado para verificar a integridade das mensagens recebidas. 
### Descoberta de nós e de comandos
Ao ser iniciado, cada nó contata um conjunto de nós iniciais (seeds), requisitando seus nós conhecidos e seu último comando recebido.

Requisição
```
<tamanho>|DSCVR|<hash>
```

Resposta
```
<tamanho>|DSCVR|<ultimo_comando>|<node_1>[,node2]|<hash>
```

### Ping
Periodicamente, cada nó verifica se seus vizinhos ainda estão disponíveis.

Requisição
```
<tamanho>|PING|[hash]
```

Resposta
```
<tamanho>|PONG|[hash]
```

### Propagação de comandos

Requisição
```
<tamanho>|CMD|<comando>|<host>|<porta>|<assinatura>|<hash>
```
Comando: SLOWLORIS
Assinatura: Assinatura RSA do payload.

O nó que recebe essa requisição verifica a assinatura usando a chave pública estabelecida em sua configuração. Caso a assinatura seja válida, o nó passa a executar a instrução recebida, repassando a mensagem para todos os seus vizinhos.

