import sys
import random
import pygame

class CPU:

	def __init__(self):
		self.pc = 0x200
		self.sp = 0
		self.stack = [0] * 16
		self.memory = [0] * 4096
		self.v = [0] * 16
		self.i = 0
		self.display_buffer = [0] * 32 * 64
		self.sound_timer = 0
		self.delay_timer = 0
		self.draw = True
		self.game = open(sys.argv[1],'rb').read()
		self.key_inputs = [0] * 16
		self.keyset = {
		pygame.K_1: 1, pygame.K_2: 2, pygame.K_3: 3, pygame.K_4: 12,
		pygame.K_q: 4, pygame.K_w: 5, pygame.K_e: 6, pygame.K_r: 13,
		pygame.K_a: 7, pygame.K_s: 8, pygame.K_d: 9, pygame.K_f: 14,
		pygame.K_z: 10, pygame.K_x: 0, pygame.K_b: 11, pygame.K_v: 15
		}

		self.fonts = [
						 0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
						 0x20, 0x60, 0x20, 0x20, 0x70,  # 1
						 0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
						 0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
						 0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
						 0xF0, 0x80, 0xF0, 0x10, 0xF8,  # 5
						 0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
						 0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
						 0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
						 0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
						 0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
						 0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
						 0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
						 0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
						 0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
						 0xF0, 0x80, 0xF0, 0x80, 0x80,  # F
					 ]


		self.opcode_lookup = {
								0x0000: {
											0x0000: self.sys_addr,       # 0nnn
											0x00E0: self.clear_screen,   # 00E0
											0x00EE: self.ret 			 # 00EE
										 },                         
								0x1000: self.jp_addr,                    # 1nnn
								0x2000: self.call_addr,                  # 2nnn
								0x3000: self.se_vx_byte,                 # 3nkk
								0x4000: self.sne_vx_byte,                # 4xkk
								0x5000: self.se_vx_vy,                   # 5xy0
								0x6000: self.ld_vx_byte,                 # 6xkk
								0x7000: self.add_vx_byte,                # 7xkk
								0x8000: {
											0x0000: self.ld_vx_vy,       # 8XY0
											0x0001: self.or_vx_vy,       # 8XY1
											0x0002: self.and_vx_vy,      # 8XY2
											0x0003: self.xor_vx_vy,      # 8xy3
											0x0004: self.add_vx_vy,      # 8xy4
											0x0005: self.sub_vx_vy,      # 8xy5
											0x0006: self.shr_vx_vy,      # 8xy6
											0x0007: self.subn_vx_vy,     # 8xy7
											0x000E: self.shl_vx_vy		 # 8xyE
										 },                         
								0x9000: self.sne_vx_vy,                  # 9xy0
								0xA000: self.ld_i_addr,                  # Annn
								0xB000: self.jp_v0_addr,                 # Bnnn
								0xC000: self.rnd_vx_byte,                # Cxkk
								0xD000: self.drw_vx_vy_n,                # Dvyn
								0xE000: {
											0x009E: self.skp_vx,         # Ex9E
											0x00A1: self.sknp_vx		 # ExA1
										},                          
								0xF000: {
											0x0007: self.ld_vx_dt,       # Fx07
											0x000A: self.ld_vx_k,        # Fx0A
											0x0015: self.ld_dt_vx,       # Fx15
											0x0018: self.ld_st_vx,       # Fx18
											0x001E: self.add_i_vx,       # Fx1E
											0x0029: self.ld_f_vx,        # Fx29
											0x0033: self.ld_b_vx,        # Fx33
											0x0055: self.ld_i_vx,        # Fx55
											0x0065: self.ld_vx_i		 # Fx65
										}                           	
								}
	####################
	#    GAME LOOP     #
	####################

	def main(self):
		self.load_fonts()   
		self.load_game()
		pygame.init()
		self.screen = pygame.display.set_mode((64 * 10, 32 * 10))
		clock = pygame.time.Clock()
		self.draw = False
		while True:
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					pygame.quit()
					sys.exit(0)
			if event.type == pygame.KEYDOWN:
				# Press L to Quit
				if event.key == pygame.K_l:
					pygame.quit()
					sys.exit(0)
				if event.key in self.keyset.keys():
					self.key_inputs[self.keyset[event.key]] = 1
			if event.type == pygame.KEYUP:
				if event.key in self.keyset.keys():
					self.key_inputs[self.keyset[event.key]] = 0

			self.execute_instruction()
			if self.draw:
				self.draw_to_screen()
			#clock.tick(120)


	########################
	#  EMULATOR FUNCTIONS  #
	########################

	def load_fonts(self):   
		for i in range(80):
				self.memory[i] = self.fonts[i]

	def load_game(self):
		for i in range(len(self.game)):
				self.memory[self.pc + i] = self.game[i]

	def execute_instruction(self):
		self.draw = False
		self.opcode = (self.memory[self.pc] << 8) | self.memory[self.pc + 1]
		self.x = (self.opcode & 0x0f00) >> 8
		self.y = (self.opcode & 0x00f0) >> 4
		function = self.opcode & 0xF000
		if (function) in self.opcode_lookup:
			if callable(self.opcode_lookup[function]):
					self.opcode_lookup[self.opcode & 0xF000]()
			else:
				if self.opcode & 0x00FF in self.opcode_lookup[function]:
					self.opcode_lookup[function][self.opcode & 0x00FF]()
				elif self.opcode & 0x000F in self.opcode_lookup[function]:
					self.opcode_lookup[function][self.opcode & 0x000F]()
		else:
			print('Something wrong here')
			sys.exit(0)
		if self.delay_timer > 0:
			self.delay_timer -= 1
		if self.sound_timer > 0:
			self.sound_timer -= 1

	def draw_to_screen(self):
		black = (0, 0, 0)
		white = (255, 255, 255)
		self.screen.fill(black)
		for i in range(len(self.display_buffer)):
				if self.display_buffer[i] == 1:
					pygame.draw.rect(self.screen, white, ((i % 64) * 10, (i / 64) * 10, 10,10))
				else:
					pygame.draw.rect(self.screen, black, ((i % 64) * 10, (i / 64) * 10, 10,10))
		pygame.display.update()


	####################
	# OPCODE FUNCTIONS #
	####################

	def sys_addr(self):                                              # 0nnn
   		self.pc = (self.opcode & 0x0FFF) - 2

	def clear_screen(self):                                         # 00E0
		self.display_buffer = [0] * 64 * 32
		self.draw = True
		self.pc += 2
		print('CLEAR SCREEN')

	def ret(self):                                                  # 0x00EE
		self.pc = self.stack[self.sp] + 2
		self.sp -= 1
		print('RET')

	def jp_addr(self):                                              # 1nnn
			self.pc = self.opcode & 0x0FFF
			print(f'JP 0x{self.opcode & 0x0FFF:04x}')

	def call_addr(self):                                            # 2nnn
			self.stack[self.sp] = self.pc
			self.sp += 1
			self.stack[self.sp] = self.pc
			self.pc = self.opcode & 0x0FFF
			print(f'CALL 0x{self.pc:04x}')

	def se_vx_byte(self):                                           # 3xkk
			if self.v[self.x] == self.opcode & 0x00FF:
				self.pc += 4
			else:
				self.pc += 2
			print(f'SE V{self.x:n} 0x{self.opcode & 0x00FF:02x}')

	def sne_vx_byte(self):                                          # 4xkk
			if self.v[self.x] != self.opcode & 0x00FF:
				self.pc += 4
			else:
				self.pc += 2
			print(f'SNE V{self.x:n} 0x{self.opcode & 0x00FF:02x}')

	def se_vx_vy(self):                                             # 5xy0
			if self.v[self.x] == self.v[self.y]:
				self.pc += 4
			else:
				self.pc += 2
			print(f'SE V{self.x:n} 0x{self.v[self.y]:04x}')

	def ld_vx_byte(self):                                           # 6xkk
			self.v[self.x] = self.opcode & 0x00FF
			self.pc += 2
			print(f'LD V{self.x:n} 0x{self.opcode & 0x00FF:02x}')

	def add_vx_byte(self):                                          # 7xkk
			self.v[self.x] += self.opcode & 0x00FF
			self.v[self.x] &= 0xff
			self.pc += 2
			print(f'LD V{self.x:n} 0x{self.opcode & 0x00FF:02x}')

	def ld_vx_vy(self):                                             # 8xy0
			self.v[self.x] = self.v[self.y]
			self.v[self.x] &= 0xFF
			self.pc += 2
			print(f'LD V{self.x:n} V{self.y:n}')

	def or_vx_vy(self):                                             # 8xy1
			self.v[self.x] = self.v[self.x] | self.v[self.y]
			self.v[self.x] &= 0xFF
			self.pc += 2
			print(f'OR V{self.x:n} V{self.y:n}')

	def and_vx_vy(self):                                            # 8xy2
			self.v[self.x] = self.v[self.x] & self.v[self.y]
			self.v[self.x] &= 0xFF
			self.pc += 2
			print(f'AND V{self.x:n} V{self.y:n}')

	def xor_vx_vy(self):                                            # 8xy3
			self.v[self.x] = self.v[self.x] ^ self.v[self.y]
			self.v[self.x] &= 0xFF
			self.pc += 2
			print(f'XOR V{self.x:n} V{self.y:n}')

	def add_vx_vy(self):                                            # 8xy4
			self.v[0xF] = int((self.v[self.x] + self.v[self.y]) > 0x00FF)
			self.v[self.x] += self.v[self.y]
			self.v[self.x] &= 0xFF
			self.pc += 2
			print(f'ADD V{self.x:n} V{self.y:n}')

	def sub_vx_vy(self):                                            # 8xy5
			self.v[0xF] = int(self.v[self.x] > self.v[self.y])
			self.v[self.x] -= self.v[self.y]
			self.v[self.x] &= 0xFF
			self.pc += 2
			print(f'SUB V{self.x:n} V{self.y:n}')

	def shr_vx_vy(self):                                            # 8xy6
			self.v[0xF] = self.v[self.x] & 0x1
			self.v[self.x] >>= 1
			self.v[self.x] &= 0xFF
			self.pc += 2
			print(f'SHR V{self.x:n} V{self.y:n}')

	def subn_vx_vy(self):                                           # 8xy7
			self.v[0xF] = int(self.v[self.x] > self.v[self.y])
			self.v[self.x] = self.v[self.y] - self.v[self.x]
			self.registers[self.vx] &= 0xFF
			self.pc += 2
			print(f'SUBN V{self.x:n} V{self.y:n}')

	def shl_vx_vy(self):                                            # 8xyE
			self.v[0xF] = self.v[self.x] >> 7
			self.v[self.x] <<= 1
			self.pc += 2
			print(f'SHL V{self.x:n} V{self.y:n}')

	def sne_vx_vy(self):                                            # 9xy0
			if self.v[self.x] != self.v[self.y]:
				self.pc += 4
			else:	
				self.pc += 2
			print(f'SNE V{self.x:n} V{self.y:n}')

	def ld_i_addr(self):                                            # Annn
			self.i = self.opcode & 0x0FFF
			self.pc += 2
			print(f'LD I 0x{self.opcode & 0x0FFF:04x}')

	def jp_v0_addr(self):                                           # Bnnn
			self.pc = (self.opcode & 0x0FFF) + self.v[0x0]
			print(f'JP V0 0x{self.opcode & 0x0FFF:04x}')

	def rnd_vx_byte(self):                                          # Cxkk
			self.v[self.x] = random.randint(0, 0xFF) & (self.opcode & 0x00FF)
			self.pc += 2
			print(f'RND V{self.x:n} 0x{self.opcode & 0x00FF:02x}')

	def drw_vx_vy_n(self):                                          # Dxyn
		self.v[0xF] = 0
		for h in range(self.opcode & 0x000F):
			pixel = self.memory[self.i + h]
			for w in range(8):
				if (pixel & (0x80 >> w)) != 0:
					loc = (self.v[self.x] + w + (h + self.v[self.y]) * 64) % 2048
					if self.display_buffer[loc] == 1:
						self.v[0xF] = 1
					self.display_buffer[loc] ^= 1
		self.draw = True
		self.pc += 2

		print(f'DRW V{self.x:n} V{self.y:n} 0x{self.opcode & 0xF:02x}')

	def skp_vx(self):                                               # EX9E
		if self.key_inputs[self.v[self.x]]:
			self.pc += 4
		else:
			self.pc += 2
		print(f'SKP V{self.x:n}')

	def sknp_vx(self):                                              # EXA1
		if not self.key_inputs[self.v[self.x]]:
			self.pc += 4
		else:
			self.pc += 2
		print(f'SKNP V{self.x:n}')
					
	def ld_vx_dt(self):                                             # Fx07
		self.v[self.x] = self.delay_timer
		self.pc += 2
		print(f'LD V{self.x:n} DT')

	def ld_vx_k(self):                                              # Fx0A
		while True:
			event = pygame.event.wait()
			if event.type == pygame.KEYDOWN:
				if event.key in self.keyset.keys():
					self.v[self.x] = self.keyset[event.key]
					break
		self.pc += 2
		print(f'LD V{self.x:n} KEY')

	def ld_dt_vx(self):                                             # Fx15
		self.delay_timer = self.v[self.x]
		self.pc += 2
		print(f'LD DT V{self.x:n}')

	def ld_st_vx(self):                                             # Fx18
		self.sound_timer = self.v[self.x]
		self.pc += 2
		print(f'LD ST V{self.x:n}')

	def add_i_vx(self):                                             # Fx1E
		self.i += self.v[self.x]
		self.pc += 2
		print(f'ADD I V{self.x:n}')

	def ld_f_vx(self):                                              # Fx29
		self.i = (self.v[self.x] * 5) & 0x0FFF
		self.pc += 2
		print(f'LD I V{self.x:n}')

	def ld_b_vx(self):                                              # Fx33
		self.memory[self.i] = self.v[self.x] // 100
		self.memory[self.i + 1] = (self.v[self.x] % 100) // 10
		self.memory[self.i + 2] = self.v[self.x] % 10
		self.pc += 2
		print(f'LD {self.v[self.x]:n} V{self.x:n}')

	def ld_i_vx(self):                                              # Fx55
			for count in range(self.x + 1):
				self.memory[self.i + count] = self.v[count]
			self.pc += 2
			print(f'LD I V{self.x:n}')

	def ld_vx_i(self):                                              # Fx65
			for count in range(self.x):
				self.v[count] = self.memory[self.i + count]
			self.pc += 2
			print(f'LD V{self.x:n} I')


if __name__ == "__main__":
	CPU().main()
