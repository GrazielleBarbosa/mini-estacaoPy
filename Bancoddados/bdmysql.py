import requests
import mysql.connector


config = {
    'user': 'root',
    'password': 'grazi123',
    'host': 'localhost',
    'database': 'sys'
}


conn = mysql.connector.connect(**config)
cursor = conn.cursor()

# Chave API
api_key = 'b1b3b2f303756f31d1a4b8ba85e04115'


cidades = ['Campinas', 'Ribeirão Preto', 'Sorocaba', 'Bauru', 'São José do Rio Preto', 'Araraquara', 'Piracicaba', 'Marília', 'São Paulo']

for cidade in cidades:

    # OpenWeatherMap
    url = f'http://api.openweathermap.org/data/2.5/weather?q={cidade}&appid={api_key}'

    response = requests.get(url)
    data = response.json()


    temperatura_kelvin = data['main']['temp']
    temperatura_celsius = temperatura_kelvin - 273.15
    umidade = data['main']['humidity']
    pressao = data['main']['pressure']


    sql = "INSERT INTO openmap (temperatura_celsius, umidade, pressao, cidade) VALUES (%s, %s, %s, %s)"
    val = (temperatura_celsius, umidade, pressao, cidade)
    cursor.execute(sql, val)


conn.commit()
conn.close()
