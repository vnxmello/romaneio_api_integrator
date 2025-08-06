# Romaneio API Integrator

## Sobre o Projeto
É uma ferramenta de desktop em Python projetada para automatizar o processo de envio de informações de romaneios para a API da Tudo Entregue.

O script se conecta a um banco de dados PostgreSQL, extrai os dados de entregas e coletas, os formata em JSON e, após a confirmação do usuário, envia cada item individualmente para a API. A interface gráfica é construída com a biblioteca `tkinter`, 
para uma experiência de usuário simples e intuitiva.

Esse projeto pode ser facilmente compilado para um executável (o que foi feito), o que o torna uma solução de fácil distribuição e uso para equipes que não possuem conhecimento em programação.

---

## Tecnologias e Pré-requisitos
Para rodar o executavel, basta compilar o script. Você não precisa ter o Python instalado em sua máquina. 

Foram utilizadas as seguintes bibliotecas:
* **psycopg2**: Para conexão com o banco de dados PostgreSQL.
* **requests**: Para realizar as requisições HTTP para a API.
* **tkinter**: Biblioteca padrão do Python para a GUI.
 
//

# Romaneio API Integrator

## About the Project
This is a Python desktop tool designed to automate the process of sending manifest (romaneio) information to the Tudo Entregue API.

The script connects to a PostgreSQL database, extracts delivery and collection data, formats it into JSON, and, after user confirmation, sends each item individually to the API. The graphical user interface (GUI) is built with the tkinter library for a simple and intuitive user experience.

This project can be easily compiled into an executable, making it a straightforward solution for distribution and use by teams without programming knowledge.

## Technologies and Prerequisites
To run the executable, you simply need to compile the script. You do not need to have Python installed on your machine.

The following libraries were used:

psycopg2: For connecting to the PostgreSQL database.

requests: For making HTTP requests to the API.

tkinter: Python's standard library for the GUI.
