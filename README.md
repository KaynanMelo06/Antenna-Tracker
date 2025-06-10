# ProjetoAntena

Uma aplicação em Python com PyQt5 e OpenCV para rastreamento e controle de uma antena via microcontrolador.  
Captura vídeo, corrige distorção, detecta marcadores coloridos em tempo real, calcula ângulos e utiliza um controlador PID para enviar comandos via serial.

---

## ✨ Funcionalidades

- Correção de distorção ótica (calibração de câmera).  
- Detecção de marcadores HSV (laranja, rosa, verde, amarelo).  
- Cálculo de posição e orientação do robô.  
- Controle PID para ajuste fino da antena.  
- Interface gráfica em PyQt5 para visualização e calibração.  
- Comunicação serial (QSerialPort) com microcontrolador (baud rate configurável).

---

## 🚀 Instalação

1. **Clone o repositório**  
   ```bash
   git clone https://github.com/seu-usuario/projetoantenaV1.git
   cd projetoantenaV1
   ```

2. **Crie e ative um ambiente virtual**  
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # Linux / macOS
   .venv\Scripts\activate      # Windows
   ```

3. **Instale as dependências**  
   ```bash
   pip install -r requirements.txt
   ```

---

## ⚙️ Configuração

- **Porta Serial**  
  Edite em `src/backend/comm/serial.py` ou via parâmetro na `MainWindow`:  
  ```python
  self.serial = Serial(port="COM3", baudrate=115200)
  ```

- **Índice da Câmera**  
  Altere em `src/ui/mainwindow.py`:  
  ```python
  self.cap = cv2.VideoCapture(0)   # ou "/dev/video2"
  ```

- **Parâmetros PID**  
  Ajuste em `src/backend/control/pid.py` ou diretamente na UI:  
  ```python
  kp, ki, kd = 1.0, 0.01, 0.1
  ```

- **Ranges HSV iniciais**  
  Definidos em `src/ui/mainwindow.py`, mas podem ser calibrados em tempo real.

---

## 📈 Uso

1. Inicie a aplicação:  
   ```bash
   python main.py
   ```

2. Na janela principal:  
   - Visualize o **frame original** (com anotações) e o **frame filtrado**.  
   - Selecione a cor do marcador ou “Todos”.  
   - Pressione **K** para ligar/pausar o envio de comandos serial.  
   - Pressione **Esc** para sair do fullscreen.

3. Para calibrar HSV:  
   - Clique em **“Calibrar HSV”**.  
   - Ajuste sliders de **H**, **S**, **V**.  
   - Use **Reset** para valores padrões ou **Apply** para aplicar novas faixas.

---

## 🔧 Desenvolvimento

- Rode exemplos em `src/aprender/` para entender como funciona a captura de vídeo e trackbars.  
- Organize novos filtros ou lógica de processamento em `src/backend/`.  
- Adicione novas janelas ou componentes em `src/ui/`.
