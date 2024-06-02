#bibliotecas

import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.svm import SVR, SVC
from ttkthemes import ThemedStyle
import requests
from plyer import notification

# Login
def fazer_login():
    usuario = entry_usuario.get()
    senha = entry_senha.get()

    # Conexão banco de dados
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM usuario WHERE nome_usuario = %s AND senha = %s", (usuario, senha))
    usuario_existente = cursor.fetchone()

    if usuario_existente:
        login_frame.grid_remove()  # Remover o frame de login
        main_frame.grid()  # Exibir o frame principal
    else:
        messagebox.showerror("Erro de Login", "Credenciais inválidas. Tente novamente.")

    conn.close()

def fazer_cadastro():
    usuario = entry_novo_usuario.get()
    senha = entry_nova_senha.get()

    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()

    # Inserir novo usuário ao bd
    cursor.execute("INSERT INTO usuario (nome_usuario, senha) VALUES (%s, %s)", (usuario, senha))
    conn.commit()

    messagebox.showinfo("Cadastro", f"Usuário {usuario} cadastrado com sucesso!")
    conn.close()

# Obter os dados h. de uma cidade do banco de dados
def obter_dados_historicos(cidade):
    cursor.execute("SELECT temperatura_celsius, umidade, pressao FROM openmap WHERE cidade = %s", (cidade,))
    rows = cursor.fetchall()
    historical_data = pd.DataFrame(rows, columns=['temperatura', 'umidade', 'pressao'])
    historical_data['cidade'] = cidade  # Adicionando a coluna 'cidade'
    return historical_data

# Prever a temperatura futura
def prever_temperatura(model, df, cidade):
    cidade_data = df[df['cidade'] == cidade][['umidade', 'pressao']]
    previsao_temperatura = model.predict(cidade_data)
    dias_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
    previsao_str = ""
    for i, temperatura in enumerate(previsao_temperatura, start=1):
        dia = dias_semana[i % 7]  # Calcular o dia da semana
        previsao_str += f"{dia}: {temperatura:.2f}°C\n"
    return previsao_str

# Prever se vai chover
def prever_chuva(model, df, cidade):
    cidade_data = df[df['cidade'] == cidade][['umidade', 'pressao']]
    previsao_chuva = model.predict(cidade_data)
    vai_chover = any(previsao_chuva == 1)
    return vai_chover

# Obter temperatura atual de Sp
def obter_temperatura_sao_paulo():
    api_key = "b1b3b2f303756f31d1a4b8ba85e04115"
    url = f"http://api.openweathermap.org/data/2.5/weather?q=São Paulo,BR&appid={api_key}&units=metric"
    response = requests.get(url)
    data = response.json()
    return data['main']['temp']

# Tomada decisões/Envio de notificações baseadas nas previsões
def tomar_decisoes(cidade):
    previsao_temperatura = prever_temperatura(model_temperatura, df, cidade)
    vai_chover = prever_chuva(model_chuva, df, cidade)
    mostrar_previsao(cidade, previsao_temperatura)

    if vai_chover:
        notification.notify(
            title='Previsão de Chuva',
            message='Vai chover.',
            timeout=5
        )
    else:
        notification.notify(
            title='Previsão de Chuva',
            message='Não vai chover.',
            timeout=5
        )

    previsoes = previsao_temperatura.split('\n')
    for previsao in previsoes:
        if previsao:
            dia, temperatura = previsao.split(': ')
            temperatura = float(temperatura.replace('°C', ''))
            if temperatura > 30:
                notification.notify(
                    title='Alerta de Alta Temperatura',
                    message=f'Temperatura alta prevista para {dia}: {temperatura:.2f}°C',
                    timeout=5
                )
            elif temperatura < 10:
                notification.notify(
                    title='Alerta de Baixa Temperatura',
                    message=f'Temperatura baixa prevista para {dia}: {temperatura:.2f}°C',
                    timeout=5
                )

def selecionar_cidade():
    cidade = combo_cidades.get()
    if cidade:
        tomar_decisoes(cidade)
    else:
        lbl_status.config(text="Por favor, selecione uma cidade.")

# Exibir a previsão de temperatura em uma nova tela
def mostrar_previsao(cidade, previsao):
    window = tk.Toplevel(root)
    window.title("Previsão de Temperatura e Chuva")
    window.geometry("400x400")

    lbl_titulo = tk.Label(window, text=f"Previsão de {cidade}", font=("Helvetica", 14))
    lbl_titulo.pack(pady=10)

    lbl_previsao_temperatura = tk.Label(window, text="Temperatura:\n" + previsao, justify="left")
    lbl_previsao_temperatura.pack(padx=20, pady=20)

# Configurações de conexão
config = {
    'user': 'root',
    'password': 'grazi123',
    'host': 'localhost',
    'database': 'sys'
}

conn = mysql.connector.connect(**config)
cursor = conn.cursor()

# Cidades para consultar
cidades = ['Campinas', 'Ribeirão Preto', 'Sorocaba', 'Bauru', 'São José do Rio Preto', 'Araraquara', 'Piracicaba',
           'Marília', 'São Paulo']

# Lista para armazenamento dd dados históricos de todas as cidades
all_city_data = []

for cidade in cidades:
    city_data = obter_dados_historicos(cidade)
    all_city_data.append(city_data)

# Fechar a conexão SQL
conn.close()

# Concatenar os dados de todas as cidades em um único DataFrame
df = pd.concat(all_city_data)

# Dividir os dados / treinamento e teste para temperatura
X_train_temp, X_test_temp, y_train_temp, y_test_temp = train_test_split(df[['umidade', 'pressao']], df['temperatura'], test_size=0.2,
                                                                        random_state=42)

# Treinar o ia de regressão para temperatura
model_temperatura = SVR(kernel='rbf')
model_temperatura.fit(X_train_temp, y_train_temp)

#

df['chuva'] = (df['umidade'] > 80).astype(int)

#
X_train_chuva, X_test_chuva, y_train_chuva, y_test_chuva = train_test_split(df[['umidade', 'pressao']], df['chuva'], test_size=0.2,
                                                                            random_state=42)

model_chuva = SVC(kernel='rbf')
model_chuva.fit(X_train_chuva, y_train_chuva)

# interface

root = tk.Tk()
root.title("Previsão de Temperatura e Chuva")

# tema da interface
style = ThemedStyle(root)
style.set_theme("arc")


login_frame = ttk.Frame(root, padding=20)
login_frame.grid(row=0, padx=100, pady=50)

lbl_usuario = ttk.Label(login_frame, text="Usuário:")
lbl_usuario.grid(row=0, column=0, sticky="e", padx=5, pady=5)
entry_usuario = ttk.Entry(login_frame, width=30)
entry_usuario.grid(row=0, column=1, padx=5, pady=5)

lbl_senha = ttk.Label(login_frame, text="Senha:")
lbl_senha.grid(row=1, column=0, sticky="e", padx=5, pady=5)
entry_senha = ttk.Entry(login_frame, show="*", width=30)
entry_senha.grid(row=1, column=1, padx=5, pady=5)

btn_login = ttk.Button(login_frame, text="Login", command=fazer_login)
btn_login.grid(row=2, columnspan=2, pady=10)

main_frame = ttk.Frame(root, padding=20)

lbl_title = ttk.Label(main_frame, text="Previsão de Temperatura e Chuva", font=("Helvetica", 18))
lbl_title.grid(row=0, column=0, columnspan=2, pady=(0, 20))


lbl_temp_sao_paulo = ttk.Label(main_frame, text="Temperatura atual em São Paulo: ")
lbl_temp_sao_paulo.grid(row=1, column=0, columnspan=2, pady=10)


try:
    temp_sao_paulo = obter_temperatura_sao_paulo
    temp_sao_paulo = obter_temperatura_sao_paulo()
    lbl_temp_sao_paulo.config(text=f"Temperatura atual em São Paulo: {temp_sao_paulo:.2f}°C")
except Exception as e:
    lbl_temp_sao_paulo.config(text="Erro ao obter a temperatura atual de São Paulo")

# Combobox
combo_cidades = ttk.Combobox(main_frame, values=cidades, state="readonly", width=30)
combo_cidades.grid(row=2, column=0, padx=10, pady=10)

btn_prever = ttk.Button(main_frame, text="Prever Temperatura e Fenômenos", command=selecionar_cidade)
btn_prever.grid(row=2, column=1, padx=10, pady=10)


lbl_status = ttk.Label(main_frame, text="")
lbl_status.grid(row=3, column=0, columnspan=2)


main_frame.grid_remove()

root.mainloop()
