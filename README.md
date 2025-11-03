# Cores e Fragrâncias by Berenice

Projeto Streamlit para gerenciamento de estoque de uma loja de cosméticos.
Estrutura pronta com CRUD, autenticação de administradores, upload de imagens e scripts de seed.

## Como usar
1. Ative o virtualenv e instale dependências:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. Rode o app:
   ```bash
   streamlit run app.py
   ```
3. Vá para a página "Área Administrativa" e cadastre um admin.
4. Use "Gerenciar Produtos" para adicionar/editar/remover produtos.

## O que está incluso
- app.py
- utils/database.py
- pages/1_Estoque.py
- pages/2_Gerenciar_Produtos.py
- pages/3_Area_Administrativa.py
- scripts/seed.py (insere produtos de exemplo)
- assets/logo.png (placeholder)
- data/ (banco será criado automaticamente)
- ZIP export disponível no mesmo diretório


## Novas funcionalidades adicionadas

- Importação/Exportação CSV de produtos
- Geração de relatório em PDF do estoque
- Limpeza automática de imagens quando produto é deletado (apenas se não usadas por outros produtos)
- Layout de listagem melhorado (cards/colunas)
- Papéis de usuário (admin/staff) com permissões (apenas admin pode remover produtos)
