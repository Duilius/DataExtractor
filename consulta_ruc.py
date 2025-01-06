import requests
from bs4 import BeautifulSoup

def consultar_ruc(ruc):
    url = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.62 Safari/537.36'
    }
    
    session = requests.Session()
    try:
        # Solicitud inicial
        response = session.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return "Error al acceder a la página principal"
        
        # Realiza la consulta con el RUC
        data = {
            'accion': 'consPorRuc',
            'nroRuc': ruc,
        }
        consulta_url = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias"
        consulta = session.post(consulta_url, headers=headers, data=data, timeout=10)

        # Analiza la respuesta
        if consulta.status_code == 200:
            soup = BeautifulSoup(consulta.text, 'html.parser')
            resultados = soup.find_all('td')  # Ajusta este selector según la estructura de la página
            return [td.text.strip() for td in resultados]
        else:
            return f"Error en la consulta: {consulta.status_code}"
    except requests.exceptions.Timeout:
        return "Error: Tiempo de espera excedido"
    except requests.exceptions.ConnectionError as e:
        return f"Error de conexión: {e}"
    except Exception as e:
        return f"Error inesperado: {e}"

# Ejemplo de uso
ruc = "10053937760"
estado_ruc = consultar_ruc(ruc)
print(estado_ruc)
