# Agente de monitoramento de licitações municipais

Este repositório contém um agente simples em Python para monitorar páginas de licitações em sites de prefeituras.

## O que ele faz

- Lê uma lista de fontes em `config.yaml`.
- Coleta os itens de cada página via CSS selectors.
- Filtra por palavras-chave de interesse.
- Evita alertas duplicados usando um arquivo de estado (`state.json`).
- Gera um relatório em Markdown com as novas licitações encontradas.

## Estrutura

- `licitacoes_agent.py`: script principal.
- `config.exemplo.yaml`: modelo de configuração para você copiar.
- `requirements.txt`: dependências Python.

## Como usar

1. Crie ambiente virtual e instale dependências:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Copie o arquivo de configuração:

```bash
cp config.exemplo.yaml config.yaml
```

3. Ajuste os seletores CSS e palavras-chave para as prefeituras da sua região.

4. Execute o agente:

```bash
python licitacoes_agent.py --config config.yaml --state state.json --output relatorio.md
```

## Execução automática (cron)

Exemplo para executar de hora em hora:

```bash
0 * * * * cd /workspace/gbm && /usr/bin/python3 licitacoes_agent.py --config config.yaml --state state.json --output relatorio.md >> agent.log 2>&1
```

## Próximos passos recomendados

- Integrar envio por e-mail/WhatsApp/Telegram.
- Criar uma fonte por prefeitura com seletor validado.
- Adicionar fallback com Playwright para páginas com JavaScript dinâmico.
