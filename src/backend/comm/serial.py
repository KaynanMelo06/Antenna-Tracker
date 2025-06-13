import math
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt5.QtCore import QByteArray, QObject


class Serial(QObject):
    def __init__(self, port_name: str = "/dev/ttyUSB0") -> None:
        super().__init__()

        # Atributo que simula o “staticData->usb” do C++
        self.usb = False

        # Cria e configura a porta serial
        self.port = QSerialPort()
        self.port.setPortName(port_name)
        self.port.setBaudRate(QSerialPort.Baud115200)
        self.port.setDataBits(QSerialPort.Data8)
        self.port.setParity(QSerialPort.NoParity)
        self.port.setStopBits(QSerialPort.OneStop)
        self.port.setFlowControl(QSerialPort.NoFlowControl)

        #Tenta abrir a porta em modo ReadWrite
        if not self.port.open(QSerialPort.ReadWrite):
            raise Exception(
                f"Falha ao abrir porta {self.port.portName()}: {self.port.errorString()}"
            )

        # Se abriu com sucesso, “ativa” o usb 
        if self.port.isOpen():
            self.usb = True

    def close(self) -> None:
        if self.port.isOpen():
            self.port.close()
            self.usb = False

    def sendData(self, id: int, leftspeed: int, rightspeed: int) -> None:
        """
        Envia 'size' bytes vindos de 'data' pela serial, 
        mas somente se usb == True 
        """
        buffer = bytearray(12)
        buffer[0] = id & 0xFF
        
        if(leftspeed == 0 and rightspeed == 0):
            buffer[1] = 0x01
        elif(leftspeed >= 0 and rightspeed >= 0):
            buffer[1] = 0x03
        elif (leftspeed <= 0 and rightspeed <= 0):
            buffer[1] = 0x04
        elif(leftspeed >= 0 and rightspeed <=0 ):
            buffer[1] = 0x05
            if(id == 1 or id == 3):
                buffer[1] = 0x06
        elif(leftspeed <= 0 and rightspeed >=0 ):
            buffer[1] = 0x06
            if(id == 1 or id == 3):
                buffer[1] = 0x05
                
        buffer[2] = ((abs(leftspeed) >> 8) & 0xFF)
        buffer[3] = (abs(leftspeed) & 0xFF)
        buffer[4] = ((abs(rightspeed) >> 8) & 0xFF)
        buffer[5] = (abs(rightspeed) & 0xFF)
    
        
        lowD = int(0.772 * 1000)
        lowI = int(0.000 * 1000)
        lowP = int(4.956 * 1000)
        

        buffer[6] = ((lowP >> 8) & 0xFF)
        buffer[7] = (lowP & 0xFF)
        buffer[8] = ((lowI >> 8) & 0xFF)
        buffer[9] = (lowI & 0xFF)
        buffer[10] = ((lowD >> 8) & 0xFF)
        buffer[11] = (lowD & 0xFF)
       
        if self.usb and self.port.isOpen():
            # QByteArray recebe (char*) em C++; em Python, basta passar bytes
            message = QByteArray(buffer)
            self.port.flush()
            self.port.write(message)
            self.port.flush()
