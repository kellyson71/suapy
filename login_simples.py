from getpass import getpass
from suapy import autenticar

matricula = input("Digite sua matrícula: ")
senha = getpass("Digite sua senha: ")

perfil = autenticar(matricula, senha)

print("Login realizado com sucesso!")
print(f"Olá, {perfil.nome}!")
print(f"E-mail: {perfil.email}")
