import streamlit as st
import os
from datetime import datetime, date
from utils.database import (
    add_produto, get_all_produtos, mark_produto_as_sold,
    MARCAS, ESTILOS, TIPOS
)

# --- Funções Auxiliares ---
def load_css(file_name):
    if not os.path.exists(file_name):
        st.warning(f"O arquivo CSS '{file_name}' não foi encontrado.")
        return
    try:
        with open(file_name, encoding='utf-8') as f: 
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erro ao carregar CSS: {e}")

load_css("style.css")

# Ações do chatbot
st.set_page_config(page_title="Chatbot de Estoque - Cores e Fragrâncias")

# Inicializa o estado de login se não existir
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# Verifica se o usuário está logado
if not st.session_state.get("logged_in"):
    st.error("Acesso negado. Faça login na área administrativa para usar o chatbot.")
    st.info("Vá para a página 'Área Administrativa' para entrar.")
    st.stop()

# --- CHATBOT ---

# Inicializa o histórico do chat
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = [
        {"role": "assistant", "content": "Olá! Sou o Chatbot de Estoque. Como posso ajudar você? Digite 'ajuda' para ver os comandos."}
    ]
if "chat_state" not in st.session_state:
    st.session_state["chat_state"] = {"step": "idle", "data": {}}

st.title("🤖 Chatbot de Estoque (Operacional)")

# Função principal do Chatbot
def process_command(user_input: str):
    user_input = user_input.strip().lower()
    
    # --- Lógica de Cancelamento Global ---
    if user_input == "cancelar":
        if st.session_state["chat_state"]["step"] != "idle":
            st.session_state["chat_state"] = {"step": "idle", "data": {}}
            return "Operação cancelada. Digite 'ajuda' para ver os comandos."
        return "Não há nenhuma operação em andamento para cancelar."

    # --- Lógica do Estado (Adicionar Produto) ---
    state = st.session_state["chat_state"]
    if state["step"] == "add_waiting_nome":
        state["data"]["nome"] = user_input.title()
        state["step"] = "add_waiting_preco"
        return "Qual é o **Preço** (ex: 49.90)? OBS: Preço deve ser positivo."
    
    elif state["step"] == "add_waiting_preco":
        try:
            preco_float = float(user_input.replace(",", "."))
            if preco_float <= 0:
                return "O preço deve ser um valor positivo."
            state["data"]["preco"] = preco_float
            state["step"] = "add_waiting_qtd"
            return "Qual é a **Quantidade** em estoque (somente número inteiro)? OBS: Quantidade não negativa."
        except ValueError:
            return "Formato de preço inválido. Por favor, digite o preço (ex: 49.90)."
            
    elif state["step"] == "add_waiting_qtd":
        try:
            quantidade_int = int(user_input)
            if quantidade_int < 0:
                return "A quantidade não pode ser negativa."
            state["data"]["quantidade"] = quantidade_int
            state["step"] = "add_waiting_marca"
            return f"De qual **Marca** é o produto? Opções (parcial): {', '.join(MARCAS[:5])}..."
        except ValueError:
            return "Formato de quantidade inválido. Por favor, digite um número inteiro."
    
    elif state["step"] == "add_waiting_marca":
        if user_input.title() in MARCAS:
            state["data"]["marca"] = user_input.title()
            state["step"] = "add_waiting_estilo"
            return f"Qual é o **Estilo**? (Opções: {', '.join(ESTILOS[:5])}...). "
        else:
            return "Marca não reconhecida. Tente novamente ou digite 'cancelar'."
            
    elif state["step"] == "add_waiting_estilo":
        if user_input.title() in ESTILOS:
            state["data"]["estilo"] = user_input.title()
            state["step"] = "add_waiting_tipo"
            return f"Qual é o **Tipo**? (Opções: {', '.join(TIPOS[:5])}...). "
        else:
            return "Estilo não reconhecido. Tente novamente ou digite 'cancelar'."

    elif state["step"] == "add_waiting_tipo":
        if user_input.title() in TIPOS:
            state["data"]["tipo"] = user_input.title()
            state["step"] = "add_waiting_validade"
            return "Qual a **Data de Validade**? (Formato: DD/MM/AAAA ou 'nao')"
        else:
            return "Tipo não reconhecido. Tente novamente ou digite 'cancelar'."

    elif state["step"] == "add_waiting_validade":
        data_validade_iso = None
        if user_input != 'nao':
            try:
                data_validade = datetime.strptime(user_input, "%d/%m/%Y").date()
                data_validade_iso = data_validade.isoformat()
            except ValueError:
                return "Formato de data inválido. Use DD/MM/AAAA ou digite 'nao'."
        
        # Concluir a adição
        try:
            add_produto(
                state["data"]["nome"], state["data"]["preco"], state["data"]["quantidade"], 
                state["data"]["marca"], state["data"]["estilo"], state["data"]["tipo"], 
                None, data_validade_iso
            )
            nome = state["data"]["nome"]
            state["step"] = "idle"
            state["data"] = {}
            st.session_state["chat_state"] = state
            
            # 🚀 ATUALIZAÇÃO AUTOMÁTICA
            st.rerun() 
            return f"🎉 Produto **'{nome}'** adicionado com sucesso! Mais alguma coisa? Digite 'ajuda'."
        except Exception as e:
            state["step"] = "idle"
            state["data"] = {}
            st.session_state["chat_state"] = state
            return f"❌ Erro ao adicionar produto: {str(e)}. Tente novamente ou digite 'ajuda'."
            
    # --- Lógica do Estado (Marcar como Vendido) ---
    elif state["step"] == "sell_waiting_id":
        try:
            produto_id = int(user_input)
            produtos = get_all_produtos() # Pega os dados mais frescos
            produtos_map = {p['id']: p for p in produtos}
            
            if produto_id in produtos_map and int(produtos_map[produto_id]['quantidade']) > 0:
                mark_produto_as_sold(produto_id, 1) # Vende 1 unidade
                
                # Mensagem de sucesso
                estoque_restante = int(produtos_map[produto_id]['quantidade']) - 1
                if estoque_restante == 0:
                    result_msg = f"✅ Produto **{produtos_map[produto_id]['nome']}** (ID: {produto_id}) marcado como **VENDIDO** e fora de estoque."
                else:
                    result_msg = f"✅ 1 unidade de **{produtos_map[produto_id]['nome']}** (ID: {produto_id}) vendida. Estoque restante: {estoque_restante}."

                state["step"] = "idle"
                state["data"] = {}
                st.session_state["chat_state"] = state
                
                # 🚀 ATUALIZAÇÃO AUTOMÁTICA
                st.rerun()
                return result_msg
            
            elif produto_id in produtos_map and int(produtos_map[produto_id]['quantidade']) == 0:
                state["step"] = "idle"
                state["data"] = {}
                st.session_state["chat_state"] = state
                return f"❌ Produto (ID: {produto_id}) já está fora de estoque."
            else:
                return "ID do produto não encontrado. Por favor, digite um ID válido ou 'cancelar'."
        except ValueError:
            return "ID inválido. Por favor, digite somente o número do ID ou 'cancelar'."
            
    # --- Comandos de Ação (Apenas se em estado 'idle') ---
    if state["step"] == "idle":
        if user_input == "ajuda":
            # ... (Comandos inalterados) ...
            return ("**Comandos disponíveis:**\n"
                    "- `adicionar produto`: Inicia o formulário de cadastro.\n"
                    "- `estoque`: Mostra todos os produtos.\n"
                    "- `estoque [marca]`: Filtra o estoque por uma marca (ex: `estoque eudora`).\n"
                    "- `vender [ID]`: Marca 1 unidade de um produto como vendido. Ou digite `vender` para ser guiado.\n"
                    "- `cancelar`: Cancela a operação atual.\n"
                    "- `ajuda`: Mostra esta lista.")

        elif user_input == "adicionar produto":
            state["step"] = "add_waiting_nome"
            state["data"] = {}
            st.session_state["chat_state"] = state
            return "Ok, vamos adicionar um produto. Qual é o **Nome** dele?"
            
        elif user_input.startswith("vender"):
            parts = user_input.split()
            if len(parts) == 2: # Tenta vender diretamente pelo ID
                state["step"] = "sell_waiting_id" # Reusa a lógica de verificação
                st.session_state["chat_state"] = state
                return process_command(parts[1])
            else:
                state["step"] = "sell_waiting_id"
                state["data"] = {}
                st.session_state["chat_state"] = state
                return "Certo. Qual é o **ID do produto** que você vendeu?"

        elif user_input.startswith("estoque"):
            produtos = get_all_produtos() # Pega os dados mais frescos
            if len(user_input.split()) == 1:
                if not produtos:
                    return "Nenhum produto cadastrado no estoque."
                
                response = "**Produtos em Estoque:**\n"
                for p in produtos:
                    response += f"- **{p['nome']}** (ID: {p['id']}) - R$ {p['preco']:.2f}, Qtd: {p['quantidade']}, Marca: {p['marca']}\n"
                return response
                
            else:
                target_marca = user_input.split("estoque ", 1)[1].strip().title()
                produtos_filtrados = [p for p in produtos if p.get("marca") == target_marca]
                
                if not produtos_filtrados:
                    return f"Nenhum produto encontrado para a marca **{target_marca}**."
                    
                response = f"**Produtos da marca {target_marca} em Estoque:**\n"
                for p in produtos_filtrados:
                    response += f"- **{p['nome']}** (ID: {p['id']}) - R$ {p['preco']:.2f}, Qtd: {p['quantidade']}, Estilo: {p['estilo']}\n"
                return response

        else:
            return "Desculpe, não entendi o comando. Digite 'ajuda' para ver os comandos disponíveis."
            
    return "Resposta não esperada. Por favor, siga as instruções ou digite 'cancelar' para abortar."


# --- Interface do Streamlit ---

# Exibe o histórico de mensagens
for message in st.session_state["chat_history"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Processa a entrada do usuário
if user_input := st.chat_input("Seu comando..."):
    st.session_state["chat_history"].append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.markdown(user_input)
        
    response = process_command(user_input)
    with st.chat_message("assistant"):
        st.markdown(response)
        
    st.session_state["chat_history"].append({"role": "assistant", "content": response})