import sys, inspect, re

class CPU:
    def __init__(self):
        self.ram = [0] * 256        #ram 00-FF
        self.reg = [0] * 8          #registers
        self.pc = 7                 #location of program counter/current instruction in registers
        self.reg[self.pc] = 0       #initialize program counter
        self.sp = 6                 #location of stack pointer in registers
        self.reg[self.sp] = 0xF4    #initialize stack pointer
        self.fl = 5                 #location of flag status in registers
        self.reg[self.fl] = 0       #initialize flag status
        self.halted = False         #interrupt status
        self.instruction = {        #cpu instruction set and their methods
            0b00000001:(self.HLT, 1),  0b10000010:(self.LDI, 3), 0b01000111:(self.PRN, 2),
            0b01000101:(self.PUSH, 2), 0b01000110:(self.POP, 2), 0b01010000:(self.CALL, 0),
            0b00010001:(self.RET, 0),  0b01010100:(self.JMP, 0),
            0b10100010:(lambda: self.alu('MUL'), 3), 0b10100000:(lambda: self.alu('ADD'), 3),
            0b10100001:(lambda: self.alu('SUB'), 3), 0b10100011:(lambda: self.alu('DIV'), 3),
            0b01100101:(lambda: self.alu('INC'), 2), 0b01100110:(lambda: self.alu('DEC'), 2),
            0b10100111:(lambda: self.alu('CMP'), 3), 0b01010101:(lambda: self.alu('JEQ'), 0),
            0b01010110:(lambda: self.alu('JNE'), 0),
            0b10101000:(lambda: self.alu('AND'), 3), 0b10101010:(lambda: self.alu('OR'), 3),
            0b10101011:(lambda: self.alu('XOR'), 3), 0b01101001:(lambda: self.alu('NOT'), 2),
            0b10101100:(lambda: self.alu('SHL'), 3), 0b10101101:(lambda: self.alu('SHR'), 3),
        }
    def load(self, program):
        with open(f'./programs/{program}.ls8', 'r') as punchcard:
            address = 0
            for line in punchcard:
                instruction = re.match(r'(\d+)(?=\D)', line) if re.match(r"(\d+)(?=\D)", line) else None
                if instruction:
                    self.ram_write(address, int(instruction[0], 2))
                    address += 1
    def ram_read(self, MAR): return self.ram[MAR]       #memory address register
    def ram_write(self, MAR, MDR): self.ram[MAR] = MDR  #memory data register
    def alu(self, op):
        #MATH
        def ADD(): self.reg[self.ram_read(self.reg[self.pc]+1)] += self.reg[self.ram_read(self.reg[self.pc]+2)]
        def SUB(): self.reg[self.ram_read(self.reg[self.pc]+1)] -= self.reg[self.ram_read(self.reg[self.pc]+2)]
        def MUL(): self.reg[self.ram_read(self.reg[self.pc]+1)] *= self.reg[self.ram_read(self.reg[self.pc]+2)]
        def DIV(): self.reg[self.ram_read(self.reg[self.pc]+1)] /= self.reg[self.ram_read(self.reg[self.pc]+2)]
        def INC(): self.reg[self.ram_read(self.reg[self.pc]+1)] += 1
        def DEC(): self.reg[self.ram_read(self.reg[self.pc]+1)] -= 1
        #LOGIC
        def CMP():
            if self.reg[self.ram_read(self.reg[self.pc]+1)] == self.reg[self.ram_read(self.reg[self.pc]+2)]: self.reg[self.fl] = 0b00000001
            elif self.reg[self.ram_read(self.reg[self.pc]+1)] < self.reg[self.ram_read(self.reg[self.pc]+2)]: self.reg[self.fl] = 0b00000100
            else: self.reg[self.fl] = 0b00000010
        def JEQ():
            if self.reg[self.fl] == 0b00000001: self.reg[self.pc] = self.reg[self.ram_read(self.reg[self.pc]+1)]
            else: self.reg[self.pc] += 2
        def JNE():
            if self.reg[self.fl] != 0b00000001: self.reg[self.pc] = self.reg[self.ram_read(self.reg[self.pc]+1)]
            else: self.reg[self.pc] += 2
        #BITWISE
        def AND(): self.reg[self.reg[self.pc]+1] = self.reg[self.reg[self.pc]+1] & self.reg[self.reg[self.pc]+2]
        def OR(): self.reg[self.reg[self.pc]+1] = self.reg[self.reg[self.pc]+1] | self.reg[self.reg[self.pc]+2]
        def XOR(): self.reg[self.reg[self.pc]+1] = self.reg[self.reg[self.pc]+1] ^ self.reg[self.reg[self.pc]+2]
        def NOT(): self.reg[self.reg[self.pc]+1] = ~self.reg[self.reg[self.pc]+1]
        def SHL(): self.reg[self.reg[self.pc]+1] = self.reg[self.reg[self.pc]+1] << self.reg[self.reg[self.pc]+2]
        def SHR(): self.reg[self.reg[self.pc]+1] = self.reg[self.reg[self.pc]+1] >> self.reg[self.reg[self.pc]+2]
        ops = {
            'ADD':ADD, 'SUB':SUB, 'MUL':MUL, 'DIV':DIV, 'INC':INC, 'DEC':DEC,
            'CMP':CMP, 'JEQ':JEQ, 'JNE':JNE, #'JGT':JGT, 'JLE':JLE, 'JLT':JLT,
            'AND':AND,   'OR':OR, 'XOR':XOR, 'NOT':NOT, 'SHL':SHL, 'SHR':SHR,
        }
        try: ops[op]()
        except: raise Exception('Unsupported ALU operation!')
    def LDI(self): self.reg[self.ram_read(self.reg[self.pc]+1)] = self.ram_read(self.reg[self.pc]+2)
    def PRN(self): print(self.reg[self.ram_read(self.reg[self.pc]+1)])
    def HLT(self): self.halted = True
    def JMP(self): self.reg[self.pc] = self.reg[self.ram_read(self.reg[self.pc]+1)]
    def PUSH(self, MDR=None):
        self.reg[self.sp] -= 1
        data = MDR if MDR else self.reg[self.ram[self.reg[self.pc]+1]]
        self.ram_write(self.reg[self.sp], data)
    def POP(self):
        self.reg[self.ram_read(self.reg[self.pc]+1)] = self.ram_read(self.reg[self.sp])
        self.reg[self.sp] += 1
    def CALL(self):
        self.PUSH(self.reg[self.pc]+2)
        self.reg[self.pc] = self.reg[self.ram_read(self.reg[self.pc]+1)]
    def RET(self):
        self.reg[self.pc] = self.ram_read(self.reg[self.sp])
        self.reg[self.sp] += 1
    def trace(self):
        print(f"TRACE: %02i | %03i %03i %03i |" % (
            self.reg[self.pc]+1,
            self.ram_read(self.reg[self.pc]),
            self.ram_read(self.reg[self.pc] + 1),
            self.ram_read(self.reg[self.pc] + 2)
        ), end='')
        for i in range(8): print(" %03i" % self.reg[i], end='')
        print()
    def run(self):
        while not self.halted:
            IR = self.ram_read(self.reg[self.pc])
            self.instruction[IR][0]()                       #execute instruction
            self.reg[self.pc] += self.instruction[IR][1]    #move program counter