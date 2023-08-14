import csv
import os
import tempfile
import pandas as pd


# Função para converter caracteres elegíveis para UTF-8
def convert_word(word):
    word = str(word)
    if "�" in word:
        index = word.index("�")
        word1 = word[:index]
        word2 = word[index+1:]
        with open("resources/wordlist-big-latest.txt", "r") as f:
            for line in f:
                if word1 in line and word2 in line:
                    word = line
                    return word

    # Lista de caracteres elegíveis e suas conversões
    conversions = {
        'Ã¡': 'á',
        'Ã€': 'À',
        'Ã¢': 'â',
        'Ã£': 'ã',
        'Ã©': 'é',
        'Ã‰': 'É',
        'Ãª': 'ê',
        'Ã­': 'í',
        'Ã³': 'ó',
        'Ã´': 'ô',
        'Ãµ': 'õ',
        'Ãº': 'ú',
        'Ã§': 'ç',
        'Ã€': 'À',
        'Ãœ': 'Ü',
        'Ã': 'Á',
        'Ã': 'É',
        'Ã': 'Í',
        'Ã“': 'Ó',
        'Ã”': 'Ô',
        'Ã•': 'Õ',
        'Ãš': 'Ú',
        'Ã‡': 'Ç'
    }
    for k, v in conversions.items():
        word = word.replace(k, v)
    return word


def clean_csv_file(filename):
    # Criar um arquivo temporário para escrever o conteúdo processado
    with tempfile.NamedTemporaryFile(mode='w', delete=False, newline='', encoding="utf-8") as temp_file:
        # Cria um leitor CSV para ler o arquivo original
        with open(filename, 'r') as file:
            reader = csv.reader(file, delimiter=';', quotechar='"')
            # Cria um escritor CSV para escrever no arquivo temporário
            writer = csv.writer(temp_file, quotechar='"', quoting=csv.QUOTE_MINIMAL, delimiter=';')
            # Itera sobre as linhas do arquivo CSV
            for row in reader:
                # Itera sobre as células da linha
                # Itera sobre as células elegíveis para conversão
                if row != []:
                    for cell in row:
                        if "Unnamed" not in cell:
                            # Converte cada célula elegível para UTF-8
                            new_cell = convert_word(cell)
                            # Substitui a célula original pela célula convertida
                            if "," in new_cell:
                                new_cell = new_cell.replace(",", ".")
                            row[row.index(cell)] = new_cell
                    # Escreve a linha com as células convertidas
                else:
                    row = []
                writer.writerow(row)
        temp_file.flush()
        os.fsync(temp_file.fileno())
    # Substitui o arquivo original pelo arquivo temporário
    os.replace(temp_file.name, filename)


def convert_excel_to_csv(file_path):

    try:
        # Verificar se o arquivo existe
        if not os.path.exists(file_path):
            return None

        # Obter extensão do arquivo
        ext = os.path.splitext(file_path)[1]

        # Converter arquivo Excel para CSV
        if ext == ".xlsx" or ext == ".xls":
            df = pd.read_excel(file_path) # erro aqui
            csv_path = os.path.splitext(file_path)[0] + ".csv"
            df.to_csv(csv_path, index=None, header=True, quoting=csv.QUOTE_NONE, escapechar="/", sep=";")
            return csv_path

        # Arquivo já é CSV
        elif ext == ".csv":
            return file_path

        # Arquivo não suportado
        else:
            return None
    except:
        return None
