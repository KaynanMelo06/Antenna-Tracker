class PID : 
    def __init__ (self, input, setpoint):
        self.input = input
        self.setpoint = setpoint
        self.p_term = 0
        self.i_term = 0
        self.d_term = 0
        self.error = self.last_error = 0

    def process (self, kp, ki, kd, outmin, outmax, input, setpoint):
        self.input = input
        self.setpoint = setpoint
        self.error = self.setpoint - self.input
        self.p_term = kp * self.error
        #self.i_term += ki * error
        self.i_term = 0
        self.d_term = kd * (self.error - self.last_error)

        self.last_error = self.error
        output = self.p_term + self.i_term + self.d_term
        if output > outmax:
            output = outmax
        elif output < outmin:
            output = outmin
        return output
        
