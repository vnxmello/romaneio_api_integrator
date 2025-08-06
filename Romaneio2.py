import psycopg2
import json
import requests
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime

#configuracoes de conexao com o bd postgresql
conn_config = {
    'host': '',
    'database': '',
    'port': '',
    'user': '',
    'password': ''
}

#criacao do template json / dados OBRIGATORIOS minimos para o post 
json_template = [
    {
        "Driver": {
            "PhoneCountry": "55",
            "PhoneNumber": "1",
            "DefineDriverAfter": 1
        },
        "Customer": {
            "DocumentType": "CNPJ",
            "DocumentNumber": "44496590000160"
        },
        "OrderType": 1,
        "OrderID": "",
        "OrderNumber": "",
        "OrderDescription": "CT-e",
        "SourceAddress": {
            "Address": "",
            "Address2": "",
            "ZipCode": "",
            "City": "",
            "State": "",
            "Country": "Brasil",
            "Name": "",
            "DocumentNumber": ""
        },
        "DestinationAddress": {
            "Address": "",
            "Address2": "",
            "ZipCode": "",
            "City": "",
            "State": "",
            "Country": "Brasil",
            "Name": "",
            "Responsibility": "",
            "PhoneCountry": "55",
            "PhoneNumber": ""
        },
        "DeliveryDate": ""
    }
]

#funcao para buscar dados do banco de dados
def fetch_data(romaneio):
    try:
        conn = psycopg2.connect(**conn_config)
        cur = conn.cursor()
        query = """
WITH tb AS (
    SELECT
        t1.tipo_entrega,
        t1.romaneio,
        regexp_replace(t1.cliente_documento, '[-()./ ]', '', 'gi') AS cliente_documento,
        t1.cliente_nome,
        regexp_replace(t1.cliente_celular, '[-()./ ]', '', 'gi') AS cliente_celular,
        regexp_replace(t1.emitente_documento, '[-() /.]', '', 'gi') AS emitente_documento,
        t1.emitente,
        regexp_replace(t1.emitente_cep, '[-(). ]', '', 'gi') AS emitente_cep,
        t1.emitente_endereco,
        t1.emitente_complemento,
        t1.emitente_bairro,
        t1.emitente_cidade,
        t1.emitente_estado,
        regexp_replace(t1.destinatario_cep, '[-() ]', '', 'gi') AS destinatario_cep,
        t1.destinatario_endereco,
        t1.destinatario_complemento,
        t1.destinatario_bairro,
        t1.destinatario_cidade,
        t1.destinatario_estado,
        t2.data_previsao_entrega,
        t2.observacoes
    FROM (
        SELECT
            d.numero_lancamento,
            p.codigo,
            (CASE WHEN d.filial_id = 15 THEN 'ENTREGA' ELSE 'COLETA' END)::CHARACTER(7) AS tipo_entrega,
            rsp.romaneio_separacao_id AS romaneio,
            p.cpf_cnpj AS cliente_documento,
            UPPER(p.nome) AS cliente_nome,
            COALESCE(pc.informacao, '9999999999')::CHARACTER(20) AS cliente_celular,
            pr.cpf_cnpj AS emitente_documento,
            f.descricao AS emitente,
            cp_e.cep AS emitente_cep,
            BTRIM(UPPER(d.emitente_logradouro) || ' , ' || d.emitente_numero)::CHARACTER(100) AS emitente_endereco,
            UPPER(d.emitente_complemento) AS emitente_complemento,
            UPPER(b_e.descricao) AS emitente_bairro,
            UPPER(c_e.descricao) AS emitente_cidade,
            'RS'::CHARACTER(2) AS emitente_estado,
            cp.cep AS destinatario_cep,
            BTRIM(UPPER(d.destinatario_logradouro) || ' , ' || d.destinatario_numero) AS destinatario_endereco,
            UPPER(d.destinatario_complemento) AS destinatario_complemento,
            UPPER(b.descricao) AS destinatario_bairro,
            UPPER(c.descricao) AS destinatario_cidade,
            u.sigla AS destinatario_estado
        FROM atmiranda.romaneios_separacoes_pedidos rsp
        JOIN atmiranda.documentos d ON d.id = rsp.documento_id
        JOIN atmiranda.pessoas p ON p.id = d.pessoa_cliente_fornecedor_id
        JOIN atmiranda.romaneios_separacoes rp ON rp.id = rsp.romaneio_separacao_id
        JOIN atmiranda.filiais f ON f.id = d.filial_id
        JOIN atmiranda.pessoas pr ON pr.id = f.pessoa_id
        JOIN atmiranda.vendedores v ON v.id = d.vendedor_id
        JOIN atmiranda.pessoas_enderecos p_e ON p_e.id = d.endereco_cliente_fornecedor_id
        JOIN atmiranda.bairros b ON b.id = d.destinatario_bairro_id
        JOIN atmiranda.bairros b_e ON b_e.id = d.emitente_bairro_id
        JOIN atmiranda.ceps cp ON cp.id = d.destinatario_cep_id
        JOIN atmiranda.ceps cp_e ON cp_e.id = d.emitente_cep_id
        JOIN atmiranda.cidades c ON c.id = cp.cidade_id
        JOIN atmiranda.cidades c_e ON c_e.id = cp_e.cidade_id
        JOIN atmiranda.ufs u ON u.id = c.uf_id
        LEFT JOIN (
            SELECT DISTINCT ON (pessoa_id) pessoa_id, informacao
            FROM atmiranda.pessoas_contatos
            WHERE meio_contato_id IN (1, 3, 6)
        ) pc ON p.id = pc.pessoa_id
        WHERE rp.situacao = 1
        AND d.filial_id NOT IN (2, 13)
    ) t1
    JOIN (
        SELECT DISTINCT
            op.descricao AS operacoes,
            fiv.descricao AS filialvenda,
            fie.descricao AS filialentrega,
            doci.numero_lancamento AS lancamento,
            rp.created_at::date AS data,
            rp.data_previsao_entrega,
            pe.codigo,
            pe.nome,
            CASE
                WHEN rp.status = 3 THEN 'Romaneio Finalizado'
                WHEN rp.status = 1 THEN 'Pendente'
                WHEN rp.status = 2 THEN 'Sem Romaneio'
                WHEN rp.status = 5 THEN '5'
                ELSE 'ELSE'
            END AS Status,
            rp.tipo,
            le.descricao AS local_estocagem,
            doc.observacoes
        FROM reservas_produtos rp
        JOIN filiais fiv ON fiv.id = rp.filial_venda_id
        JOIN filiais fie ON fie.id = rp.filial_entrega_id
        JOIN documentos doc ON doc.id = rp.documento_id
        JOIN itens_documentos idoc ON doc.id = idoc.documento_id AND idoc.filial_id = doc.filial_id AND idoc.produto_id = rp.produto_id
        JOIN itens_documentos_locais_estocagens idle ON idoc.id = idle.item_documento_id
        JOIN locais_estocagens le ON le.id = idle.local_estocagem_id
        JOIN documentos doci ON doci.id = rp.documento_ordem_entrega_id AND doci.filial_id = rp.filial_entrega_id
        JOIN pessoas pe ON pe.id = doc.pessoa_cliente_fornecedor_id
        JOIN operacoes_documentos op ON op.id = doc.operacao_documento_id
        WHERE rp.status <> 4
        AND doc.status NOT IN ('devolvido', 'cancelado')
    ) t2 ON t1.numero_lancamento = t2.lancamento AND t1.codigo = t2.codigo
)
SELECT
    romaneio,
    tipo_entrega,
    cliente_documento,
    cliente_nome,
    cliente_celular,
    emitente_documento,
    emitente,
    emitente_cep,
    emitente_endereco,
    emitente_complemento,
    emitente_bairro,
    emitente_cidade,
    emitente_estado,
    destinatario_cep,
    destinatario_endereco,
    destinatario_complemento,
    destinatario_bairro,
    destinatario_cidade,
    destinatario_estado,
    TO_CHAR(data_previsao_entrega, 'dd/mm/yy') AS data_previsao_entrega,
    observacoes
FROM tb
WHERE romaneio = %s
ORDER BY tipo_entrega DESC;
"""
        cur.execute(query, (romaneio,))
        data = cur.fetchall()
        cur.close()
        conn.close()
        return data
    except Exception as e:
        print(f"Erro ao buscar dados: {e}")
        return None

#funcao para preencher o json com os dados buscados
def fill_json(data):
    if not data:
        return None

    json_outputs = []
    for index, row in enumerate(data):
        json_output = json.loads(json.dumps(json_template))  #faz uma cpia exata do template
        json_output[0]["OrderID"] = f"{row[0]}-{index + 1}"  #romaneio com sufixo para cada entrega/coleta
        json_output[0]["OrderNumber"] = f"{row[0]}-{index + 1}"  # romaneio com sufixo
        json_output[0]["OrderType"] = 1 if row[1] == 'ENTREGA' else 2  #define orrdertype como 1 para ENTREGA e 2 para COLETA
        json_output[0]["SourceAddress"]["Address"] = row[8]  #emitente_endereco
        json_output[0]["SourceAddress"]["Address2"] = row[10]  #emitente_complemento
        json_output[0]["SourceAddress"]["ZipCode"] = row[7]  #emitente_cep
        json_output[0]["SourceAddress"]["City"] = row[11]  #emitente_cidade
        json_output[0]["SourceAddress"]["State"] = row[12]  #emitente_estado
        json_output[0]["SourceAddress"]["Name"] = row[6]  #emitente
        json_output[0]["SourceAddress"]["DocumentNumber"] = row[5]  #emitente_documento
        json_output[0]["DestinationAddress"]["Address"] = row[14]  #destinatario_endereco
        json_output[0]["DestinationAddress"]["Address2"] = row[16]  #destinatario_complemento
        json_output[0]["DestinationAddress"]["ZipCode"] = row[13]  #destinatario_cep
        json_output[0]["DestinationAddress"]["City"] = row[17]  #destinatario_cidade
        json_output[0]["DestinationAddress"]["State"] = row[18]  #destinatario_estado
        json_output[0]["DestinationAddress"]["Name"] = row[3]  #cliente_nome
        json_output[0]["DestinationAddress"]["PhoneCountry"] = "55"  #definindo o codigo do pais do telefone
        json_output[0]["DestinationAddress"]["PhoneNumber"] = row[4]  #cliente_celular
        try:
            delivery_date = datetime.strptime(row[19], '%d/%m/%y').strftime('%Y-%m-%d') #ajuste do formato da data
        except ValueError:
            delivery_date = ""
        json_output[0]["DeliveryDate"] = delivery_date  #data_previsao_entrega
        json_outputs.append(json_output)

    return json_outputs

#funçao para enviar dados para a API
def send_to_api(json_data):
    url = ""  #url da api
    headers = {
        "AppKey": "",
        "Content-Type": "application/json",
        "requesterKey": ""
    }
    try:
        response = requests.post(url, headers=headers, json=json_data)
        if response.status_code != 200:
            print(f"Erro na API: {response.status_code} - {response.text}")
        return response
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar dados para a API: {e}")
        return None

#funcao para confirmar envio dos dados
def confirm_send(romaneio, json_data):
    num_entregas = len(json_data)
    response = messagebox.askyesno("Confirmação", f"Romaneio {romaneio} tem {num_entregas} entregas. Enviar dados para a API?")
    if response:
        for filled_json in json_data:
            print(json.dumps(filled_json, indent=4, ensure_ascii=False))
            response = send_to_api(filled_json)  #envia cada json individualmente
            if response:
                print("Resposta da API:", response.status_code, response.text)
                messagebox.showinfo("Resposta da API", f"Status: {response.status_code}\n{response.text}")
            else:
                messagebox.showerror("Erro", "Erro ao enviar dados para a API.")
    else:
        messagebox.showinfo("Cancelado", "Envio de dados cancelado.")

#funcao para lidar com a preparacao e envio de dados
def handle_send():
    romaneio = entry.get()
    if not romaneio.strip():
        messagebox.showwarning("Aviso", "O campo de romaneio não pode estar vazio.")
        return
    data = fetch_data(romaneio)
    if data:
        filled_jsons = fill_json(data)
        if filled_jsons:
            confirm_send(romaneio, filled_jsons)
    else:
        messagebox.showwarning("Aviso", "Nenhum dado encontrado para o romaneio fornecido.")

#funcao pra fechar a aplicacao
def handle_close():
    root.destroy()

#interface visual/grafica
root = tk.Tk()
root.iconbitmap('icon.ico')
root.title("Romaneio")
root.geometry("400x300")
root.configure(bg="#f0f0f0")

frame = tk.Frame(root, bg="#f0f0f0")
frame.pack(pady=20)

tk.Label(frame, text="Digite o número do romaneio:", font=("Helvetica", 12), bg="#f0f0f0").pack(pady=10)

style = ttk.Style()
style.configure("Custom.TEntry", padding=5, relief="flat", background="#ffffff", foreground="#333333", fieldbackground="#ffffff")
style.map("Custom.TEntry",
          fieldbackground=[('focus', '#e0e0e0')],
          foreground=[('focus', '#333333')])

entry = ttk.Entry(frame, width=40, font=("Helvetica", 12), style="Custom.TEntry")
entry.pack(pady=10)

send_button = tk.Button(frame, text="Enviar", command=handle_send, bg='#28a745', fg='white', font=("Helvetica", 12))
send_button.pack(side=tk.LEFT, padx=10, pady=20)

close_button = tk.Button(frame, text="Fechar", command=handle_close, bg='#dc3545', fg='white', font=("Helvetica", 12))
close_button.pack(side=tk.RIGHT, padx=10, pady=20)

#funcoes para mudar a cor dos botoes ao passar o mouse
def on_enter_send(e):
    send_button['background'] = '#218838'

def on_leave_send(e):
    send_button['background'] = '#28a745'

def on_enter_close(e):
    close_button['background'] = '#c82333'

def on_leave_close(e):
    close_button['background'] = '#dc3545'

#bind de eventos para mudanca de cor dos botoes
send_button.bind("<Enter>", on_enter_send)
send_button.bind("<Leave>", on_leave_send)
close_button.bind("<Enter>", on_enter_close)
close_button.bind("<Leave>", on_leave_close)

#bind de teclas
root.bind('<Return>', lambda event: handle_send())
root.bind('<Escape>', lambda event: handle_close())

root.mainloop()
