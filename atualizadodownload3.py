import os
import httpx  # Substituímos requests por httpx
import xml.etree.ElementTree as ET
from urllib.parse import quote, urlparse
from tkinter import *
from tkinter import filedialog
import time
import tkinter as tk
from tkinter import ttk
import pandas as pd
import re
import tkinter.messagebox

def download_files():
    global root
    api_key = api_key_entry.get()
    download_folder = folder_entry.get()
    if not api_key or not download_folder:
        return
    files_list = text_area.get("1.0", END).split("\n")
    files_list = [file.strip() for file in files_list if file]
    files_downloaded = 0
    files_already_downloaded = 0

    # Verificar todos os arquivos antes de começar o download
    files_to_download = []
    for file in files_list:
        encoded_file = quote(file)
        file_url = server + "xml/" + encoded_file + "?apiKey=" + api_key
        temp_file_name = os.path.basename(urlparse(file_url).path) + '.xml'
        
        # Procurar em todas as subpastas do diretório de download
        arquivo_encontrado = False
        for root_dir, dirs, files in os.walk(download_folder):
            if temp_file_name in files:
                arquivo_encontrado = True
                files_already_downloaded += 1
                break
        
        if not arquivo_encontrado:
            files_to_download.append(file)
    
    # Atualizar o máximo da barra de progresso para refletir apenas arquivos novos
    progress_bar['maximum'] = len(files_to_download)
    progress_bar['value'] = 0
    
    # Mostrar mensagem se todos os arquivos já estiverem baixados
    if not files_to_download:
        tk.messagebox.showinfo("Aviso", f"Todos os {files_already_downloaded} arquivos já estão baixados!")
        return
    
    # Continuar apenas com arquivos novos
    for file in files_to_download:
        # Codificar o nome do arquivo para evitar caracteres de controle
        encoded_file = quote(file)
        file_url = server + "xml/" + encoded_file + "?apiKey=" + api_key
        parsed_url = urlparse(file_url)
        file_name = os.path.basename(parsed_url.path) + '.xml'
        file_path = os.path.join(download_folder, file_name)

        # Definir o nome do arquivo temporário
        temp_file_name = os.path.basename(urlparse(file_url).path) + '.xml'
        temp_file_path = os.path.join(download_folder, temp_file_name)

        if os.path.exists(temp_file_path):
            files_already_downloaded += 1
            progress_bar['value'] += 1
            root.update_idletasks()
            continue

        try:
            # Baixar o arquivo temporariamente usando httpx
            with httpx.Client(verify=False) as client:  # Desativa a verificação SSL
                response = client.get(file_url)
                response.raise_for_status()  # Levanta exceção se houver erro HTTP
                with open(temp_file_path, 'wb') as f:
                    f.write(response.content)
            files_downloaded += 1

            # Analisar o XML para extrair o CNPJ e o nome desejado
            tree = ET.parse(temp_file_path)
            root_xml = tree.getroot()
            
            # Extrair CNPJ e nome
            cnpj_tag = root_xml.find('.//CNPJ')
            nome_tag = root_xml.find('.//xNome')
            
            if cnpj_tag is not None and nome_tag is not None:
                cnpj = cnpj_tag.text
                nome = nome_tag.text
                
                # Remover caracteres inválidos do nome do diretório
                cnpj = re.sub(r'[<>:"/\\|?*]', '', cnpj)
                nome = re.sub(r'[<>:"/\\|?*]', '', nome)
                
                # Criar a pasta do CNPJ seguido do nome se não existir
                folder_name = f"{cnpj}_{nome}"
                nome_folder = os.path.join(download_folder, folder_name)
                if not os.path.exists(nome_folder):
                    os.makedirs(nome_folder)
                
                # Mover o arquivo para a pasta correta
                final_file_path = os.path.join(nome_folder, temp_file_name)
                os.rename(temp_file_path, final_file_path)
            else:
                print("Tag <CNPJ> ou <xNome> não encontrada no XML.")
                os.remove(temp_file_path)  # Remover o arquivo temporário se as tags não forem encontradas

            print("chave: " + temp_file_name + " processada com sucesso")  # Dentro do try

        except Exception as e:
            print(f"Erro ao processar o arquivo {temp_file_name}: {e}")
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)  # Remover o arquivo temporário em caso de erro

        progress_bar['value'] += 1
        root.update_idletasks()
    
    if files_already_downloaded > 0:
        tk.messagebox.showinfo("Aviso", f"{files_already_downloaded} arquivos já estavam baixados.")
    if files_downloaded == 0:
        tk.messagebox.showinfo("Aviso", "Nenhum arquivo foi baixado com sucesso!")
    else:
        tk.messagebox.showinfo("Concluído", f"Download finalizado!\n\nArquivos baixados com sucesso: {files_downloaded}\nArquivos já existentes: {files_already_downloaded}")

def select_folder():
    folder_path = filedialog.askdirectory()
    folder_entry.delete(0, END)
    folder_entry.insert(0, folder_path)

def select_excel_files():
    file_paths = filedialog.askopenfilenames(filetypes=[("Excel files", "*.xls *.xlsx")])
    if not file_paths:
        return
    try:
        all_keys = []
        for file_path in file_paths:
            df = pd.read_excel(file_path, usecols="B", header=None)
            keys = df.iloc[:, 0].dropna().tolist()
            all_keys.extend(keys)
        
        text_area.delete("1.0", END)
        text_area.insert(END, "\n".join(all_keys))
    except Exception as e:
        tk.messagebox.showerror("Erro", f"Erro ao ler os arquivos Excel: {e}")

server = "https://cfe.sefaz.ce.gov.br:8443/portalcfews/mfe/fiscal-coupons/"

def create_interface():
    global root, api_key_entry, folder_entry, text_area, progress_bar

    root = Tk()
    root.title("Download Cf-e por JannioFSantos")

    # Estilo para a interface
    style = ttk.Style()
    style.configure('TButton', font=('Helvetica', 10))
    style.configure('TLabel', font=('Helvetica', 10))
    style.configure('TEntry', font=('Helvetica', 10))
    style.configure('TText', font=('Helvetica', 10))

    api_key_label = ttk.Label(root, text="Apikey=")
    api_key_label.pack()

    api_key_entry = ttk.Entry(root, width=70)
    api_key_entry.pack()

    folder_label = ttk.Label(root, text="Caminho pasta download")
    folder_label.pack()

    folder_entry = ttk.Entry(root, width=70)
    folder_entry.pack()

    folder_button = ttk.Button(root, text="Selecionar pasta", command=select_folder)
    folder_button.pack()

    # Botão para selecionar arquivo Excel
    excel_button = ttk.Button(root, text="Selecionar planilhas Excel", command=select_excel_files)
    excel_button.pack(pady=5)

    text_area = Text(root, height=30, width=70, font=('Helvetica', 10))
    text_area.pack()

    download_button = ttk.Button(root, text="Iniciar download", command=download_files)
    download_button.pack(padx=10, pady=10)

    # Adicionar a barra de progresso
    progress_bar = ttk.Progressbar(root, orient='horizontal', length=400, mode='determinate')
    progress_bar.pack(pady=10)

    root.mainloop()

# Chamar a função para criar a interface
create_interface()