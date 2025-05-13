from PyQt5.QtSerialPort import QSerialPort
from PyQt5.QtCore import QByteArray


class Serial :
    def __init__(self, port_name):
        self.port = QSerialPort(port_name)
        self.port.setBaudRate(QSerialPort.Baud9600)
        self.port.setDataBits(QSerialPort.Data8)
        self.port.setParity(QSerialPort.NoParity)
        self.port.setStopBits(QSerialPort.OneStop)
        self.port.setFlowControl(QSerialPort.NoFlowControl)
        self.open()

    def open(self):
        if not self.port.open(QSerialPort.ReadWrite):
            raise Exception(f"Failed to open port {self.port.portName()}: {self.port.errorString()}")

    def close(self):
        if self.port.isOpen():
            self.port.close()

    def senddata(self, data, size):
        if self.port.isOpen():
            message = QByteArray(data, size)
            self.port.flush()
            self.port.write(message)
            self.port.flush()
