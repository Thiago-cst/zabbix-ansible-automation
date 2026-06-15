# Automação de Registro de Hosts no Zabbix via IaC (Ansible + Python)

Este repositório contém o código-fonte e a arquitetura desenvolvidos como parte do Trabalho de Conclusão de Curso (TCC) em Ciência da Computação. O projeto propõe uma solução de automação baseada em *Infrastructure as Code* (IaC) para mitigar o gargalo operacional no provisionamento de novos servidores em infraestruturas corporativas.

## 🎯 Objetivo do Projeto

O objetivo principal é eliminar a intervenção humana no fluxo de *onboarding* de novos ativos no sistema de monitoramento Zabbix. A solução integra a orquestração do sistema operacional (via Ansible) com o registro lógico na plataforma de monitoramento (via API da Zabbix), reduzindo o tempo de cadastro de minutos para segundos e garantindo 100% de padronização.

## 🏗️ Arquitetura Híbrida

Durante o desenvolvimento, identificou-se que os módulos nativos de integração do Ansible com o Zabbix apresentavam falhas de compatibilidade em determinados ambientes (*'socket_path must be a value'*). Para contornar essa limitação e garantir maior resiliência, adotou-se uma **arquitetura híbrida**:

1. **Ansible (Orquestrador Agentless):** Responsável por conectar via SSH aos nós alvo, instalar o agente Zabbix, configurar os *hostnames* e garantir que os serviços estejam rodando.
2. **Python + pyzabbix (Integração API-Driven):** Um *script* customizado que é invocado pelo Ansible para se comunicar diretamente com os *endpoints* JSON-RPC do Zabbix Server, efetuando o registro lógico, alocação em grupos e vinculação de *templates*.

## 🛡️ O Script Python e o Princípio da Idempotência

O arquivo `zabbix_create_host.py` é o núcleo lógico da integração com a API. Para que a automação seja confiável em ambientes de produção, ela precisa ser **idempotente** (poder ser executada múltiplas vezes sem gerar duplicidades ou falhas).

O *script* garante a idempotência através do seguinte fluxo de decisão:
* Utiliza o método `host.get` para consultar ativamente o banco de dados do Zabbix e verificar se a máquina já está registrada.
* Se o *host* já existir, o script é encerrado com status de sucesso (`changed: false`), preservando o estado atual da rede.
* Caso não exista, o método `host.create` é acionado para injetar o IP, vincular os *templates* (CPU, Memória, Rede) e inserir o ativo nos grupos corretos (`changed: true`).

O *script* foi desenhado para cuspir (*stdout*) um JSON padronizado, permitindo que o interpretador do Ansible entenda perfeitamente o resultado da execução da API.

### Pré-requisitos do projeto
* Ansible instalado no *Control Node*.
* Python 3.x com as bibliotecas `requests` e `pyzabbix`.
* Acesso à rede (ou redirecionamento de portas/NAT) para os nós gerenciados.

👨‍💻 Autor
Thiago Costa Sousa Bacharelado em Ciência da Computação

Este projeto foi validado inicialmente em um ambiente de emulação avançada (EVE-NG) e posteriormente homologado com sucesso em máquinas virtuais de produção corporativa, respeitando as políticas de segmentação e segurança da informação.
