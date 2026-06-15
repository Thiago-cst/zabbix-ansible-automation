#!/usr/bin/env python3
"""
Script Ansible para criar ou garantir a existência de um host no Zabbix.
Este script foi desenhado para ser idempotente e comunicar com o Ansible.

Recebe:
- sys.argv[1]: Uma string JSON com os parâmetros do host.
- ZABBIX_SERVER_URL: Uma variável de ambiente com a URL da API.

Retorna:
- Uma string JSON formatada para o Ansible (com chaves 'changed' houve alteração, 'msg' retorno da ação ou 'failed' algo deu errado).
"""
import os
import sys
import json

# Mesmo que tenha alguns sublinhados vermelhos na importação da API, o código deve funcionar.
try:
    from pyzabbix import ZabbixAPI, ZabbixAPIException
    from requests.exceptions import ConnectionError
except ImportError:
    print(
        json.dumps(
            {
                "failed": True,
                "msg": "FALHA: A biblioteca 'pyzabbix' ou 'requests' não está instalada no ambiente Python.",
            }
        )
    )
    sys.exit(1)


def print_json_exit(success, changed, msg):
    """
    Função auxiliar para formatar e imprimir a saída JSON padrão do Ansible.
    Se success=False, assume-se que falhou.
    """
    if success:
        print(json.dumps({"changed": changed, "msg": msg}))
        sys.exit(0)
    else:
        print(json.dumps({"failed": True, "msg": msg}))
        sys.exit(1)


def main():
    # Função principal do script.

    # --- 1. VALIDAÇÃO DE ENTRADAS ---
    # Primeiro é verificado se possui a URL da API, que vem do ambiente
    zabbix_url = os.environ.get("ZABBIX_SERVER_URL")
    if not zabbix_url:
        print_json_exit(
            False,
            False,
            "FALHA: A variável de ambiente ZABBIX_SERVER_URL não foi definida.",
        )

    # Segundo, é verificado e carregado os parâmetros que vêm do Ansible
    try:
        params = json.loads(sys.argv[1])
    except IndexError:
        print_json_exit(
            False, False, "FALHA: Nenhum argumento JSON foi passado para o script."
        )
    except json.JSONDecodeError:
        print_json_exit(
            False,
            False,
            "FALHA: O argumento passado para o script não é um JSON válido.",
        )

    # Terceiro, então é validado que todos os parâmetros de que precisamos estão dentro do JSON
    required_params = [
        "user",
        "password",
        "host_name",
        "host_ip",
        "host_group",
        "template_name",
    ]
    host_params = {}
    for param in required_params:
        value = params.get(param)
        if not value:
            print_json_exit(
                False,
                False,
                f"FALHA: O parâmetro JSON obrigatório '{param}' está em falta.",
            )
        host_params[param] = value

    # --- 2. LÓGICA PRINCIPAL (TRY/EXCEPT) ---
    try:
        # Conexão e Login
        zapi = ZabbixAPI(zabbix_url)
        zapi.login(host_params["user"], host_params["password"])

        # 1. Verificar se o host já existe
        existing_host = zapi.host.get(filter={"host": [host_params["host_name"]]})
        if existing_host:
            print_json_exit(
                True,
                False,
                f"Host '{host_params['host_name']}' já existe no Zabbix.",
            )

        # 2. Obter o ID do grupo de hosts
        group = zapi.hostgroup.get(filter={"name": [host_params["host_group"]]})
        if not group:
            print_json_exit(
                False,
                False,
                f"Grupo de hosts '{host_params['host_group']}' não foi encontrado.",
            )
        group_id = group[0]["groupid"]

        # 3. Obter o ID do template
        template = zapi.template.get(filter={"host": [host_params["template_name"]]})
        if not template:
            print_json_exit(
                False,
                False,
                f"Template '{host_params['template_name']}' não foi encontrado.",
            )
        template_id = template[0]["templateid"]

        # 4. Criar o host
        zapi.host.create(
            host=host_params["host_name"],
            interfaces=[
                {
                    "type": 1,
                    "main": 1,
                    "useip": 1,
                    "ip": host_params["host_ip"],
                    "dns": "",
                    "port": "10050",
                }
            ],
            groups=[{"groupid": group_id}],
            templates=[{"templateid": template_id}],
        )

        print_json_exit(
            True,
            True,
            f"Host '{host_params['host_name']}' criado com sucesso no Zabbix.",
        )

    # --- 3. TRATAMENTO DE ERROS ESPECÍFICOS ---
    except ZabbixAPIException as e:
        print_json_exit(False, False, f"FALHA (API Zabbix): {e}")
    except ConnectionError as e:
        print_json_exit(
            False,
            False,
            f"FALHA (Rede): Não foi possível conectar a {zabbix_url}. Erro: {e}",
        )
    except Exception as e:
        # Erro genérico ou inesperado.
        print_json_exit(False, False, f"FALHA (Inesperada): {e}")


if __name__ == "__main__":
    main()
