import time

class PID : 
    def __init__ (self, input, setpoint):
        self.input = input
        self.setpoint = setpoint
        self.p_term = 0.000
        self.i_term = 0.000
        self.d_term = 0.000
        self.error = self.last_error = 0
        self.last_time   = time.time()   # armazena o instante da última chamada

    def process (self, kp, ki, kd, outmin, outmax, input, setpoint):
        # calcula dt
        now = time.time()
        dt  = now - self.last_time
        self.last_time = now
        
        self.input = input
        self.setpoint = setpoint
        self.error = self.setpoint - self.input
        
        self.p_term = kp * self.error
        self.i_term += ki * self.error
        self.i_term = 0.000
        # termo derivativo considerando dt
        if dt > 0:
            self.d_term = kd * (self.error - self.last_error) / dt
        else:
            self.d_term = 0.0

        self.last_error = self.error
        
        # Dead-band: não mexer se estiver “perto” do alvo
        deadband = 2.0     # graus
        if abs(self.error) < deadband:
            output = 0.0
        else:
            # cálculo normal
            output = self.p_term + self.i_term + self.d_term
        
        # saturacao
        if output > outmax:
            output = outmax
        elif output < outmin:
            output = outmin
        return output
        
