# Regla Digital — uso rápido

Este paquete contiene la aplicación portable de la Regla Digital desarrollada para la exposición del Grupo 1 del 7.º B de la clase de Robótica Educativa del Colegio Santa Caterina Da Siena.

## Abrir la aplicación

1. Descomprimir completamente `ReglaDigitalPortable.zip`.
2. Conectar el Arduino UNO mediante un cable USB de datos.
3. Ejecutar `ReglaDigital.exe`.
4. Esperar unos segundos hasta que se abra el navegador.
5. Presionar el indicador **Conexión**, elegir el puerto COM y seleccionar **Conectar Arduino**.

No es necesario instalar Python en la computadora de exposición.

Si Windows muestra una advertencia, se debe a que el ejecutable educativo no posee una firma digital comercial. Utilizar únicamente el archivo obtenido desde el repositorio oficial del proyecto.

## Antes de usar el ejecutable

El Arduino debe tener cargado el programa incluido en:

```text
firmware/regla_digital.ino
```

El LCD debe utilizar la dirección I2C `0x27`. Las conexiones completas están en `docs/CONEXIONES.md`.

## Si no aparece el puerto COM

- Cerrar el Monitor Serie y el Arduino IDE.
- Confirmar que el cable USB transmite datos.
- Probar otro puerto USB.
- Revisar el Administrador de dispositivos de Windows.
- Instalar el driver CH340/CH341 si se utiliza una placa Arduino compatible con ese conversor.

## Si el navegador no se abre

Abrir manualmente:

```text
http://127.0.0.1:8766
```

La aplicación también dispone de un modo de simulación para presentar la interfaz sin el hardware conectado.
