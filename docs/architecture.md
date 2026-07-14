# Arquitetura da MayMay

## Fluxo principal

Usuário
→ interface de texto ou voz
→ API local
→ agente
→ memória e ferramentas
→ Ollama
→ modelo local
→ resposta

## Módulos

- `api`: comunicação entre interface e backend
- `core`: configurações e serviços centrais
- `llm`: comunicação com modelos locais
- `agents`: agentes especializados
- `tools`: ferramentas executáveis
- `memory`: memória de curto e longo prazo
- `voice`: reconhecimento e síntese de voz
- `automation`: tarefas agendadas e monitoramento
- `integrations`: Gmail, Calendar, Drive, Spotify e outros
- `security`: permissões, aprovações e validações
- `storage`: banco de dados e persistência
