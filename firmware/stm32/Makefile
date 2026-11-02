# Firmware del Speed Follower (STM32G431CBT6). Requiere Arm GNU Toolchain (arm-none-eabi-gcc ≥ 12) y GNU make.
#   make            -> build/speed_follower.elf, .hex y .bin
#   make flash      -> graba con STM32CubeProgrammer (STLINK-V3MINIE por SWD)
#   make tamano     -> uso de flash y RAM
PREFIJO ?= arm-none-eabi-
CC  = $(PREFIJO)gcc
CXX = $(PREFIJO)g++
OBJCOPY = $(PREFIJO)objcopy
SIZE = $(PREFIJO)size
PROGRAMADOR ?= STM32_Programmer_CLI

BUILD = build
OBJETIVO = $(BUILD)/speed_follower
CPU = -mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard
DEFS = -DSTM32G431xx
INC = -Isrc -I../logica -I.. -Ivendor/cmsis_core -Ivendor/cmsis_device_g4
OPT = -O2 -g3
AVISOS = -Wall -Wextra -Werror -Wno-missing-field-initializers
CFLAGS = $(CPU) $(DEFS) $(INC) $(OPT) -ffunction-sections -fdata-sections -fsingle-precision-constant
CXXFLAGS = $(CFLAGS) $(AVISOS) -std=c++17 -fno-exceptions -fno-rtti -fno-threadsafe-statics -fno-use-cxa-atexit
LDFLAGS = $(CPU) -TSTM32G431CBTX_FLASH.ld -Wl,--gc-sections -Wl,-Map=$(OBJETIVO).map -Wl,--print-memory-usage \
          --specs=nano.specs --specs=nosys.specs -nostartfiles -Wl,--no-warn-rwx-segments
LIBS = -lm

CXX_SRC = src/main.cpp src/hw.cpp ../logica/sf_logica.cpp ../logica/estados.cpp ../logica/posicion.cpp
C_SRC = vendor/cmsis_device_g4/system_stm32g4xx.c
ASM_SRC = vendor/cmsis_device_g4/startup_stm32g431xx.s
OBJ = $(patsubst %,$(BUILD)/%.o,$(notdir $(CXX_SRC) $(C_SRC) $(ASM_SRC)))
vpath %.cpp src ../logica
vpath %.c vendor/cmsis_device_g4
vpath %.s vendor/cmsis_device_g4

all: $(OBJETIVO).elf $(OBJETIVO).hex $(OBJETIVO).bin tamano

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/%.cpp.o: %.cpp ../config_maestra.h src/pines_generados.h | $(BUILD)
	$(CXX) $(CXXFLAGS) -c $< -o $@

$(BUILD)/%.c.o: %.c | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/%.s.o: %.s | $(BUILD)
	$(CC) $(CPU) -c $< -o $@

$(OBJETIVO).elf: $(OBJ) STM32G431CBTX_FLASH.ld
	$(CXX) $(OBJ) $(LDFLAGS) $(LIBS) -o $@

$(OBJETIVO).hex: $(OBJETIVO).elf
	$(OBJCOPY) -O ihex $< $@

$(OBJETIVO).bin: $(OBJETIVO).elf
	$(OBJCOPY) -O binary $< $@

tamano: $(OBJETIVO).elf
	$(SIZE) $<

flash: $(OBJETIVO).hex
	$(PROGRAMADOR) -c port=SWD mode=UR -w $< -v -rst

clean:
	rm -rf $(BUILD)

.PHONY: all tamano flash clean
