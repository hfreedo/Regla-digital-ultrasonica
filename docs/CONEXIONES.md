# Conexiones del prototipo

| Componente | Arduino UNO |
|---|---|
| HC-SR04 TRIG | D9 |
| HC-SR04 ECHO | D10 |
| LCD I2C SDA | A4 |
| LCD I2C SCL | A5 |
| HC-SR04 VCC | 5V |
| LCD I2C VCC | 5V |
| Tierras GND | GND común |

## Consideraciones

- El firmware utiliza `9600` baudios.
- La dirección inicial del LCD es `0x27`; algunos módulos utilizan `0x3F`.
- Cerrar el Monitor Serie antes de conectar la aplicación, porque un puerto COM solamente puede ser utilizado por un programa a la vez.
- Para la exposición se recomienda trabajar entre 3 y 100 cm con objetos planos y colocados frente al sensor.
- La medición se toma desde la cara frontal del HC-SR04 hasta el objeto.
